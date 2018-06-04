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
        return dict(
            client_id=self.oidc_config.client_id,
            client_secret=self.oidc_config.client_secret
        )

    def provider_info(self):
        return dict(
            issuer="https://{DOMAIN}/".format(DOMAIN=self.oidc_config.OIDC_DOMAIN),
            authorization_endpoint=self.oidc_config.auth_endpoint(),
            token_endpoint=self.oidc_config.token_endpoint(),
            userinfo_endpoint=self.oidc_config.userinfo_endpoint()

        )

    def auth(self, app):
        o = OIDCAuthentication(
            app,
            provider_configuration_info=self.provider_info(),
            client_registration_info=self.client_info()
        )

        return o


class nullOpenIDConnect(OpenIDConnect):
    """Null object for ensuring test cov if new up fails."""

    def __init__(self, configuration):
        """None based versions of OIDC Object."""
        self.oidc_config = None

    def client_info(self):
        return dict(
            client_id=None,
            client_secret=None
        )

    def provider_info(self):
        return dict(
            issuer=None,
            authorization_endpoint=None,
            token_endpoint=None,
            userinfo_endpoint=None,
        )


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
        return self.jws_data.get('code', None)

    @property
    def preferred_connection_name(self):
        return self.jws_data.get('preferred_connection_name', 'Unknown')

    @property
    def redirect_uri(self):
        return self.jws_data.get('redirect_uri', 'https://sso.mozilla.com')

    def _get_connection_name(self, connection):
        CONNECTION_NAMES = {
            'google-oauth2': 'Google',
            'github': 'GitHub',
            'firefoxaccounts': 'Firefox Accounts',
            'Mozilla-LDAP-Dev': 'LDAP',
            'Mozilla-LDAP': 'LDAP',
            'email': 'passwordless email'
        }
        return (
            CONNECTION_NAMES[connection]
            if connection in CONNECTION_NAMES else connection
        )

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
                logger.warning('The public key signature was not valid for jws {jws}'.format(jws=self.jws))
                self.jws_data = json.loads(self.jws.payload)
                self.jws_data['code'] = 'invalid'
                return False
            else:
                self.jws_data = json.loads(self.jws_obj.payload.decode())
                logger.info('Loaded JWS data.')
                self.jws_data['connection_name'] = self._get_connection_name(self.jws_data['connection'])
                return True
        except UnicodeDecodeError:
            return False

    def error_message(self):
        error_code = self.error_code
        if error_code == 'githubrequiremfa':
            error_text = \
                "You must setup a security device(\"MFA\", \"2FA\") for your GitHub account in order to access \
                this service. Please follow the \
                <a href=\"https://help.github.com/articles/securing-your-account-with-two-factor-authentication-2fa/\">\
                GitHub documentation\
                </a> to setup your device, then try logging in again."
        elif error_code == 'fxarequiremfa':
            error_text = \
                "You must setup a security device(\"MFA"", \"2FA\") for your Firefox Account in order to access \
                this service. Please setup a <a href=\"https://accounts.firefox.com\">security device</a>, then \
                try logging in again."
        elif error_code == 'notingroup':
            error_text = "Sorry, you do not have permission to access {client}.  \
            Please contact eus@mozilla.com if you should have access.".format(client=self.data.get('client'))
        elif error_code == 'accesshasexpired':
            error_text = "Sorry, your access to {client} has expired because you have not been actively using it. \
            Please request access again.".format(client=self.data.get('client'))
        elif error_code == 'primarynotverified':
            "You primary email address is not yet verified. Please verify your \
            email address with {connection_name} in order to use this service.".format(
                connection_name=self._get_connection_name(self.jws_data.get('connection', ''))
            )
        elif error_code == 'incorrectaccount':
            error_text = "Sorry, you may not login using {connection_name}.  \
             We require login to be performed using the most secure method available for your account, which is \
             {preferred_connection_name}.".format(
                connection_name=self._get_connection_name(self.jws_data.get('connection', '')),
                preferred_connection_name=self._get_connection_name(self.preferred_connection_name)
            )
        elif error_code == 'accountnotprimary':
            error_text = "You already have an account with a different login method for this identifier. Please \
              set {connection_name} as your primary login method on <a href=\"https://www.mozillians.org\">\
              mozillians.org</a> or use your original login method for this account.".format(
                connection_name=self._get_connection_name(self.jws_data.get('connection', ''))
              )
        else:
            error_text = "Oye, something went wrong."
        return error_text
