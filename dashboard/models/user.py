"""User class that governs maniuplation of session['userdata']"""
import logging
import time
from faker import Faker

from . import alert

fake = Faker()
logger = logging.getLogger(__name__)


class User(object):
    def __init__(self, session, app_config):
        """Constructor takes user session."""
        self.id_token = session.get('id_token', None)
        self.app_config = app_config
        self.userinfo = session.get('userinfo')
        self.idvault_info = session.get('idvault_userinfo')

    def email(self):
        try:
            email = self.userinfo.get('email')
        except Exception as e:
            logger.error(
                'The email attribute does no exists falling back to OIDC Conformant: {}.'.format(e)
            )
            email = self.userinfo.get('https://sso.mozilla.com/claim/emails')[0]['emails']
        return email

    def apps(self, app_list):
        """Return a list of the apps a user is allowed to see in dashboard."""
        authorized_apps = {
            'apps': []
        }

        for app in app_list['apps']:
            if self._is_valid_yaml(app):
                if self._is_authorized(app):
                    authorized_apps['apps'].append(app)

        return authorized_apps.get('apps', [])

    @property
    def avatar(self):
        if self.idvault_info:
            picture_url = self.idvault_info.get('picture')
        else:
            picture_url = None

        return picture_url

    def group_membership(self):
        """Return list of group membership if user is asserted from ldap."""
        if self.userinfo.get('https://sso.mozilla.com/claim/groups', []):
            group_count = len(self.userinfo.get('https://sso.mozilla.com/claim/groups', []))

        if self.userinfo.get('groups'):
            group_count = len(self.userinfo.get('groups', []))

        if 'https://sso.mozilla.com/claim/groups' in self.userinfo.keys() and group_count > 0:
                return self.userinfo['https://sso.mozilla.com/claim/groups']

        if 'groups' in self.userinfo.keys() and group_count > 0:
                return self.userinfo['groups']
        else:
            # This could mean a user is authing with non-ldap
            return []

    @property
    def first_name(self):
        """Return user first_name."""
        try:
            return self.idvault_userinfo.get('firstName')
        except KeyError:
            return self.userinfo.get('user_id')

    @property
    def last_name(self):
        """Return user last_name."""
        try:
            return self.idvault_info.get('lastName')
        except KeyError:
            return None

    def user_identifiers(self):
        """Construct a list of potential user identifiers to match on."""
        return [self.email(), self.userinfo['sub']]

    @property
    def alerts(self):
        alerts = alert.Alert().find(user_id=self.userinfo['sub'])
        return alerts

    def take_alert_action(self, alert_id, alert_action, helpfulness=None):
        a = alert.Alert()
        alert_dict = a.find_by_id(alert_id)

        alert_dict['last_update'] = int(time.time())

        if alert_action == 'acknowledge':
            logger.info('An alert was acked for {uid}.'.format(uid=self.userinfo['sub']))
            alert_dict['state'] = alert_action
            res = a.update(alert_id=alert_id, alert_dict=alert_dict)
        elif alert_action == 'escalate':
            logger.info('An alert was escalated for {uid}.'.format(uid=self.userinfo['sub']))
            alert_dict['state'] = alert_action
            res = a.update(alert_id=alert_id, alert_dict=alert_dict)
        elif alert_action == 'indicate-helpfulness':
            logger.info('Alert helpfulness was set for {uid}.'.format(uid=self.userinfo['sub']))
            alert_dict['helpfulness'] = helpfulness
            res = a.update(alert_id=alert_id, alert_dict=alert_dict)
        else:
            res = {'ResponseMetadata': {'HTTPStatusCode': 200}}

        m = alert.Feedback(
            alert_dict=alert_dict,
            alert_action=alert_action
        )

        m.send()
        return res

    def _is_authorized(self, app):
        if app['application']['display'] == 'False':
            return False
        elif not app['application']['display']:
            return False
        elif 'everyone' in app['application']['authorized_groups']:
            return True
        elif set(app['application']['authorized_groups']) & set(self.group_membership()):
            return True
        elif set(app['application']['authorized_users']) & set(self.user_identifiers()):
            return True
        else:
            return False

    def _is_valid_yaml(self, app):
        """If an app doesn't have the required fields skip it."""
        try:
            app['application']['display']
            app['application']['authorized_groups']
            app['application']['authorized_users']
            return True
        except Exception:
            return False


class FakeUser(object):
    def __init__(self, app_config):
        """Constructor takes user session."""
        self.app_config = app_config

    def email(self):
        return fake.email()

    def apps(self, app_list):
        authorized_apps = {
            'apps': []
        }

        for app in app_list['apps']:
            if self._is_valid_yaml(app):
                if self._is_authorized(app):
                    authorized_apps['apps'].append(app)
        return authorized_apps.get('apps', [])

    @property
    def avatar(self):
        return self.profile['avatar']

    def group_membership(self):
            return []

    @property
    def first_name(self):
        return fake.first_name_male()

    @property
    def last_name(self):
        return fake.last_name()

    @property
    def alerts(self):
        return {
            'visible_alerts': [
                {
                    'alert_code': '416c65727447656f6d6f64656c',
                    'alert_id': '4053bd6a9e9a6bb03095f479c0fab2',
                    'date': '2017-10-27',
                    'description': 'This alert is created based on geo ip information about the last login of a user.',
                    'duplicate': True,
                    'risk': 'medium',
                    'summary': 'Did you recently login from Unknown, {}?'.format(fake.country()),
                    'url': 'https://mana.mozilla.org/wiki/display/SECURITY/Alert%3A+Change+in+Country',
                    'url_title': 'Get Help',
                    'user_id': 'ad|Mozilla-LDAP|fakeuser'
                },
                {
                    'alert_code': '63f675d8896f4fb2b3caa204c8c2761e',
                    'user_id': 'ad|Mozilla-LDAP|fakeuser',
                    'risk': 'medium',
                    'summary': 'Your version of Firefox is older than the current stable release.',
                    'description': 'Running the latest version of your browser is key to keeping your '
                                   'computer secure and your private data private. Older browsers may '
                                   'have known security vulnerabilities that attackers can exploit to '
                                   'steal your data or load malware, which can put you and Mozilla at risk. ',
                    'date': '2017-10-27',
                    'url': 'https://www.mozilla.org/firefox/',
                    'url_title': 'Download',
                    'duplicate': False
                }
            ]
        }

    def _is_valid_yaml(self, app):
        return True

    def _is_authorized(self, app):
        if 'everyone' in app['application']['authorized_groups']:
            return True
        else:
            return False
