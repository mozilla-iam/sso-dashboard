import pytest
from dashboard.app import app
from flask import url_for


def test_root(client):
    assert client.get(url_for('/')).status_code == 302
