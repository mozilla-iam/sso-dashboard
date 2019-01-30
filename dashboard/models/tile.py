"""Governs loading all tile displayed to the user in the Dashboard."""
import boto3
import logging
import os


from boto3.dynamodb.conditions import Attr


logger = logging.getLogger(__name__)


class S3Transfer(object):
    """News up and does the job if configuration specifies S3 for data transfer."""

    def __init__(self, app_config):
        self.app_config = app_config
        self.client = None
        self.s3_bucket = self.app_config.S3_BUCKET
        self.apps_yml = None

    def connect_s3(self):
        if not self.client:
            self.client = boto3.client("s3")

    def is_updated(self):
        """Compare etag of what is in bucket to what is on disk."""
        self.connect_s3()
        try:
            self.client.head_object(
                Bucket=self.s3_bucket, Key="apps.yml", IfMatch=self._etag()
            )
            return False
        except Exception as e:
            logger.error("Etags do not match as a result of {error}".format(error=e))
            return True

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
        self.connect_s3()
        apps_yml = self.client.get_object(Bucket=self.s3_bucket, Key="apps.yml")

        response = self.client.head_object(Bucket=self.s3_bucket, Key="apps.yml")

        self.apps_yml = apps_yml.get("Body").read().decode("utf-8")

        this_dir = os.path.dirname(__file__)
        filename = os.path.join(this_dir, "../data/{name}").format(name="apps.yml")
        c = open(filename, "w+")
        c.write(self.apps_yml)
        c.close()
        self._update_etag(response.get("ETag"))

    def _touch(self):
        fname = "dashboard/app.py"
        fhandle = open(fname, "a")
        try:
            os.utime(fname, None)
        finally:
            fhandle.close()

    def sync_config(self):
        self.connect_s3()
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
