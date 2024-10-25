import json
from pathlib import Path
import os

import dashboard.models.user as user


class TestUser:
    def setup_method(self):
        self.fixture_file = Path(__file__).parent.parent / "data" / "userinfo.json"
        try:
            with open(self.fixture_file) as f:
                self.session_fixture = json.load(f)

            self.good_apps_list = {"apps": []}

            self.u = user.User(session=self.session_fixture, app_config=None)
            self.u.api_token = "foo"
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            self.u = None
            raise RuntimeError(f"Failed to set up TestUser: {str(e)}")

    def test_object_init(self):
        assert self.u is not None

    def test_avatar(self):
        avatar = self.u.avatar
        assert avatar is None

    def test_parsing_groups(self):
        groups = self.u.group_membership()
        assert len(groups) > 0

    def test_user_name(self):
        f_name = self.u.first_name
        l_name = self.u.last_name

        assert f_name == ""
        assert l_name == ""

    def test_user_identifiers(self):
        assert len(self.u.user_identifiers()) == 2

    def test_apps(self):
        apps = self.u.apps(self.good_apps_list)
        assert apps == []
