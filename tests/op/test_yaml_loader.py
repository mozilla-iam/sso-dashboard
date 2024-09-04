import pytest
import yaml
from unittest.mock import patch, MagicMock
from dashboard.op.yaml_loader import Application

# Testing data
apps = """
apps:
  - application:
      name: "Test Application"
      url: "https://example.com"
      vanity_url:
        - "/test-app"
  - application:
      name: "Long Application Name That Exceeds Limit"
      url: "https://example-long.com"
      vanity_url:
        - "/long-app"
"""


@pytest.fixture
def valid_application():
    return Application(apps)


def test_load_data(valid_application):
    assert valid_application.apps is not None
    assert len(valid_application.apps["apps"]) == 2
    assert valid_application.apps["apps"][1]["application"]["name"] == "Test Application"


def test_load_data_invalid_yaml():
    invalid_app = "invalid: : : yaml"
    with pytest.raises(TypeError):
        Application(invalid_app)


def test_render_data(valid_application):
    assert valid_application.apps["apps"][0]["application"]["name"] == "Long Application.."
    assert valid_application.apps["apps"][1]["application"]["alt_text"] == "Test Application"


def test_alphabetize(valid_application):
    assert valid_application.apps["apps"][0]["application"]["name"] == "Long Application.."
    assert valid_application.apps["apps"][1]["application"]["name"] == "Test Application"


def test_truncate(valid_application):
    assert valid_application._truncate("Short Name") == "Short Name"
    assert valid_application._truncate("This is a very long application name") == "This is a very l.."


def test_vanity_urls(valid_application):
    redirects = valid_application.vanity_urls()
    assert len(redirects) == 2
    assert redirects[0] == {"/long-app": "https://example-long.com"}
    assert redirects[1] == {"/test-app": "https://example.com"}


def test_vanity_urls_no_vanity():
    app_no_vanity = """
    apps:
      - application:
          name: "No Vanity App"
          url: "https://no-vanity.com"
    """
    app = Application(app_no_vanity)
    redirects = app.vanity_urls()
    assert len(redirects) == 0


def test_no_apps_present(valid_application):
    del valid_application.apps["apps"]

    assert len(valid_application.vanity_urls()) == 0
