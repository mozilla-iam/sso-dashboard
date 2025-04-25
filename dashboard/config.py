"""Configuration loader for different environments."""

import os
import base64
import datetime


class Default:
    """Defaults for the configuration objects."""

    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "local")

    # Flask makes use of the `FLASK_DEBUG` environment variable, with or
    # without using `Flask.config.from_prefixed_env` (a method we don't
    # use).
    DEBUG: bool = os.environ.get("FLASK_DEBUG", "True") == "True"

    TESTING: bool = os.environ.get("TESTING", "True") == "True"

    CSRF_ENABLED: bool = os.environ.get("CSRF_ENABLED", "True") == "True"
    PERMANENT_SESSION: bool = os.environ.get("PERMANENT_SESSION", "True") == "True"
    PERMANENT_SESSION_LIFETIME: datetime.timedelta = datetime.timedelta(
        seconds=int(os.environ.get("PERMANENT_SESSION_LIFETIME", "86400"))
    )

    SESSION_COOKIE_SAMESITE: str = os.environ.get("SESSION_COOKIE_SAMESITE", "lax")
    SESSION_COOKIE_HTTPONLY: bool = os.environ.get("SESSION_COOKIE_HTTPONLY", "True") == "True"

    SECRET_KEY: str
    SERVER_NAME: str = os.environ.get("SERVER_NAME", "localhost:8000")
    SESSION_COOKIE_NAME: str
    CDN: str

    S3_BUCKET: str
    FORBIDDEN_PAGE_PUBLIC_KEY: bytes

    PREFERRED_URL_SCHEME: str = os.environ.get("PREFERRED_URL_SCHEME", "https")
    REDIS_CONNECTOR: str

    def __init__(self):
        self.SESSION_COOKIE_NAME = f"{self.SERVER_NAME}_session"
        self.CDN = os.environ.get("CDN", f"https://cdn.{self.SERVER_NAME}")
        self.REDIS_CONNECTOR = os.environ["REDIS_CONNECTOR"]
        self.SECRET_KEY = os.environ["SECRET_KEY"]
        self.S3_BUCKET = os.environ["S3_BUCKET"]
        self.FORBIDDEN_PAGE_PUBLIC_KEY = base64.b64decode(os.environ["FORBIDDEN_PAGE_PUBLIC_KEY"])


class OIDC:
    """Convienience Object for returning required vars to flask."""

    OIDC_DOMAIN: str
    OIDC_CLIENT_ID: str
    OIDC_CLIENT_SECRET: str
    OIDC_REDIRECT_URI: str
    LOGIN_URL: str

    def __init__(self):
        """General object initializer."""
        self.OIDC_DOMAIN = os.environ["OIDC_DOMAIN"]
        self.OIDC_CLIENT_ID = os.environ["OIDC_CLIENT_ID"]
        self.OIDC_CLIENT_SECRET = os.environ["OIDC_CLIENT_SECRET"]
        # Check for a prefixed environment variable, otherwise fallback to the
        # unprefixed one.
        if redirect_uri := os.environ.get("OIDC_REDIRECT_URI"):
            self.OIDC_REDIRECT_URI = redirect_uri
        else:
            self.OIDC_REDIRECT_URI = os.environ["OIDC_REDIRECT_URI"]
        self.LOGIN_URL = f"https://{self.OIDC_DOMAIN}/login?client={self.OIDC_CLIENT_ID}"

    @property
    def client_id(self):
        return self.OIDC_CLIENT_ID

    @property
    def client_secret(self):
        return self.OIDC_CLIENT_SECRET
