#!/usr/bin/python

"""Class that governs all authentication with open id connect."""
from oic.oic.message import IdToken, OpenIDSchema
from six.moves.urllib.parse import parse_qsl, urlparse
from flask_pyoidc.flask_pyoidc import OIDCAuthentication




class nullOpenIDConnect(object):
    """Null object for ensuring test cov if new up fails."""

    def __init__(self):
        """None based versions of OIDC Object."""
        pass


class OpenIDConnect(object):
    """Auth object for login, logout, and response validation."""

    def __init__(self):
        """Object initializer for auth object."""
        pass
