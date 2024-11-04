from pathlib import Path
import pytest
from flask import Flask
from dashboard import config
from dashboard import vanity
from dashboard.models import tile
from dashboard.op import yaml_loader


@pytest.fixture
def externals(monkeypatch):
    # Internal to the way dashboard.models.tile.CDNTransfer works.
    models_dir = Path(__file__).parent / "models"
    monkeypatch.setattr("os.path.dirname", lambda _: models_dir)
    # Internal to how Configs work.
    monkeypatch.setenv("SSO-DASHBOARD_REDIS_CONNECTOR", "foobar")
    monkeypatch.setenv("SSO-DASHBOARD_SECRET_KEY", "deadbeef")
    monkeypatch.setenv("SSO-DASHBOARD_S3_BUCKET", "")
    monkeypatch.setenv("SSO-DASHBOARD_FORBIDDEN_PAGE_PUBLIC_KEY", "")
    monkeypatch.setenv("SSO-DASHBOARD_CDN", "https://localhost")


@pytest.fixture
def app_config(externals):
    return config.Default()


@pytest.fixture
def dashboard_app(app_config):
    """
    A mini instance of the app.
    """
    app = Flask("dashboard")
    app.config.from_object(app_config)
    yield app


@pytest.fixture
def cdn(app_config):
    return tile.CDNTransfer(app_config)


@pytest.fixture
def client(dashboard_app):
    return dashboard_app.test_client()


class TestVanity:
    def test_router(self, dashboard_app, cdn, client):
        router = vanity.Router(dashboard_app, cdn)
        router.setup()
        response = client.get("/netlify")
        assert response.location == "https://some-url-for-netlify", "Did not properly redirect vanity URL"
