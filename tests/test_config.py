from dashboard import config


class TestConfig(object):
    def test_object_init(self):
        c = config.Config()

        assert c.DEBUG is True
        assert c.TESTING is False
        assert c.CSRF_ENABLED is True
        assert c.SECRET_KEY is not None
        assert c.SERVER_NAME is not None

    def test_production_settings(self):
        c = config.ProductionConfig()

        assert c.DEBUG is False
        assert c.TESTING is False
        assert c.CSRF_ENABLED is True
        assert c.SECRET_KEY is not None
        assert c.SERVER_NAME is not None
        assert c.PREFERRED_URL_SCHEME is 'https'

    def test_development_settings(self):
        c = config.DevelopmentConfig()

        assert c.TESTING is False
        assert c.CSRF_ENABLED is True
        assert c.SECRET_KEY is not None
        assert c.SERVER_NAME is not None


class TestOIDCObject(object):
    def test_object_init(self):
        o = config.OIDCConfig()
        assert o is not None

    def test_auth_endpoint_method(self):
        o = config.OIDCConfig()
        o.OIDC_DOMAIN = 'foo.bar.com'
        assert o.auth_endpoint() == 'https://foo.bar.com/authorize'
        assert o is not None

    def test_user_endpoint_method(self):
        o = config.OIDCConfig()
        o.OIDC_DOMAIN = 'foo.bar.com'
        assert o.userinfo_endpoint() == 'https://foo.bar.com/userinfo'
        assert o is not None

    def test_token_endpoint_method(self):
        o = config.OIDCConfig()
        o.OIDC_DOMAIN = 'foo.bar.com'
        assert o.token_endpoint() == 'https://foo.bar.com/oauth/token'
        assert o is not None

    def test_client_id(self):
        o = config.OIDCConfig()
        o.OIDC_DOMAIN = 'foo.bar.com'
        o.OIDC_CLIENT_SECRET = 'abc123'
        assert o.client_secret == 'abc123'
        assert o is not None
