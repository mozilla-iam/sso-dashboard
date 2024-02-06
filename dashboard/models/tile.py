"""Governs loading all tile displayed to the user in the Dashboard."""

import logging
import os
import urllib3

logger = logging.getLogger(__name__)


class CDNTransfer(object):
    """Download apps.yaml from CDN"""

    def __init__(self, app_config):
        self.app_config = app_config
        """Used in app.py load apps.yml"""
        self.apps_yml = None
        self.url = self.app_config.CDN + "/apps.yml"

    def is_updated(self):
        """Compare etag of what is in CDN to what is on disk."""
        http = urllib3.PoolManager()
        response = http.request("HEAD", self.url)

        if response.headers["ETag"] != self._etag():
            logger.error("Etags do not match")
            return True
        else:
            return False

    def last_update(self):
        this_dir = os.path.dirname(__file__)
        filename = os.path.join(this_dir, "../data/apps.yml")
        return abs(os.path.getmtime(filename))

    def _update_etag(self, etag):
        """Update the etag file."""
        this_dir = os.path.dirname(__file__)
        filename = os.path.join(this_dir, "../data/{name}").format(name="apps.yml-etag")
        c = open(filename, "w+")
        c.write(etag)
        c.close()

    def _etag(self):
        """get the etag from the file"""
        this_dir = os.path.dirname(__file__)
        filename = os.path.join(this_dir, "../data/{name}").format(name="apps.yml-etag")
        try:
            return open(filename, "r").read()
        except Exception as e:
            """If the etag file is not found return a default etag."""
            logger.info("Error fetching etag: {e}".format(e=e))
            return "12345678"

    def _get_config(self):
        """Download the apps.yml from the CDN."""
        http = urllib3.PoolManager()
        response = http.request("GET", self.url)
        this_dir = os.path.dirname(__file__)
        filename = os.path.join(this_dir, "../data/{name}").format(name="apps.yml")
        with open(filename, "wb") as file:
            file.write(response.data)
        self.apps_yml = response.data.decode("utf-8")
        self._update_etag(response.headers["ETag"])

    def _touch(self):
        fname = "dashboard/app.py"
        fhandle = open(fname, "a")
        try:
            os.utime(fname, None)
        finally:
            fhandle.close()

    def sync_config(self):
        """Determines if the config file is updated and if so fetches the new config."""
        try:
            # this is for checking updates after the app has started
            if self.is_updated():
                logger.info("Config file is updated fetching new config.")
                self._get_config()
                # Touch app.py to force a gunicorn reload
                self._touch()
                return True
            else:
                # this is needed on initial app startup,
                # otherwise the app will not have a config
                self._get_config()
                return False
        except Exception as e:
            print(e)
            logger.error("Problem fetching config file {error}".format(error=e))


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
