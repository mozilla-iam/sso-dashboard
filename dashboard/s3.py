"""Class for operations to fetch items from boto3."""
import boto3
import os

from utils import get_secret


class AppFetcher(object):
    def __init__(self):
        self.client = boto3.client('s3')
        self.s3_bucket = get_secret('sso-dashboard.s3_bucket', {'app': 'sso-dashboard'})

    def is_updated(self):
        """Compare etag of what is in bucket to what is on disk."""
        try:
            self.client.head_object(
                Bucket=self.s3_bucket,
                Key='apps.yml',
                IfMatch=self._etag()
            )
            return False
        except Exception as e:
            print("Etags do not match as a result of {error}").format(error=e)
            return True

    def last_update(self):
        this_dir = os.path.dirname(__file__)
        filename = os.path.join(this_dir, 'data/apps.yml')
        return abs(os.path.getmtime(filename))

    def _get_images(self):
        images = self.client.list_objects(
            Bucket=self.s3_bucket,
            Prefix='images'
        )

        for image in images['Contents']:
            print(image['Key'])
            this_image = self.client.get_object(
                Bucket=self.s3_bucket,
                Key=image['Key']
            )

            this_dir = os.path.dirname(__file__)
            filename = os.path.join(
                this_dir,
                'static/img/logos/{name}'
            ).format(
                name=image['Key'].split('/')[1]
            )

            f = open(filename, 'w+')
            f.write(this_image['Body'].read())
            f.close()

    def _update_etag(self, etag):
        this_dir = os.path.dirname(__file__)
        filename = os.path.join(this_dir, 'data/{name}').format(
            name='apps.yml-etag'
        )
        c = open(filename, 'w+')
        c.write(etag)
        c.close()

    def _etag(self):
        this_dir = os.path.dirname(__file__)
        filename = os.path.join(this_dir, 'data/{name}').format(
            name='apps.yml-etag'
        )
        try:
            return open(filename, 'r').read()
        except Exception as e:
            print(e)
            return "12345678"

    def _get_config(self):
        config = self.client.get_object(
            Bucket=self.s3_bucket,
            Key='apps.yml'
        )

        this_dir = os.path.dirname(__file__)
        filename = os.path.join(this_dir, 'data/{name}').format(
            name='apps.yml'
        )
        c = open(filename, 'w+')
        c.write(config['Body'].read())
        c.close()
        self._update_etag(config['ETag'])

    def _touch(self):
        fname = 'app.py'
        fhandle = open(fname, 'a')
        try:
            os.utime(fname, None)
        finally:
            fhandle.close()

    def sync_config_and_images(self):
        try:
            if self.is_updated():
                print("Config file is updated fetching new config.")
                self._get_images()
                self._get_config()
                # Touch app.py to force a gunicorn reload
                self._touch()
                return True
            else:
                return False
                # Do nothing
        except Exception as e:
            print(
                "Problem fetching new images and config file {error}".format(
                    error=e
                )
            )
