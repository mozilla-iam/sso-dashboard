"""User class that governs maniuplation of session['userdata']"""

import logging
import time
from faker import Faker

fake = Faker()
logger = logging.getLogger()


class User(object):
    def __init__(self, session, app_config):
        """Constructor takes user session."""
        self.id_token = session.get("id_token", None)
        self.app_config = app_config
        self.userinfo = session.get("userinfo")

    def email(self):
        try:
            email = self.userinfo.get("email")
        except Exception:
            logger.exception("The email attribute does no exists falling back to OIDC Conformant.")
            email = self.userinfo.get("https://sso.mozilla.com/claim/emails")[0]["emails"]
        return email

    def apps(self, app_list):
        """Return a list of the apps a user is allowed to see in dashboard."""
        authorized_apps = {"apps": []}

        for app in app_list["apps"]:
            if self._is_valid_yaml(app):
                if self._is_authorized(app):
                    authorized_apps["apps"].append(app)

        return authorized_apps.get("apps", [])

    @property
    def avatar(self):
        return None

    def group_membership(self):
        """Return list of group membership if user is asserted from ldap."""
        if self.userinfo.get("https://sso.mozilla.com/claim/groups", []) != []:
            group_count = len(self.userinfo.get("https://sso.mozilla.com/claim/groups", []))
        else:
            if self.userinfo.get("groups"):
                group_count = len(self.userinfo.get("groups", []))
            else:
                group_count = 0

        if "https://sso.mozilla.com/claim/groups" in self.userinfo.keys() and group_count > 0:
            return self.userinfo["https://sso.mozilla.com/claim/groups"]

        if "groups" in self.userinfo.keys() and group_count > 0:
            return self.userinfo["groups"]
        else:
            # This could mean a user is authing with non-ldap
            return []

    @property
    def first_name(self):
        """Return user first_name."""
        return ""

    @property
    def last_name(self):
        """Return user last_name."""
        return ""

    def user_identifiers(self):
        """Construct a list of potential user identifiers to match on."""
        return [self.email(), self.userinfo["sub"]]

    def _is_authorized(self, app):
        if app["application"]["display"] == "False":
            return False
        elif not app["application"]["display"]:
            return False
        elif "everyone" in app["application"]["authorized_groups"]:
            return True
        elif set(app["application"]["authorized_groups"]) & set(self.group_membership()):
            return True
        elif set(app["application"]["authorized_users"]) & set(self.user_identifiers()):
            return True
        else:
            return False

    def _is_valid_yaml(self, app):
        """If an app doesn't have the required fields skip it."""
        try:
            app["application"]["display"]
            app["application"]["authorized_groups"]
            app["application"]["authorized_users"]
            return True
        except KeyError:
            return False


class FakeUser(object):
    def __init__(self, app_config):
        """Constructor takes user session."""
        self.app_config = app_config

    def email(self):
        return fake.email()

    def apps(self, app_list):
        authorized_apps = {"apps": []}

        for app in app_list["apps"]:
            if self._is_valid_yaml(app):
                if self._is_authorized(app):
                    authorized_apps["apps"].append(app)
        return authorized_apps.get("apps", [])

    @property
    def avatar(self):
        return self.profile["avatar"]

    def group_membership(self):
        return []

    @property
    def first_name(self):
        return fake.first_name_male()

    @property
    def last_name(self):
        return fake.last_name()

    def _is_valid_yaml(self, app):
        return True

    def _is_authorized(self, app):
        if "everyone" in app["application"]["authorized_groups"]:
            return True
        else:
            return False
