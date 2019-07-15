import pytest
from dashboard.app import app
from flask import url_for


@pytest.fixture
def client():
    db_fd, dashboard.app.config['DATABASE'] = tempfile.mkstemp()
    dashboard.app.config['TESTING'] = True
    client = dashboard.app.test_client()

    with dashboard.app.app_context():
        dashboard.init_db()

    yield client

    os.close(db_fd)
    os.unlink(dashboard.app.config['DATABASE'])


def test_root(client):
    assert client.get('/').status_code() == 302
