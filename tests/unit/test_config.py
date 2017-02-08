#!/usr/bin/python
"""Authentication class test."""

import os
from dotenv import load_dotenv, find_dotenv
from os.path import join, dirname
from dashboard import app as sso_dashboard


class TestDashboardRoutes(object):
    """Dashboard client instantiation object."""

    def __init__(self):
        """Will return a flask testing client for route testing."""
        self.app = self.create_app()

    def create_app(self):
        """Set any additional test time config params here."""
        sso_dashboard.app.config['TESTING'] = True
        #return sso_dashboard.app.test_client()
        return True

CLIENT = TestDashboardRoutes()


def setup_test():
    """Load dotenv for comparison as part of test setup."""
    load_dotenv(find_dotenv())


def test_config():
    """Tests that config values believed to be set are set."""
    c = sso_dashboard.app.config
    assert c['DEBUG'] == True
    assert c['SECRET_KEY'] == "this is a secret key"
