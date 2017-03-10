import hashlib


"""User class that governs maniuplation of session['userdata']"""

class User(object):
    def __init__(self, session):
        """Constructor takes user session."""
        self.userinfo = session['userinfo']

    def userhash(self):
        """Represent user e-mail as hex hash."""
        m = hashlib.md5()
        m.update(self.userinfo['email'])
        return m.hexdigest()

    def profile_picture(self):
        """Return url of profile picture of returns robohash."""
        if self.userinfo['picture']:
            return self.userinfo['picture']
        else:
            return None

    def group_membership(self):
        """Return list of group membership if user is asserted from ldap."""
        if len(self.userinfo['groups']) > 0:
            return self.userinfo['groups']
        else:
            return None

    def first_name(self):
        """Return user first_name."""
        if self.userinfo['given_name']:
            return self.userinfo['given_name']
        else:
            return None

    def last_name(self):
        """Return user last_name."""
        if self.userinfo['family_name']:
            return self.userinfo['family_name']
        else:
            return None

    def user_identifiers(self):
        """Construct a list of potential user identifiers to match on."""
        return [self.userinfo['email'], self.userinfo['user_id']]

    def __is_authorized(self, app):
        if app['application']['display'] == 'False':
            return False
        elif app['application']['display'] == False:
            return False
        elif 'everyone' in app['application']['authorized_groups']:
            return True
        elif set(app['application']['authorized_groups']) & set(self.group_membership()):
            return True
        elif set(app['application']['authorized_users']) & set(self.user_identifiers()):
            return True
        else:
            return False

    def apps(self, app_list):
        """Return a list of the apps a user is allowed to see in dashboard."""
        authorized_apps = {
            'apps': []
        }

        for app in app_list['apps']:
            if self.__is_authorized(app):
                authorized_apps['apps'].append(app)
        return authorized_apps
