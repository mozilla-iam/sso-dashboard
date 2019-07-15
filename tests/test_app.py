import pytest
from dashboard.app import app
from flask import url_for
from flask import create_app
from flask import client


@pytest.fixture
def app():
    app = create_app()
    return app


def test_root(client):
    assert client.get(url_for('/')).status_code == 302
