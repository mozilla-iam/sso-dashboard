import os

from everett.manager import ConfigManager
from everett.manager import ConfigOSEnv
from everett.ext.inifile import ConfigIniEnv

# -*- coding: utf-8 -*-

"""Mozilla Single Signon Dashboard."""

__author__ = """Andrew Krug"""
__email__ = "akrug@mozilla.com"
__version__ = "0.0.1"


__all__ = ["app", "auth", "config", "models", "s3", "utils", "vanity"]



def get_config():
    return ConfigManager(
        [
            ConfigIniEnv(
                [
                    os.environ.get("DASHBOARD_CONFIG_INI"),
                    "~/.sso-dashboard.ini",
                    "/etc/sso-dashboard.ini",
                ]
            ),
            ConfigOSEnv(),
        ]
    )
