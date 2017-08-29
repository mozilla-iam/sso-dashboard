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

    def create(self, alert_dict):
        """
        Create an alert.
        :param alert_json: takes a dictionary of alert information 
        :return: alert_id
        """
        self.connect_dynamodb()

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
        self.connect_dynamodb()

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
                'user_id': self.userinfo.get('user_id'),
                'risk': 'MEDIUM',
                'summary': 'Your version of Firefox is older than the current stable release.',
                'description': 'Running the latest version of your browser is key to keeping your '
                               'computer secure and your private data private. Older browsers may '
                               'have known security vulnerabilities that attackers can exploit to '
                               'steal your data or load malware, which can put you and Mozilla at risk. ',
                'date': str(datetime.date.today()),
                'url': None,
                'url_title': None
            }
            self.alert.create(alert_dict=alert_dict)

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

        if u_version and u_version < self._firefox_info().get('LATEST_FIREFOX_VERSION'):
            return True
        else:
            return False





