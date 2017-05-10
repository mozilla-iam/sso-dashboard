from dotenv import find_dotenv, load_dotenv

from dashboard import app as sso_dashboard
from dashboard.op import authzero


def setup_test():
    """Load dotenv for comparison as part of test setup."""
    load_dotenv(find_dotenv())


def test_object():
    """Test that config values believed to be set are set."""
    config = sso_dashboard.oidc_config
    management = authzero.AccessToken(config)
    assert management is not None


def test_http_client():
    """Test http client loads and returns."""
    config = sso_dashboard.oidc_config
    management = authzero.AccessToken(config)

    client = management.http_client()
    assert client is not None


def test_payload():
    """Test payload has requisite values."""
    config = sso_dashboard.oidc_config
    management = authzero.AccessToken(config)

    payload = management.payload()

    assert payload is not None


def test_get_token():
    """Test token retreival."""
    config = sso_dashboard.oidc_config
    management = authzero.AccessToken(config)
    token = management.get_token()
    print(token)
    assert token['access_token'] is not None
