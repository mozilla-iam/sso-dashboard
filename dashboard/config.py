"""Configuration loader for different environments."""

import base64
import datetime
from dashboard import get_config

CONFIG = get_config()


class Config(object):
    def __init__(self, app):
        self.app = app

        self.environment = CONFIG("environment", default="local")
        self.settings = self._init_env()

    def _init_env(self):
        return DefaultConfig()


class DefaultConfig(object):
    """Defaults for the configuration objects."""

    DEBUG = bool(CONFIG("debug", namespace="sso-dashboard", parser=bool, default="False"))
    TESTING = bool(CONFIG("testing", namespace="sso-dashboard", parser=bool, default="False"))

    CSRF_ENABLED = bool(CONFIG("csrf_enabled", parser=bool, default="True"))
    PERMANENT_SESSION = bool(CONFIG("permanent_session", namespace="sso-dashboard", parser=bool, default="True"))
    seconds = int(CONFIG("permanent_session_lifetime", namespace="sso-dashboard", default="86400"))
    PERMANENT_SESSION_LIFETIME = datetime.timedelta(seconds=seconds)

    SESSION_COOKIE_SAMESITE = CONFIG("session_cookie_samesite", namespace="sso-dashboard", default="lax")
    SESSION_COOKIE_HTTPONLY = bool(
        CONFIG("session_cookie_httponly", namespace="sso-dashboard", parser=bool, default="True")
    )

    SECRET_KEY = CONFIG("secret_key", namespace="sso-dashboard")
    SERVER_NAME = CONFIG("server_name", namespace="sso-dashboard", default="localhost:8000")
    SESSION_COOKIE_NAME = SERVER_NAME + "_session"

    S3_BUCKET = CONFIG("s3_bucket", namespace="sso-dashboard")

    CDN = CONFIG(
        "cdn",
        namespace="sso-dashboard",
        default="https://cdn.{SERVER_NAME}".format(SERVER_NAME=SERVER_NAME),
    )

    FORBIDDEN_PAGE_PUBLIC_KEY = base64.b64decode(CONFIG("forbidden_page_public_key", namespace="sso-dashboard"))

    PREFERRED_URL_SCHEME = CONFIG("preferred_url_scheme", namespace="sso-dashboard", default="https")

    REDIS_CONNECTOR = CONFIG("redis_connector", namespace="sso-dashboard")


class OIDCConfig(object):
    """Convienience Object for returning required vars to flask."""

    def __init__(self):
        """General object initializer."""
        CONFIG = get_config()
        self.OIDC_DOMAIN = CONFIG("oidc_domain", namespace="sso-dashboard")
        self.OIDC_CLIENT_ID = CONFIG("oidc_client_id", namespace="sso-dashboard")
        self.OIDC_CLIENT_SECRET = CONFIG("oidc_client_secret", namespace="sso-dashboard")
        self.LOGIN_URL = "https://{DOMAIN}/login?client={CLIENT_ID}".format(
            DOMAIN=self.OIDC_DOMAIN, CLIENT_ID=self.OIDC_CLIENT_ID
        )

    @property
    def client_id(self):
        return self.OIDC_CLIENT_ID

    @property
    def client_secret(self):
        return self.OIDC_CLIENT_SECRET

    def auth_endpoint(self):
        return "https://{DOMAIN}/authorize".format(DOMAIN=self.OIDC_DOMAIN)

    def token_endpoint(self):
        return "https://{DOMAIN}/oauth/token".format(DOMAIN=self.OIDC_DOMAIN)

    def userinfo_endpoint(self):
        return "https://{DOMAIN}/userinfo".format(DOMAIN=self.OIDC_DOMAIN)
