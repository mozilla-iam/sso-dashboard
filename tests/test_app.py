import os


class TestApp(object):
    def setup_class(self):
        os.environ["DASHBOARD_CONFIG_INI"] = "tests/sso-dashboard.ini"
        os.environ["AWS_XRAY_SDK_ENABLED"] = "false"
        from dashboard import app
        app.app.testing = True
        self.app = app.app.test_client()

    def test_default_unauthenticated_root(self):
        response = self.app.get("/", headers={}, follow_redirects=False)
        assert response.status_code() == 302
        assert response.headers['Location'] == 'http://localhost/dashboard'

    def test_prod_unauthenticated_root(self):
        self.config['SERVER_NAME'] = 'sso.mozilla.com'
        response = self.app.get("/", headers={}, follow_redirects=False)
        assert response.status_code() == 302
        assert response.headers['Location'] == 'https://sso.mozilla.com/dashboard'
