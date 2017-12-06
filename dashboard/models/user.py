"""User class that governs maniuplation of session['userdata']"""
import logging
import requests

from . import alert


logger = logging.getLogger(__name__)


class Mozillians(object):
    """Operations governing Mozillians."""
    def __init__(self, app_config=None):
        self.app_config = app_config

    @property
    def api_key(self):
        if self.app_config is not None:
            return self.app_config.MOZILLIANS_API_KEY

    @property
    def api_url(self):
        if self.app_config is not None:
            return self.app_config.MOZILLIANS_API_URL

    def _get_user_info(self, email):
        response = self._get_user(email)
        if not response:
            return None

        try:
            results = response.get('results', -1)
            user_url = results[0].get('_url')
            user_info = requests.get(user_url, headers=self.headers, timeout=5)
        except:
            return None

        if user_info.status_code is not 200:
            return None

        try:
            info = user_info.json()
        except:
            return None

        return info

    def _get_user(self, email):
        self.headers = {'X-API-KEY': self.api_key}
        params = {'email': email}

        if not self.api_url:
            return None

        try:
            mozillians_response = requests.get(self.api_url, headers=self.headers,
                                               params=params, timeout=5)
        except:
            return None

        if mozillians_response.status_code is not 200:
            return None

        try:
            response = mozillians_response.json()
        except:
            return None

        return response

    def user_detail(self, email, field='photo'):
        response = self._get_user_info(email)

        ctx = {
            'avatar': None,
            'full_name': None
        }

        if response:
            if response['photo']['privacy'] == 'Public':
                ctx['avatar'] = response['photo']['value']
            if response['full_name']['privacy'] == 'Public':
                ctx['full_name'] = response['full_name']['value']

        return ctx


class User(object):
    def __init__(self, session, app_config):
        """Constructor takes user session."""
        self.id_token = session.get('id_token', None)
        self.app_config = app_config
        m = Mozillians(self.app_config)
        self.userinfo = session.get('userinfo')
        self.idvault_info = session.get('idvault_userinfo')
        self.profile = m.user_detail(self.email())

    def email(self):
        try:
            email = self.userinfo.get('email')
        except Exception as e:
            logger.error('The email attribute does no exists falling back to OIDC Conformant.')
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
        return self.profile['avatar']

    def group_membership(self):
        """Return list of group membership if user is asserted from ldap."""
        if 'https://sso.mozilla.com/claim/groups' in self.userinfo.keys() \
            and len(self.userinfo['https://sso.mozilla.com/claim/groups']) > 0:
            return self.userinfo['https://sso.mozilla.com/claim/groups']
        else:
            # This could mean a user is authing with non-ldap
            return []

    @property
    def first_name(self):
        """Return user first_name."""
        try:
            return self.userinfo['given_name']
        except KeyError:
            return self.profile['full_name']

    @property
    def last_name(self):
        """Return user last_name."""
        try:
            return self.userinfo['family_name']
        except KeyError:
            return None

    def user_identifiers(self):
        """Construct a list of potential user identifiers to match on."""
        return [self.email(), self.userinfo['sub']]

    @property
    def alerts(self):
        alerts = alert.Alert().find(user_id=self.userinfo['sub'])
        return alerts

    def acknowledge_alert(self, alert_id):
        a = alert.Alert()

        """ Future home of the code that pushes an alert back to MozDef """
        logger.info('An alert was acked for {uid}.'.format(uid=self.userinfo['sub']))
        return a.destroy(alert_id=alert_id, user_id=self.userinfo['sub'])

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

