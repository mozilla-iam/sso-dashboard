from dotenv import load_dotenv, find_dotenv
from dashboard import app as sso_dashboard
from dashboard.op import authzero
import os
import json
import base64


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
    print token
    assert token['access_token'] is not None


def test_token_decoding():
    """Attempt token decode and validation."""
    config = sso_dashboard.oidc_config
    management = authzero.AccessToken(config)
    token = management.get_token()
    decoder = authzero.TokenOperations(token['access_token'])
    decoded_payload = decoder.decode(os.environ['AUTH0_SIGNING_SECRET'])
    print token
    print decoded_payload
    assert 0
    assert decoded_payload['sub'] is not None
    assert decoded_payload['iss'] is not None
    assert decoded_payload['exp'] is not None
    assert decoded_payload['scope'] is not None
    assert decoded_payload['aud'] is not None
    #TBD
    #assert decoded_payload['jti'] is not None

def test_auth0_library():
    """Attempt connect to management API."""
    config = sso_dashboard.oidc_config
    management = authzero.AccessToken(config)
    token = management.get_token()
    decoder = authzero.TokenOperations(token['access_token'])
    decoded_payload = decoder.decode(os.environ['AUTH0_SIGNING_SECRET'])
    management_api = authzero.Managment(token['access_token'], domain=None)
    client = management_api.get_client()
    print client.connections.all()
    assert 0
