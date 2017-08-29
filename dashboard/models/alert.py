"""Operations governing the creation and destruction of user facing alerts."""
import binascii
import boto3
import os

from boto3.dynamodb.conditions import Attr


class Alert(object):
    """Primary object containing alert functions."""
    def __init__(self):
        self.alert_table_name = 'sso-dashboard-alert'
        self.dynamodb = None

    def connect_dynamodb(self):
        if self.dynamodb is None:
            dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
            table = dynamodb.Table(self.alert_table_name)
            self.dynamodb = table

    def create(self, alert_dict):
        """
        Create an alert.
        :param alert_json: takes a dictionary of alert information 
        :return: alert_id
        """
        # self.connect_dynamodb()

        alert_dict['alert_id'] = self._create_alert_id()
        response = self.dynamodb.put_item(
            Item=alert_dict
        )

        return response

    def destroy(self, alert_id):
        """
        Delete an alert.
        :param alert_id: Primary key of the alert to destroy.
        :return: status_code
        """
        response = self.dynamodb.delete_item(
            Key={
                'alert_id': alert_id
            }
        )

        return response

    def update(self, alert_id, alert_dict):
        """
        Update an alert record for a user.
        :param alert_id: Primary key of the alert to update.
        :param alert_dict: Complete information for replacement of the alert.
        :return: 
        """
        alert_dict['alert_id'] = alert_id
        response = self.dynamodb.put_item(
            Item=alert_dict
        )

        return response

    def find(self, user_id):
        """
        Search dynamodb for all non-expired alerts for a given user.
        :param user_id: The auth0 id of the user.
        :return: List of alerts
        """
        response = self.dynamodb.scan(
            FilterExpression=Attr('user_id').eq(user_id)
        )

        return response.get('Items')

    def _create_alert_id(self):
        """
        
        :return: random alertid
        """
        return binascii.b2a_hex(os.urandom(15))
