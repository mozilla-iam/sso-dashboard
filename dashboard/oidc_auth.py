import json
from typing import Optional
import josepy.errors
from josepy.jwk import JWK
from josepy.jws import JWS

# Class that governs all authentication with OpenID Connect.
from flask_pyoidc import OIDCAuthentication  # type: ignore
from flask_pyoidc.provider_configuration import ClientMetadata  # type: ignore
from flask_pyoidc.provider_configuration import ProviderConfiguration  # type: ignore

KNOWN_ERROR_CODES = {
    "githubrequiremfa",
    "fxarequiremfa",
    "notingroup",
    "accesshasexpired",
    "primarynotverified",
    "incorrectaccount",
    "aai_failed",
    "staffmustuseldap",
    "maintenancemode",
}


class OpenIDConnect:
    """Auth object for login, logout, and response validation."""

    def __init__(self, configuration):
        """Object initializer for auth object."""
        self.oidc_config = configuration

    def client_info(self):
        client_info = ClientMetadata(client_id=self.oidc_config.client_id, client_secret=self.oidc_config.client_secret)
        return client_info

    def provider_info(self):
        auth_request_params = {"scope": ["openid", "profile", "email"]}
        provider_config = ProviderConfiguration(
            issuer=f"https://{self.oidc_config.OIDC_DOMAIN}",
            client_metadata=self.client_info(),
            auth_request_params=auth_request_params,
        )
        return provider_config

    def get_oidc(self, app):
        provider_info = self.provider_info()
        o = OIDCAuthentication({"default": provider_info}, app)
        return o


def friendly_connection_name(connection):
    CONNECTION_NAMES = {
        "google-oauth2": "Google",
        "github": "GitHub",
        "firefoxaccounts": "Mozilla Accounts",
        "Mozilla-LDAP-Dev": "LDAP",
        "Mozilla-LDAP": "LDAP",
        "email": "passwordless email",
    }
    return CONNECTION_NAMES.get(connection, connection)


class TokenError(BaseException):
    pass


class TokenVerification:
    def __init__(self, jws, public_key):
        try:
            self.jws = JWS.from_compact(jws)
        except josepy.errors.DeserializationError as exc:
            raise TokenError("Could not deserialize JWS") from exc
        except UnicodeDecodeError as exc:
            raise TokenError("Invalid encoding of JWS parts") from exc
        try:
            self.public_key = JWK.load(public_key)
        except josepy.errors.Error as exc:
            raise TokenError("Could not load public key") from exc
        if self.signed():
            try:
                self.jws_data = json.loads(self.jws.payload)
            except json.decoder.JSONDecodeError as exc:
                raise TokenError("Invalid JSON in payload") from exc
        else:
            self.jws_data = {
                "code": "invalid",
            }

    @property
    def client(self) -> Optional[str]:
        return self.jws_data.get("client")

    @property
    def error_code(self) -> Optional[str]:
        return self.jws_data.get("code")

    @property
    def connection(self) -> Optional[str]:
        return self.jws_data.get("connection")

    @property
    def preferred_connection_name(self) -> Optional[str]:
        return self.jws_data.get("preferred_connection_name")

    def signed(self) -> bool:
        """
        By the time we get here we've got a valid key, and a properly
        (probably) formatted JWS.

        The only thing left to do is to verify the signature on the JWS.
        """
        try:
            return self.jws.verify(self.public_key)
        except josepy.errors.Error:
            return False

    def error_message(self) -> Optional[str]:
        """
        If this isn't an error code we recognize then we _should_ log at a
        higher layer (one with more context).
        """
        if self.client:
            client_name = self.client
        else:
            client_name = "this application"
        if self.connection:
            connection_name = friendly_connection_name(self.connection)
        else:
            connection_name = "Unknown"
        if self.preferred_connection_name:
            preferred_connection_name = friendly_connection_name(self.preferred_connection_name)
        else:
            preferred_connection_name = "Unknown"
        if self.error_code == "githubrequiremfa":
            return """
                You must setup a security device ("MFA", "2FA") for your GitHub
                account in order to access this service. Please follow the
                <a href="https://help.github.com/articles/securing-your-account-with-two-factor-authentication-2fa/">GitHub documentation</a>
                to setup your device, then try logging in again.
            """
        if self.error_code == "fxarequiremfa":
            return """
                Please
                <a href="https://support.mozilla.org/kb/secure-firefox-account-two-step-authentication">secure your Mozilla Account with two-step authentication</a>,
                then try logging in again.<br><br>
                If you have just setup your security device and you see this
                message, please log out of
                <a href="https://accounts.firefox.com">Mozilla Accounts</a>
                (click the "Sign out" button), then log back in.
            """
        if self.error_code == "notingroup":
            return f"""
                Sorry, you do not have permission to access
                {client_name}. Please contact the application
                owner for access. If unsure who that may be, please contact
                ServiceDesk@mozilla.com for support.
            """
        if self.error_code == "accesshasexpired":
            return f"""
                Sorry, your access to {client_name} has expired
                because you have not been actively using it. Please request
                access again.
            """
        if self.error_code == "primarynotverified":
            return f"""
                You primary email address is not yet verified. Please verify your
                email address with
                {connection_name}
                in order to use this service.
            """
        if self.error_code == "incorrectaccount":
            return f"""
                Sorry, you may not login using {connection_name}.  Instead,
                please use {preferred_connection_name}.
            """
        if self.error_code == "aai_failed":
            return f"""
                {client_name.title()} requires you to setup additional
                security measures for your account, such as enabling
                multi-factor authentication (MFA) or using a safer
                authentication method (such as a Mozilla Account login).  You
                will not be able to login until this is done.
            """
        if self.error_code == "staffmustuseldap":
            return """
                It appears that you are attempting to log in with a Mozilla
                email address, which requires LDAP authentication.
                Please log out and sign back in using your LDAP credentials.
                To do this, click the Logout button below and then log in again
                by entering your emal address and clicking Enter.
                Avoid using the buttons Sign in with Mozilla, with GitHub, or
                with Google.
            """
        if self.error_code == "maintenancemode":
            return """
                The system is in maintenance mode. Please try again later.
            """
        return None
