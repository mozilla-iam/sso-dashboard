import json
import logging
from josepy.jwk import JWK
from josepy.jws import JWS

"""Class that governs all authentication with open id connect."""
from flask_pyoidc.flask_pyoidc import OIDCAuthentication

logger = logging.getLogger(__name__)


class OpenIDConnect(object):
    """Auth object for login, logout, and response validation."""

    def __init__(self, configuration):
        """Object initializer for auth object."""
        self.oidc_config = configuration

    def client_info(self):
        client_info = {"client_id": self.oidc_config.client_id, "client_secret": self.oidc_config.client_secret}
        return client_info

    def get_oidc(self, app):
        extra_request_args = {"scope": ["openid", "profile"]}
        o = OIDCAuthentication(
            app,
            issuer="https://{DOMAIN}".format(DOMAIN=self.oidc_config.OIDC_DOMAIN),
            client_registration_info=self.client_info(),
            extra_request_args=extra_request_args,
        )
        return o


class tokenVerification(object):
    def __init__(self, jws, public_key):
        self.jws = jws
        self.jws_data = {}
        self.public_key = public_key

    @property
    def verify(self):
        return self._verified()

    @property
    def data(self):
        return self.jws_data

    @property
    def error_code(self):
        return self.jws_data.get("code", None)

    @property
    def preferred_connection_name(self):
        return self.jws_data.get("preferred_connection_name", "Unknown")

    @property
    def redirect_uri(self):
        return self.jws_data.get("redirect_uri", "https://sso.mozilla.com")

    def _get_connection_name(self, connection):
        CONNECTION_NAMES = {
            "google-oauth2": "Google",
            "github": "GitHub",
            "firefoxaccounts": "Firefox Accounts",
            "Mozilla-LDAP-Dev": "LDAP",
            "Mozilla-LDAP": "LDAP",
            "email": "passwordless email",
        }
        return CONNECTION_NAMES[connection] if connection in CONNECTION_NAMES else connection

    def _signed(self, jwk):
        if self.jws_obj.verify(jwk):
            return True
        else:
            return False

    def _verified(self):
        try:
            jwk = JWK.load(self.public_key)
            self.jws_obj = JWS.from_compact(self.jws)
            if self._signed(jwk) is False:
                logger.warning("The public key signature was not valid for jws {jws}".format(jws=self.jws))
                self.jws_data = json.loads(self.jws.payload)
                self.jws_data["code"] = "invalid"
                return False
            else:
                self.jws_data = json.loads(self.jws_obj.payload.decode())
                logger.info("Loaded JWS data.")
                self.jws_data["connection_name"] = self._get_connection_name(self.jws_data["connection"])
                return True
        except UnicodeDecodeError:
            return False

    def error_message(self):
        error_code = self.error_code
        if error_code == "githubrequiremfa":
            error_text = 'You must setup a security device ("MFA", "2FA") for your GitHub account in order to access \
                this service. Please follow the \
                <a href="https://help.github.com/articles/securing-your-account-with-two-factor-authentication-2fa/">\
                GitHub documentation\
                </a> to setup your device, then try logging in again.'
        elif error_code == "fxarequiremfa":
            error_text = 'Please <a href="https://support.mozilla.org/kb/secure-firefox-account-two-step-authentication">\
                secure your Firefox Account with two-step authentication</a>, \
                then try logging in again.\n<br/><br/>\n\
                If you have just setup your security device and you see this message, please log out of \
                 <a href="https://accounts.firefox.com">Firefox Accounts</a> (click the "Sign out" button), then \
                 log back in.'
        elif error_code == "notingroup":
            error_text = "Sorry, you do not have permission to access {client}.  \
            Please contact eus@mozilla.com if you should have access.".format(
                client=self.data.get("client")
            )
        elif error_code == "accesshasexpired":
            error_text = "Sorry, your access to {client} has expired because you have not been actively using it. \
            Please request access again.".format(
                client=self.data.get("client")
            )
        elif error_code == "primarynotverified":
            "You primary email address is not yet verified. Please verify your \
            email address with {connection_name} in order to use this service.".format(
                connection_name=self._get_connection_name(self.jws_data.get("connection", ""))
            )
        elif error_code == "incorrectaccount":
            error_text = "Sorry, you may not login using {connection_name}.  \
             Instead, please use \
             {preferred_connection_name}.".format(
                connection_name=self._get_connection_name(self.jws_data.get("connection", "")),
                preferred_connection_name=self._get_connection_name(self.preferred_connection_name),
            )
        elif error_code == "aai_failed":
            error_text = "{client} requires you to setup additional security measures for your account, \
            such as enabling multi-factor authentication (MFA) or using a safer authentication method (such as a \
            Firefox Account login). You will not be able to login until this is \
            done.".format(
                client=self.data.get("client")
            )
        elif error_code == "staffmustuseldap":
            error_text = "Staff LDAP account holders are required to use their LDAP account to login. Please go back \
            and type your LDAP email address to login with your Staff account, instead of using \
            {connection_name}.".format(
                connection_name=self._get_connection_name(self.jws_data.get("connection", ""))
            )
        else:
            error_text = "Oye, something went wrong."
        return error_text
