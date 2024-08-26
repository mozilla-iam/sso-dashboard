import os

from everett.manager import ConfigManager
from everett.manager import ConfigOSEnv

# -*- coding: utf-8 -*-

"""Mozilla Single Signon Dashboard."""

__author__ = """Andrew Krug"""
__email__ = "akrug@mozilla.com"
__version__ = "0.0.1"


__all__ = ["app", "auth", "config", "models", "s3", "utils", "vanity"]


def get_config():
    return ConfigManager([ConfigOSEnv()])
