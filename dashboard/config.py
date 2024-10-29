"""Configuration loader for different environments."""

import os
import base64
import datetime


class Default:
    """Defaults for the configuration objects."""

    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "local")
    DEBUG: bool = os.environ.get("SSO-DASHBOARD_DEBUG", "True") == "True"
    TESTING: bool = os.environ.get("SSO-DASHBOARD_TESTING", "True") == "True"

    CSRF_ENABLED: bool = os.environ.get("SSO-DASHBOARD_CSRF_ENABLED", "True") == "True"
    PERMANENT_SESSION: bool = os.environ.get("SSO-DASHBOARD_PERMANENT_SESSION", "True") == "True"
    PERMANENT_SESSION_LIFETIME: datetime.timedelta = datetime.timedelta(
        seconds=int(os.environ.get("SSO-DASHBOARD_PERMANENT_SESSION_LIFETIME", "86400"))
    )

    SESSION_COOKIE_SAMESITE: str = os.environ.get("SSO-DASHBOARD_SESSION_COOKIE_SAMESITE", "lax")
    SESSION_COOKIE_HTTPONLY: bool = os.environ.get("SSO-DASHBOARD_SESSION_COOKIE_HTTPONLY", "True") == "True"

    SECRET_KEY: str = os.environ["SSO-DASHBOARD_SECRET_KEY"]
    SERVER_NAME: str = os.environ.get("SSO-DASHBOARD_SERVER_NAME", "localhost:8000")
    SESSION_COOKIE_NAME: str
    CDN: str

    S3_BUCKET: str = os.environ["SSO-DASHBOARD_S3_BUCKET"]

    FORBIDDEN_PAGE_PUBLIC_KEY: bytes = base64.b64decode(os.environ["SSO-DASHBOARD_FORBIDDEN_PAGE_PUBLIC_KEY"])

    PREFERRED_URL_SCHEME: str = os.environ.get("SSO-DASHBOARD_PREFERRED_URL_SCHEME", "https")
    REDIS_CONNECTOR: str = os.environ["SSO-DASHBOARD_REDIS_CONNECTOR"]

    def __init__(self):
        self.SESSION_COOKIE_NAME = f"{self.SERVER_NAME}_session"
        self.CDN = os.environ.get("SSO-DASHBOARD_CDN", f"https://cdn.{self.SERVER_NAME}")


class OIDC:
    """Convienience Object for returning required vars to flask."""

    OIDC_DOMAIN: str = os.environ["SSO-DASHBOARD_OIDC_DOMAIN"]
    OIDC_CLIENT_ID: str = os.environ["SSO-DASHBOARD_OIDC_CLIENT_ID"]
    OIDC_CLIENT_SECRET: str = os.environ["SSO-DASHBOARD_OIDC_CLIENT_SECRET"]
    LOGIN_URL: str

    def __init__(self):
        """General object initializer."""
        self.LOGIN_URL = f"https://{self.OIDC_DOMAIN}/login?client={self.OIDC_CLIENT_ID}"

    @property
    def client_id(self):
        return self.OIDC_CLIENT_ID

    @property
    def client_secret(self):
        return self.OIDC_CLIENT_SECRET

    def auth_endpoint(self):
        return f"https://{self.OIDC_DOMAIN}/authorize"

    def token_endpoint(self):
        return f"https://{self.OIDC_DOMAIN}/oauth/token"

    def userinfo_endpoint(self):
        return f"https://{self.OIDC_DOMAIN}/userinfo"
