import os
import tempfile
import pytest
from dashboard.app import app


@pytest.fixture
def client():
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.app.config['TESTING'] = True
    client = app.test_client()

    with app.app_context():
        app.init_db()

    yield client

    os.close(db_fd)
    os.unlink(app.config['DATABASE'])


def test_root(client):
    assert client.get('/').status_code() == 302
