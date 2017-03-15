#!/usr/bin/python
"""Authentication class test."""


from dashboard import app as sso_dashboard


def setup_test():
    """Load dotenv for comparison as part of test setup."""
    load_dotenv(find_dotenv())


def test_config():
    """Test that config values believed to be set are set."""
    c = sso_dashboard.app.config
    assert c['DEBUG'] == True
    assert c['SECRET_KEY'] == "this is a secret key"
