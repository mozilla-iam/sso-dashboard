import os

from everett.manager import ConfigManager  # type: ignore
from everett.manager import ConfigOSEnv  # type: ignore

# -*- coding: utf-8 -*-

"""Mozilla Single Signon Dashboard."""

__author__ = """Andrew Krug"""
__email__ = "akrug@mozilla.com"
__version__ = "0.0.1"


__all__ = ["app", "auth", "config", "models", "s3", "utils", "vanity"]


def get_config():
    return ConfigManager([ConfigOSEnv()])
