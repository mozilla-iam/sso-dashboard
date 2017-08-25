"""Configuration loader for different environments."""
from dashboard.utils import get_secret


class Config(object):
    """Defaults for the configuration objects."""
    DEBUG = True
    TESTING = False
    CSRF_ENABLED = True
    PERMANENT_SESSION = True
    PERMANENT_SESSION_LIFETIME = 86400

    SESSION_COOKIE_HTTPONLY = True
    LOGGER_NAME = "sso-dashboard"

    SECRET_KEY = get_secret('sso-dashboard.secret_key', {'app': 'sso-dashboard'})
    SERVER_NAME = get_secret('sso-dashboard.server_name', {'app': 'sso-dashboard'})

    MOZILLIANS_API_URL = 'https://mozillians.org/api/v2/users/'
    MOZILLIANS_API_KEY = get_secret('sso-dashboard.mozillians_api_key', {'app': 'sso-dashboard'})

    CDN = 'https://cdn.{SERVER_NAME}'.format(SERVER_NAME=SERVER_NAME)


class ProductionConfig(Config):
    PREFERRED_URL_SCHEME = 'https'
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    PREFERRED_URL_SCHEME = 'http'
    DEVELOPMENT = True
    DEBUG = True
    SECRET_KEY = 'abab123123'
    SERVER_NAME = 'localhost:5000'
    CDN = 'https://cdn.sso.allizom.org'


class TestingConfig(Config):
    TESTING = True


class OIDCConfig(object):
    """Convienience Object for returning required vars to flask."""
    def __init__(self):
        """General object initializer."""
        self.OIDC_DOMAIN = get_secret('sso-dashboard.oidc_domain', {'app': 'sso-dashboard'})
        self.OIDC_CLIENT_ID = get_secret('sso-dashboard.oidc_client_id', {'app': 'sso-dashboard'})
        self.OIDC_CLIENT_SECRET = get_secret(
            'sso-dashboard.oidc_client_secret', {'app': 'sso-dashboard'}
        )
        self.LOGIN_URL = "https://{DOMAIN}/login?client={CLIENT_ID}".format(
            DOMAIN=self.OIDC_DOMAIN,
            CLIENT_ID=self.OIDC_CLIENT_ID
        )

    @property
    def client_id(self):
        return self.OIDC_CLIENT_ID

    @property
    def client_secret(self):
        return self.OIDC_CLIENT_SECRET

    def auth_endpoint(self):
        return "https://{DOMAIN}/authorize".format(
            DOMAIN=self.OIDC_DOMAIN
        )

    def token_endpoint(self):
        return "https://{DOMAIN}/oauth/token".format(
            DOMAIN=self.OIDC_DOMAIN
        )

    def userinfo_endpoint(self):
        return "https://{DOMAIN}/userinfo".format(
            DOMAIN=self.OIDC_DOMAIN
        )
