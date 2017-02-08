#!/usr/bin/python
"""Configuration loader for different environments."""

import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


class Config(object):
    """Defaults for the configuration objects."""
    DEBUG = True
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = os.environ['SECRET_KEY']


class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
