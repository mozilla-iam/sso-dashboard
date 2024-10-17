"""Governs loading all tile displayed to the user in the Dashboard."""

import logging
import os
import urllib3
from urllib3.exceptions import HTTPError

logger = logging.getLogger()


class CDNTransfer(object):
    """Download apps.yaml from CDN"""

    def __init__(self, app_config):
        """
        Handles fetching and loading the apps.yml file
        When a CDNTransfer Object is instantiated, the CDN is checked for
        an updated version of apps.yml.  If a ETags are mismatched then
        a new version is available. We download it which causes the worker
        to reload.  If the Etags of the CDN matches that on disk, we
        simply read from the disk.
        """
        self.app_config = app_config
        self.apps_yml = None
        self.url = self.app_config.CDN + "/apps.yml"
        # Check if there is an update to apps.yml
        self.sync_config()

    def is_updated(self):
        """Compare etag of what is in CDN to what is on disk."""
        http = urllib3.PoolManager()
        response = http.request("HEAD", self.url)

        if response.headers["ETag"] != self._etag():
            logger.warning("Etags do not match")
            return True
        else:
            return False

    def _update_etag(self, etag):
        """Update the etag file."""
        this_dir = os.path.dirname(__file__)
        filename = os.path.join(this_dir, "../data/{name}").format(name="apps.yml-etag")
        with open(filename, "w+") as c:
            c.write(etag)

    def _etag(self):
        """get the etag from the file"""
        this_dir = os.path.dirname(__file__)
        filename = os.path.join(this_dir, "../data/{name}").format(name="apps.yml-etag")
        try:
            with open(filename, "r") as f:
                # What happens if we read nothing?
                etag = f.read()
            return etag
        # This can fail with
        # * FileNotFoundError
        # * PermissionError
        # TODO(bhee): Do we want to be specific?
        except Exception:
            """If the etag file is not found return a fake etag."""
            logger.exception("Error fetching etag")
            return "12345678"

    def _download_config(self):
        """Download the apps.yml from the CDN."""
        http = urllib3.PoolManager()

        try:
            logger.info("Downloading apps.yml from CDN")
            response = http.request("GET", self.url)
            if response.status != 200:
                raise HTTPError(f"HTTP request failed with status {response.status}")
        except HTTPError as exc:
            exc.add_note("Request for apps.yml failed")
            raise

        this_dir = os.path.dirname(__file__)
        filename = os.path.join(this_dir, "../data/{name}").format(name="apps.yml")

        try:
            # As soon as this file is closed, gunicorn should reload the workers
            with open(filename, "wb") as file:
                file.write(response.data)
                # Ensure all data is flushed to disk
                file.flush()
                # Ensure data is written to disk before proceeding
                os.fsync(file.fileno())
                # It is very important that the ETag file is written before we close
                # apps.yml file. Otherwise, this may cause a reload loop
                self._update_etag(response.headers["ETag"])
        except Exception as exc:
            exc.add_note("An error occurred while attempting to write apps.yml")
            raise

    def _load_apps_yml(self):
        """Load the apps.yml file on disk"""
        this_dir = os.path.dirname(__file__)
        filename = os.path.join(this_dir, "../data/{name}").format(name="apps.yml")
        with open(filename, "r") as file:
            logger.info("Loading apps.yml from disk")
            self.apps_yml = file.read()

    def sync_config(self):
        """Determines if the config file is updated and if so fetches the new config."""
        try:
            # Check if the CDN has an updated apps.yml
            if self.is_updated():
                logger.info("Config file is updated fetching new config.")
                self._download_config()
        except Exception:
            logger.exception("Problem fetching config file")

        # Load the apps.yml file into self.apps_list
        # if it isn't already loaded
        try:
            if not self.apps_yml:
                self._load_apps_yml()
        except Exception:
            logger.exception("Problem loading the config file")


class Tile(object):
    def __init__(self, app_config):
        """
        :param app_config: Flask app config object.
        """
        self.app_config = app_config

    def find_by_user(self, email):
        """Return all the tiles for a given user."""
        pass

    def find_by_group(self, group):
        """Return all the tiles for a given group."""
        pass

    def find_by_profile(self, userprofile):
        """Takes a flask_session of userinfo and return all apps for user and groups."""
        pass

    def all(self):
        """Return all apps."""
        pass
