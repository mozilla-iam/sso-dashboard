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

    def _has_avatar(self, email):
        if self.api_url is not None:
            try:
                mozillians_response = requests.get(self.api_url, headers=self.headers,
                                                   params=self.params, timeout=5)
                if mozillians_response.status_code is not 200:
                    return None
                response = mozillians_response.json()
                return response
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                return None
        else:
            return None

    def _is_only_one_avatar(self, response):
        # Check if only single resource gets returned and it's valid
        avatars = response.get('results', -1)

        if len(avatars) == 1:
            self.user_url = avatars[0].get('_url')
            return True
        else:
            self.user_url = None
            return False

    def _get_image_url(self):
        # Finally fetch user public avatar and make sure  we have a valid fallback
        try:
            response = requests.get(self.user_url, headers=self.headers, timeout=5).json()
            if response['photo']['privacy'] == 'Public':
                return response['photo']['value']
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            return None

    def avatar(self, email):
        self.headers = {'X-API-KEY': self.api_key}
        self.params = {'email': email}

        response = self._has_avatar(email)

        if response:
            self._is_only_one_avatar(response)
            avatar_url = self._get_image_url()
        else:
            avatar_url = None

        return avatar_url


class User(object):
    def __init__(self, session, app_config):
        """Constructor takes user session."""
        self.userinfo = session.get('userinfo', None)
        self.app_config = app_config

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
        m = Mozillians(self.app_config)
        return m.avatar(self.userinfo.get('email'))

    def group_membership(self):
        """Return list of group membership if user is asserted from ldap."""
        if 'groups' in self.userinfo.keys() and len(self.userinfo['groups']) > 0:
            return self.userinfo['groups']
        else:
            # This could mean a user is authing with non-ldap
            return []

    @property
    def first_name(self):
        """Return user first_name."""
        try:
            return self.userinfo['given_name']
        except KeyError:
            return None

    @property
    def last_name(self):
        """Return user last_name."""
        try:
            return self.userinfo['family_name']
        except KeyError:
            return None

    def user_identifiers(self):
        """Construct a list of potential user identifiers to match on."""
        return [self.userinfo['email'], self.userinfo['user_id']]

    @property
    def alerts(self):
        alerts = alert.Alert().find(user_id=self.userinfo['user_id'])
        return alerts

    def acknowledge_alert(self, alert_id):
        a = alert.Alert()

        """ Future home of the code that pushes an alert back to MozDef """
        logger.info('An alert was acked for {uid}.'.format(uid=self.userinfo['user_id']))
        return a.destroy(alert_id=alert_id, user_id=self.userinfo['user_id'])

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
