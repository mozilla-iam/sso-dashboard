#!/usr/bin/python
"""Route decorator test ."""


from dashboard import app as sso_dashboard


class TestDashboardRoutes(object):
    """Dashboard client instantiation object."""

    def __init__(self):
        """Will return a flask testing client for route testing."""
        self.app = self.create_app()

    def create_app(self):
        """Set any additional test time config params here."""
        sso_dashboard.app.config['TESTING'] = True
        return sso_dashboard.app.test_client()


CLIENT = TestDashboardRoutes()


def test_index():
    """Validate the resulting body of the index page."""
    result = CLIENT.app.get('/')
    assert b'HelloWorld' in result.data
