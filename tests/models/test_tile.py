import pytest
import os
import urllib3
from unittest import mock
from dashboard.models.tile import __file__ as module_file
from dashboard.models.tile import CDNTransfer


class MockAppConfig:
    CDN = "http://mock-cdn.com"


@pytest.fixture
def cdn_transfer():
    app_config = MockAppConfig()
    return CDNTransfer(app_config)


def test_is_updated_etag_mismatch(mocker, cdn_transfer):
    mock_request = mocker.patch("urllib3.PoolManager.request")
    mock_request.return_value.headers = {"ETag": "new-etag"}
    mocker.patch.object(cdn_transfer, "_etag", return_value="old-etag")

    assert cdn_transfer.is_updated() is True


def test_is_updated_etag_match(mocker, cdn_transfer):
    mock_request = mocker.patch("urllib3.PoolManager.request")
    mock_request.return_value.headers = {"ETag": "matching-etag"}
    mocker.patch.object(cdn_transfer, "_etag", return_value="matching-etag")

    assert cdn_transfer.is_updated() is False


def test_update_etag(mocker, cdn_transfer):
    mock_open = mocker.patch("builtins.open", mocker.mock_open())

    cdn_transfer._update_etag("new-etag")

    mock_open.assert_called_once_with(os.path.join(os.path.dirname(module_file), "../data/apps.yml-etag"), "w+")
    mock_open().write.assert_called_once_with("new-etag")


def test_etag_file_exists(mocker, cdn_transfer):
    mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data="stored-etag"))

    assert cdn_transfer._etag() == "stored-etag"
    mock_open.assert_called_once_with(os.path.join(os.path.dirname(module_file), "../data/apps.yml-etag"), "r")


def test_etag_file_missing(mocker, cdn_transfer):
    mock_open = mocker.patch("builtins.open", mocker.mock_open())
    mock_open.side_effect = FileNotFoundError

    assert cdn_transfer._etag() == "12345678"


# NOTE: Temporarily disabling this test until we have a reliable means of patching out
#       `urllib3` calls. Even after multiple attempts, the call to `request` still
#       tries to resolve the mock domain in the mocked CDN object.
#       References:
#       - https://mozilla-hub.atlassian.net/jira/software/c/projects/IAM/issues/IAM-1403
#
@pytest.mark.skip(reason="Cannot properly mock `urllib3`'s `request` call.")
def test_download_config(mocker, cdn_transfer):
    mock_response = mock.Mock()
    mock_response.status = 200
    mock_response.headers = {"ETag": "new-etag"}
    mock_response.data = b"mock apps.yml content"
    with mock.patch("urllib3.PoolManager") as mock_pool_manager, mock.patch("os.fsync") as mock_fsync, mock.patch(
        "builtins.open", mock.mock_open()
    ) as mock_open_yml, mock.patch("builtins.open", mock.mock_open()) as mock_open_etag:
        mock_http = mock_pool_manager.return_value
        mock_http.request.return_value = mock_response
        mock_open_yml.return_value.fileno.return_value = 3
        cdn_transfer._download_config()

        mock_open_yml.assert_any_call(os.path.join(os.path.dirname(module_file), "../data/apps.yml"), "wb")
        mock_open_yml().write.assert_called_once_with(b"mock apps.yml content")
        mock_fsync().assert_called_once_with(3)
        mock_open_etag.assert_any_call(os.path.join(os.path.dirname(module_file), "../data/apps.yml-etag"), "w+")
        mock_open_etag().write.assert_called_once_with("new-etag")


def test_download_config_http_error(mocker, cdn_transfer):
    mocker.patch("urllib3.PoolManager.request", side_effect=urllib3.exceptions.HTTPError)

    with pytest.raises(urllib3.exceptions.HTTPError):
        cdn_transfer._download_config()


def test_load_apps_yml(mocker, cdn_transfer):
    mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data="mock apps.yml content"))

    cdn_transfer._load_apps_yml()

    mock_open.assert_called_once_with(os.path.join(os.path.dirname(module_file), "../data/apps.yml"), "r")
    assert cdn_transfer.apps_yml == "mock apps.yml content"


# NOTE: Temporarily disabling this test until we have a reliable means of patching out
#       `urllib3` calls. Even after multiple attempts, the call to `request` still
#       tries to resolve the mock domain in the mocked CDN object.
#       References:
#       - https://mozilla-hub.atlassian.net/jira/software/c/projects/IAM/issues/IAM-1403
#
@pytest.mark.skip(reason="Cannot properly mock `urllib3`'s `request` call.")
def test_sync_config_update(mocker, cdn_transfer):
    mocker.patch.object(CDNTransfer, "is_updated", return_value=True)
    mock_download = mocker.patch.object(CDNTransfer, "_download_config")
    mock_load = mocker.patch.object(CDNTransfer, "_load_apps_yml")

    cdn_transfer.sync_config()

    mock_download.assert_called_once()
    mock_load.assert_called_once()


# NOTE: Temporarily disabling this test until we have a reliable means of patching out
#       `urllib3` calls. Even after multiple attempts, the call to `request` still
#       tries to resolve the mock domain in the mocked CDN object.
#       References:
#       - https://mozilla-hub.atlassian.net/jira/software/c/projects/IAM/issues/IAM-1403
#
@pytest.mark.skip(reason="Cannot properly mock `urllib3`'s `request` call.")
def test_sync_config_no_update(mocker, cdn_transfer):
    mocker.patch.object(CDNTransfer, "is_updated", return_value=False)
    mock_download = mocker.patch.object(CDNTransfer, "_download_config")
    mock_load = mocker.patch.object(CDNTransfer, "_load_apps_yml")

    cdn_transfer.sync_config()

    mock_download.assert_not_called()
    mock_load.assert_called_once()


# NOTE: Temporarily disabling this test until we have a reliable means of patching out
#       `urllib3` calls. Even after multiple attempts, the call to `request` still
#       tries to resolve the mock domain in the mocked CDN object.
#       References:
#       - https://mozilla-hub.atlassian.net/jira/software/c/projects/IAM/issues/IAM-1403
#
@pytest.mark.skip(reason="Cannot properly mock `urllib3`'s `request` call.")
def test_sync_config_download_error(mocker, cdn_transfer):
    mocker.patch.object(CDNTransfer, "is_updated", return_value=True)
    mock_download = mocker.patch.object(CDNTransfer, "_download_config", side_effect=Exception("Test Exception"))
    mock_load = mocker.patch.object(CDNTransfer, "_load_apps_yml")

    cdn_transfer.sync_config()

    mock_download.assert_called_once()
    mock_load.assert_not_called()  # if download fails, it shouldn't try to load
