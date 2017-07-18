#!/usr/bin/python
"""Configuration loader for different environments."""

import os
from utils import get_secret


class Config(object):
    """Defaults for the configuration objects."""
    DEBUG = True
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = get_secret('sso-dashboard.secret_key', {'app': 'sso-dashboard'})
    SERVER_NAME = get_secret('sso-dashboard.server_name', {'app': 'sso-dashboard'})
    PERMANENT_SESSION = get_secret('sso-dashboard.secret_key', {'app': 'sso-dashboard'})
    PERMANENT_SESSION_LIFETIME = 86400
    MOZILLIANS_API_URL = 'https://mozillians.org/api/v2/users/'
    MOZILLIANS_API_KEY = get_secret('sso-dashboard.mozillians_api_key', {'app': 'sso-dashboard'})
    SESSION_COOKIE_HTTPONLY = True
    LOGGER_NAME = "sso-dashboard"


class ProductionConfig(Config):
    PREFERRED_URL_SCHEME = 'https'
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    PREFERRED_URL_SCHEME = 'https'
    DEVELOPMENT = True
    DEBUG = True
    SERVER_NAME = 'localhost:5000'


class TestingConfig(Config):
    TESTING = True


class OIDCConfig(object):
    """Convienience Object for returning required vars to flask."""
    def __init__(self):
        """General object initializer."""
        self.OIDC_DOMAIN = get_secret('sso-dashboard.oidc_domain', {'app': 'sso-dashboard'})
        self.OIDC_CLIENT_ID = get_secret('sso-dashboard.oidc_client_id', {'app': 'sso-dashboard'})
        self.OIDC_CLIENT_SECRET = get_secret('sso-dashboard.oidc_client_secret', {'app': 'sso-dashboard'})
        self.LOGIN_URL = "https://{DOMAIN}/login?client={CLIENT_ID}".format(
            DOMAIN=self.OIDC_DOMAIN,
            CLIENT_ID=self.OIDC_CLIENT_ID
        )

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

    def client_id(self):
        return self.OIDC_CLIENT_ID

    def client_secret(self):
        return self.OIDC_CLIENT_SECRET
