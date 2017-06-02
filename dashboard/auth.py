#!/usr/bin/python
import os

"""Class that governs all authentication with open id connect."""
from flask_pyoidc.flask_pyoidc import OIDCAuthentication


class nullOpenIDConnect(object):
    """Null object for ensuring test cov if new up fails."""

    def __init__(self):
        """None based versions of OIDC Object."""
        pass


class OpenIDConnect(object):
    """Auth object for login, logout, and response validation."""

    def __init__(self, configuration):
        """Object initializer for auth object."""
        self.oidc_config = configuration

    def client_info(self):
        return dict(
            client_id=self.oidc_config.client_id(),
            client_secret=self.oidc_config.client_secret()
        )

    def provider_info(self):
        return dict(
            issuer=self.oidc_config.OIDC_DOMAIN
        )

    def auth(self, app):
        o = OIDCAuthentication(
            app,
            issuer='https://' + self.provider_info()['issuer'],
            client_registration_info=self.client_info()
        )
        """ Patch rewrites redirect_uri to only
        SSL if running in production or stage. """
        if os.environ['ENVIRONMENT'] == 'Production':
            redirect_uri = o.client.registration_response['redirect_uris'][0]
            o.client.registration_response['redirect_uris'][0] = \
                redirect_uri.replace('http', 'https')
        return o
