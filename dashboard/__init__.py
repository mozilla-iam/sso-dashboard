import os

from credstash import getSecret
from credstash import ItemNotFound
from everett import NO_VALUE
from everett.manager import listify

from everett.manager import ConfigManager
from everett.manager import ConfigIniEnv

# -*- coding: utf-8 -*-

"""Mozilla Single Signon Dashboard."""

__author__ = """Andrew Krug"""
__email__ = 'akrug@mozilla.com'
__version__ = '0.0.1'


__all__ = [
    'app',
    'auth',
    'config',
    'models',
    'person',
    's3',
    'utils',
    'vanity'
]


class CredstashEnv(object):
    def get(self, key, namespace=None):
        # The namespace is either None, a string or a list of
        # strings. This converts it into a list.
        namespace = listify(namespace)
        try:
            if len(namespace) > 0:
                secret = getSecret(
                    name='{}.{}'.format(namespace[0], key),
                    context={'app': 'sso-dashboard'},
                    region="us-east-1"
                )
            else:
                secret = None
        except ItemNotFound:
            secret = None

        if secret is not None:
            return secret

        return NO_VALUE


def get_config():
    return ConfigManager(
        [
            ConfigIniEnv([
                os.environ.get('DASHBOARD_CONFIG_INI'),
                '~/.sso-dashboard.ini',
                '/etc/sso-dashboard.ini'
            ]),
            CredstashEnv()
        ]
    )
