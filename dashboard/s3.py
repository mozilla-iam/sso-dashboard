import os,sys
import boto3
from datetime import datetime

"""Class for operations to fetch items from boto3."""

class AppFetcher(object):
    def __init__(self):
        self.client = boto3.client('s3')
        self.s3_bucket = os.environ['S3_BUCKET']

    def is_updated(self):
        """
        Compares two date times
        Thu, 09 Mar 2017 23:15:30 GMT is Amazon Format
        """
        response = self.client.head_object(
            Bucket=self.s3_bucket,
            Key='apps.yml'
        )

        last_mod = datetime.strptime(
            response['ResponseMetadata']['HTTPHeaders']['last-modified'],
            '%a, %d %b %Y %H:%M:%S %Z'
        )

        last_mod = last_mod.strftime('%s')

        if last_mod > self.last_update():
            return True
        else:
            return False

    def last_update(self):
        this_dir = os.path.dirname(__file__)
        filename = os.path.join(this_dir, 'data/apps.yml')
        return os.path.getmtime(filename)

    def __get_images(self):
        images = self.client.list_objects(
            Bucket=self.s3_bucket,
            Prefix='images'
        )

        for image in images['Contents']:
            print image['Key']
            this_image = self.client.get_object(
                Bucket=self.s3_bucket,
                Key=image['Key']
            )

            this_dir = os.path.dirname(__file__)
            filename = os.path.join(this_dir, 'static/img/logos/{name}').format(
                name=image['Key'].split('/')[1]
            )

            f = open(filename, 'w+')
            f.write(this_image['Body'].read())
            f.close()

    def __get_config(self):
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

    def sync_config_and_images(self):
        if self.is_updated():
            self.__get_images()
            self.__get_config()
        else:
            pass
            #Do nothing
