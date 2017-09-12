"""Operations governing the creation and destruction of user facing alerts."""
import binascii
import boto3
import datetime
import os
import requests


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

    def find_or_create_by(self, alert_dict, user_id):
        """

        :param alert_dict: takes a dictionary of alert information
        :param user_id: the session info user_id
        :return: dynamodb response or none
        """

        # Search for the user alerts
        current_alerts = self.find(user_id)

        # If the alert is duplicate false do not create another instance of it.
        for alert in current_alerts:
            if alert.get('alert_code') == alert_dict.get('alert_code') and alert_dict.get('duplicate') is False:
                return None
            else:
                continue

        # Else create another alert.
        return self.create(alert_dict)

    def create(self, alert_dict):
        """
        Create an alert.
        :param alert_json: takes a dictionary of alert information
        :return: dynamodb response
        """
        self.connect_dynamodb()

        alert_dict['alert_id'] = self._create_alert_id()
        response = self.dynamodb.put_item(
            Item=alert_dict
        )

        return response

    def destroy(self, alert_id, user_id):
        """
        Delete an alert.
        :param alert_id: Primary key of the alert to destroy.
        :return: status_code
        """
        self.connect_dynamodb()

        response = self.dynamodb.delete_item(
            Key={
                'alert_id': alert_id,
                'user_id': user_id
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
        self.connect_dynamodb()

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
        self.connect_dynamodb()

        response = self.dynamodb.scan(
            FilterExpression=Attr('user_id').eq(user_id)
        )

        return response.get('Items')

    def _create_alert_id(self):
        """

        :return: random alertid
        """
        return binascii.b2a_hex(os.urandom(15))


class Rules(object):
    def __init__(self, userinfo, request):
        """

        :param userinfo: Flask session info about the user so that Rules can make decisions about the user.
        :param browser_header: The browser header as seen by Flask.
        """
        self.userinfo = userinfo
        self.request = request
        self.alert = Alert()

    def run(self):
        self.alert_firefox_out_of_date()

    def alert_firefox_out_of_date(self):
        if self._firefox_out_of_date():
            alert_dict = {
                'alert_code': '63f675d8896f4fb2b3caa204c8c2761e',
                'user_id': self.userinfo.get('user_id'),
                'risk': 'medium',
                'summary': 'Your version of Firefox is older than the current stable release.',
                'description': 'Running the latest version of your browser is key to keeping your '
                               'computer secure and your private data private. Older browsers may '
                               'have known security vulnerabilities that attackers can exploit to '
                               'steal your data or load malware, which can put you and Mozilla at risk. ',
                'date': str(datetime.date.today()),
                'url': 'https://www.mozilla.org/firefox/',
                'url_title': 'Download',
                'duplicate': False
            }
            self.alert.find_or_create_by(alert_dict=alert_dict, user_id=self.userinfo.get('user_id'))

    def _firefox_info(self):
        release_json = requests.get('https://product-details.mozilla.org/1.0/firefox_versions.json')
        return release_json.json()

    def _user_firefox_version(self):
        agent = self.request.headers.get('User-Agent')
        print(agent)
        if agent.find('Firefox') != -1:
            version = agent.split('Firefox/')[1]
        else:
            version = None
        return version

    def _firefox_out_of_date(self):
        u_version = self._user_firefox_version()
        current_version = self._firefox_info().get('LATEST_FIREFOX_VERSION', '').split('.')[0]

        if u_version and u_version < current_version:
            return True
        return False
