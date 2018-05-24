"""Operations governing the creation and destruction of user facing alerts."""
import binascii
import boto3
import datetime
import json
import logging
import os
import requests


from boto3.dynamodb.conditions import Attr
from faker import Faker


fake = Faker()
logger = logging.getLogger(__name__)


class Feedback(object):
    """Send user data back to MozDef or other subscribers via an SNS Topic"""
    def __init__(self, alert_dict, alert_action):
        self.alert_dict = alert_dict
        self.alert_action = alert_action
        self.ssm = None
        self.sns = None
        self.sns_topic_arn = self.get_sns_arn()

    def connect_sns(self):
        if self.sns is None:
            self.sns = boto3.client('sns', region_name='us-west-2')

    def connect_ssm(self):
        if self.ssm is None:
            self.ssm = boto3.client('ssm', region_name='us-west-2')

    def get_sns_arn(self):
        self.connect_ssm()

        response = self.ssm.get_parameter(
            Name='sso-dashboard-alerts-sns',
            WithDecryption=False
        )

        return response.get('Parameter').get('Value')

    def _construct_alert(self):
        message = {
            'category': 'user_feedback',
            'details': {
                'action': self.alert_action,  # (escalate|acknowledge|false-positive)
                'alert_information': self.alert_dict
            }
        }

        return message

    def send(self):
        """Send the event to the SNS Topic."""
        self.connect_sns()
        message = self._construct_alert()
        response = self.sns.publish(
            TopicArn=self.sns_topic_arn,
            Message=json.dumps(message),
            Subject='sso-dashboard-user-feedback'
        )
        return response


class Alert(object):
    """Primary object containing alert functions."""
    def __init__(self):
        self.alert_table_name = 'sso-dashboard-alert'
        self.dynamodb = None

    def has_actions(self, alert_dict):
        """Let's the view know if it should render actions for the alert."""

        # Whitelist the firefox out of date alert.  It should not get buttons.
        if self.alert_dict.get('alert_code') is not '63f675d8896f4fb2b3caa204c8c2761e':
            return True
        else:
            return False

    def has_escalation(self, alert_dict):
        """Let's the view know if it should render actions for the alert."""

        # Whitelist the firefox out of date alert.  It should not get buttons.
        if self.alert_dict.get('alert_code') is not '63f675d8896f4fb2b3caa204c8c2761e':
            return True
        else:
            return False

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
        for alert in current_alerts.get('visible_alerts'):
            try:
                if alert.get('alert_code') == alert_dict.get('alert_code') and alert_dict.get('duplicate') is False:
                    return None
                else:
                    continue
            except AttributeError as e:
                logger.error('Bad data in alerts table for user: {}, exception was {}'.format(user_id, e))

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
        response = None
        try:
            self.connect_dynamodb()

            response = self.dynamodb.scan(
                FilterExpression=Attr('user_id').eq(user_id)
            )

            alerts = response.get('Items', [])

            if response:
                while 'LastEvaluatedKey' in response:
                    response = self.dynamodb.scan(
                        FilterExpression=Attr('user_id').eq(user_id),
                        ExclusiveStartKey=response['LastEvaluatedKey']
                    )
                    alerts.extend(response['Items'])
        except Exception as e:
            logger.error('Could not load alerts for user: {} due to: {}.'.format(user_id, e))
            alerts = []

        inactive_alerts = []
        visible_alerts = []
        ranked_alerts = []
        escalations = []

        for alert in alerts:
            if alert.get('state', '') == 'acknowledge':
                inactive_alerts.append(alert)
            elif alert.get('helpfulness', '') != '':
                ranked_alerts.append(alert)
                visible_alerts.append(alert)
            elif alert.get('state', '') == 'escalate':
                escalations.append(alert)
                visible_alerts.append(alert)
            else:
                visible_alerts.append(alert)

        return {
            'visible_alerts': visible_alerts,
            'ranked_alerts': ranked_alerts,
            'escalations': escalations,
            'inactive_alerts': inactive_alerts
        }

    def to_summary(self, alert_dict):
        """
        Takes list of lists of alerts as formatted in self.find()
        Return statuses for consumption in NLX
        """
        high_count = 0
        maximum_count = 0
        medium_count = 0
        low_count = 0

        for alert in alert_dict.get('visible_alerts', []):
            if alert.get('risk') == 'high':
                high_count = high_count + 1
            if alert.get('risk') == 'maximum':
                maximum_count = maximum_count + 1
            if alert.get('risk') == 'medium':
                medium_count = medium_count + 1
            if alert.get('risk') == 'low':
                low_count = low_count + 1

        return {
            'alerts':
                {'maximum': maximum_count, 'high': high_count, 'medium': medium_count, 'low': low_count}
        }

    def find_by_id(self, alert_id):
        """
        Search dynamodb for all non-expired alerts for a given user.
        :param alert_id: The guid of the alert.
        :return: List of alerts
        """
        self.connect_dynamodb()

        response = self.dynamodb.scan(
            FilterExpression=Attr('alert_id').eq(alert_id)
        )

        return response.get('Items')[0]

    def _create_alert_id(self):
        """

        :return: random alertid
        """
        return binascii.b2a_hex(os.urandom(15)).decode()


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
        if agent.find('Firefox') != -1:
            version = agent.split('Firefox/')[1]
        else:
            version = None
        return version

    def _version_to_dictionary(self, version_number):
        version_number_list = version_number.split('.')
        version_dict = {
            'major_version': version_number_list[0],
            'minor_version': version_number_list[1]
        }

        if len(version_number_list) == 3:
            version_dict['dot_version'] = version_number_list[2]
        else:
            version_dict['dot_version'] = None

        return version_dict

    def _firefox_out_of_date(self):
        if self._user_firefox_version() is not None:
            u_version = self._version_to_dictionary(self._user_firefox_version())
            f_version = self._version_to_dictionary(self._firefox_info().get('LATEST_FIREFOX_VERSION'))

            if u_version.get('major_version') < f_version.get('major_version'):
                return True
            elif u_version.get('major_version') == f_version.get('major_version'):
                if u_version.get('minor_version') < f_version.get('minor_version'):
                    return True
                elif u_version.get('minor_version') == f_version.get('minor_version') \
                        and u_version.get('dot_version') is not None:
                    if u_version.get('dot_version') < f_version.get('dot_version'):
                        return True
                else:
                    return False
            else:
                return False


class FakeAlert(object):
    """Class only fires in development mode.  Adds alerts to a given user for testing only."""
    def __init__(self, user_id):
        self.user_id = user_id
        self.alert = Alert()

    def create_fake_alerts(self):
        self._create_fake_browser_alert()
        self._create_fake_geolocation_alert()

    def _create_fake_browser_alert(self):
        alert_dict = {
            'alert_code': '63f675d8896f4fb2b3caa204c8c2761e',
            'user_id': self.user_id,
            'risk': 'medium',
            'summary': 'Your version of Firefox is older than the current stable release.',
            'description': 'Running the latest version of your browser is key to keeping your '
                           'computer secure and your private data private. Older browsers may '
                           'have known security vulnerabilities that attackers can exploit to '
                           'steal your data or load malware, which can put you and Mozilla at risk. ',
            'date': str(fake.date(pattern="%Y-%m-%d", end_datetime=None)),
            'url': 'https://www.mozilla.org/firefox/',
            'url_title': 'Download',
            'duplicate': False
        }
        self.alert.find_or_create_by(alert_dict=alert_dict, user_id=self.user_id)

    def _create_fake_geolocation_alert(self):
        fake_state = fake.state()
        fake_country = fake.country()
        fake_email = fake.email()
        fake_ip = fake.ipv4()

        original_alert_dict = {
            'category': 'geomodel',
            'details': {
                'category': 'NEWCOUNTRY',
                'locality_details': {
                    'city': fake_state,
                    'country': fake_country
                },
                'principal': fake_email,
                'source_ip': fake_ip
            },
            'severity': 'NOTICE',
            'summary': '{} NEWCOUNTRY {}, {} access from {}'.format(
                fake_email,
                fake_state,
                fake_country,
                fake_ip
            ),
            'tags': ['geomodel'],
            'url': 'https://www.mozilla.org/alert',
            'utctimestamp': '{}+00:00'.format(fake.iso8601())
        }

        alert_dict = {
            'alert_code': '416c65727447656f6d6f64656c',
            'user_id': self.user_id,
            'risk': 'high',
            'summary': 'Did you recently login from {}, {} ({})?'.format(
                fake_state,
                fake_country,
                fake_ip
            ),
            'alert_str_json': json.dumps(original_alert_dict),
            'description': 'This alert is created based on geo ip information about the last login of a user.',
            'date': str(fake.date(pattern="%Y-%m-%d", end_datetime=None)),
            'url': 'https://www.mozilla.org',
            'url_title': 'Get Help',
            'duplicate': False
        }
        self.alert.find_or_create_by(alert_dict=alert_dict, user_id=self.user_id)
