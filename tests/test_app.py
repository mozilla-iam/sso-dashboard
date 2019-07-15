import os
import tempfile
import pytest
from dashboard.app import app


@pytest.fixture
def app():
    app = create_app()
    return app


def test_root(client):
    res = client.get(url_for('/'))
    assert res.status_code == 302
