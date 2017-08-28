"""Operations governing the creation and destruction of user facing alerts."""
import binascii
import boto3
import os


class AlertDelegate(object):
    """Primary object containing alert functions."""
    def __init__(self):
        self.alert_table_name = 'sso-dashboard-alerts'
        self.dynamodb = None


    def create(self, alert_dict):
        """
        Create an alert.
        :param alert_json: takes a dictionary of alert information 
        :return: alert_id
        """
        pass

    def destroy(self, alert_id):
        """
        Delete an alert.
        :param alert_id: Primary key of the alert to destroy.
        :return: status_code
        """
        pass

    def update(self, alert_id, alert_dict):
        """
        Update an alert record for a user.
        :param alert_id: Primary key of the alert to update.
        :param alert_dict: Complete information for replacement of the alert.
        :return: 
        """
        pass

    def find(self, user_id):
        """
        Search dynamodb for all non-expired alerts for a given user.
        :param user_id: The auth0 id of the user.
        :return: List of alerts
        """

    def _connect_dynamo(self):
        """
        Sets the dyanmodb_table object on the alert object.
        :return: None
        """

    def _create_alert_id(self):
        """
        
        :return: random alertid
        """
        return binascii.b2a_hex(os.urandom(15))

class Alert(AlertDelegate):
    pass

class NullAlert(AlertDelegate):
    pass