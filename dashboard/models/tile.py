"""Governs loading all tile displayed to the user in the Dashboard."""
import boto3
import logging
import os
import urllib3

from boto3.dynamodb.conditions import Attr


logger = logging.getLogger(__name__)


class CDNTransfer(object):
    """Download app.yaml from CDN"""
    def __init__(self, app_config):
        self.app_config = app_config
        self.apps_yml = None
        self.url = self.app_config.CDN + "/apps.yml"

    def is_updated(self):
        """Compare etag of what is in CDN to what is on disk."""

        http = urllib3.PoolManager()
        response = http.request('HEAD', self.url)
        lastestEtag = response.headers["ETag"]

        if (lastestEtag != self._etag()):
            logger.error("Etags do not match")
            return True
        else:
            return False



    def last_update(self):
        this_dir = os.path.dirname(__file__)
        filename = os.path.join(this_dir, "../data/apps.yml")
        return abs(os.path.getmtime(filename))

    def _update_etag(self, etag):
        this_dir = os.path.dirname(__file__)
        filename = os.path.join(this_dir, "../data/{name}").format(name="apps.yml-etag")
        c = open(filename, "w+")
        c.write(etag)
        c.close()

    def _etag(self):
        this_dir = os.path.dirname(__file__)
        filename = os.path.join(this_dir, "../data/{name}").format(name="apps.yml-etag")
        try:
            return open(filename, "r").read()
        except Exception as e:
            logger.error("Error fetching etag: {e}".format(e=e))
            return "12345678"

    def _get_config(self):
        http = urllib3.PoolManager()
        # print("self.url = "+ self.url)
        response = http.request('GET', self.url)
        #print("response: "+ response.data)
        this_dir = os.path.dirname(__file__)
        filename = os.path.join(this_dir, "../data/{name}").format(name="apps.yml")
        with open(filename, 'wb') as file:
            file.write(response.data)
        self._update_etag(response.headers["ETag"])

    def _touch(self):
        fname = "dashboard/app.py"
        fhandle = open(fname, "a")
        try:
            os.utime(fname, None)
        finally:
            fhandle.close()

    def sync_config(self):
        try:
            if self.is_updated():
                logger.info("Config file is updated fetching new config.")
                self._get_config()
                # Touch app.py to force a gunicorn reload
                self._touch()
                return True
            else:
                self._get_config()
                return False
                # Do nothing
        except Exception as e:
            print(e)
            logger.error("Problem fetching config file {error}".format(error=e))





class DynamoTransfer(object):
    """News up and does the job if configuration specifies that dynamo should be used for app information."""

    def __init__(self, app_config):
        self.configuration_table_name = "sso-dashboard-apps"
        self.dynamodb = None

    def connect_dynamodb(self):
        if self.dynamodb is None:
            dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
            table = dynamodb.Table(self.configuration_table_name)
            self.dynamodb = table

    def sync_config(self):
        self.connect_dynamodb()
        results = self.dynamodb.scan(FilterExpression=Attr("name").exists())
        return results.get("Items", None)


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
