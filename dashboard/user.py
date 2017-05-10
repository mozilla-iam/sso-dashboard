import hashlib
import os
import requests

"""User class that governs maniuplation of session['userdata']"""


class User(object):
    def __init__(self, session):
        """Constructor takes user session."""
        self.userinfo = session['userinfo']
        
    def avatar(self):
        """Return url of user avatar from mozillians.org"""
        self.api_url = os.getenv('MOZILLIANS_API_URL', None)
        self.api_token = os.getenv('MOZILLIANS_API_KEY', None)

        headers = {'X-API-KEY': self.api_token}
        params = {'email': self.userinfo['email']}

        try:
            mozillians_response = requests.get(self.api_url, headers=headers,
                                               params=params, timeout=5)
            response = mozillians_response.json()

            if mozillians_response.status_code is not 200:
                return None
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            return None

        # Check if only single resource gets returned and it's valid
        if response['count'] == 0 or response['count'] > 1:
            return None
        try:
            user_url = response['results'][0]['_url']
        except:
            return None

        # Finally fetch user public avatar and make sure  we have a valid fallback
        try:
            response = requests.get(user_url, headers=headers, timeout=5).json()
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            return None
        if response['photo']['privacy'] == 'Public':
            return response['photo']['value']
        else:
            return None

    def group_membership(self):
        """Return list of group membership if user is asserted from ldap."""
        if 'groups' in self.userinfo.keys() and len(self.userinfo['groups']) > 0:
            return self.userinfo['groups']
        else:
            # This could mean a user is authing with non-ldap
            return []

    def first_name(self):
        """Return user first_name."""
        try:
            return self.userinfo['given_name']
        except KeyError:
            return None

    def last_name(self):
        """Return user last_name."""
        try:
            return self.userinfo['family_name']
        except KeyError:
            return None

    def user_identifiers(self):
        """Construct a list of potential user identifiers to match on."""
        return [self.userinfo['email'], self.userinfo['user_id']]

    def __is_authorized(self, app):
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

    def __is_valid_yaml(self, app):
        """If an app doesn't have the required fields skip it."""
        try:
            app['application']['display']
            app['application']['authorized_groups']
            app['application']['authorized_users']
            return True
        except Exception:
            return False

    def apps(self, app_list):
        """Return a list of the apps a user is allowed to see in dashboard."""
        authorized_apps = {
            'apps': []
        }

        for app in app_list['apps']:
            if self.__is_valid_yaml(app):
                if self.__is_authorized(app):
                    authorized_apps['apps'].append(app)
        return authorized_apps
