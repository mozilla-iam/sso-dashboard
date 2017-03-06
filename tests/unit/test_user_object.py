from dotenv import load_dotenv, find_dotenv
from dashboard import app as sso_dashboard
from dashboard import user
import os
import json

SESSION = {
  "access_token": "1234567890",
  "id_token": {
    "amr": [
      "mfa"
    ],
    "aud": [
      "1234567890"
    ],
    "exp": 1234567890,
    "iat": 1234567890,
    "iss": "https://auth-dev.azillom.auth0.com/",
    "nonce": "1234567890",
    "sub": "ad|azillom-LDAP-Dev|testm"
  },
  "userinfo": {
    "clientID": "1234567890",
    "created_at": "2017-02-15T16:59:14.451Z",
    "dn": "mail=testm@azillom.com,o=com,dc=azillom",
    "email": "testm@azillom.com",
    "email_verified": 'true',
    "emails": [
      "testm@azillom.com"
    ],
    "family_name": "Krug",
    "given_name": "Andrew",
    "groups": [
        "testgroup1",
        "testgroup2"
    ],
    "identities": [
      {
        "connection": "azillom-LDAP-Dev",
        "isSocial": 'false',
        "provider": "ad",
        "user_id": "azillom-LDAP-Dev|testm"
      }
    ],
    "multifactor": [
      "duo"
    ],
    "name": "testm@azillom.com",
    "nickname": "Andrew Krug",
    "organizationUnits": "mail=testm@azillom.com,o=com,dc=azillom",
    "picture": "https://foo.bar.com/photo.png",
    "sub": "ad|azillom-LDAP-Dev|testm",
    "updated_at": "2017-03-06T18:16:04.040Z",
    "user_id": "ad|azillom-LDAP-Dev|testm"
  }
}

APP_LIST = dict(
    {   'apps': [
            {
                'application':
                    {
                        'name': 'authorized_test_app1',
                        'url': 'https://foo.bar.com',
                        'logo': '/static/img/auth0.jpg',
                        'authorized_users': [],
                        'authorized_groups': ['testgroup1'],
                        'display': False,
                        'op': 'okta'
                    }
            },
            {
                'application':
                    {
                        'name': 'unauthorized_test_ap1p',
                        'url': 'https://foo.bar.com',
                        'logo': '/static/img/auth0.jpg',
                        'authorized_users': [],
                        'authorized_groups': [],
                        'display': True,
                        'op': 'okta'
                    }
            },
            {
                'application':
                    {
                        'name': 'authorized_test_app2',
                        'url': 'https://foo.bar.com',
                        'logo': '/static/img/auth0.jpg',
                        'authorized_users': [],
                        'authorized_groups': ['testgroup2'],
                        'display': True,
                        'op': 'okta'
                    }
            },
            {
                'application':
                    {
                        'name': 'user_authorized_app',
                        'url': 'https://foo.bar.com',
                        'logo': '/static/img/auth0.jpg',
                        'authorized_users': ['testm@azillom.com'],
                        'authorized_groups': [],
                        'display': True,
                        'op': 'okta'
                    }
            },
        ]
    }
)

def test_object_instantiation():
    u = user.User(SESSION)

def test_profile_picture():
    u = user.User(SESSION)
    assert u.profile_picture() is not None
    assert u.profile_picture() == "https://foo.bar.com/photo.png"

def test_first_name():
    u = user.User(SESSION)
    assert u.first_name() is not None
    assert u.first_name() == "Andrew"

def test_last_name():
    u = user.User(SESSION)
    assert u.last_name() is not None
    assert u.last_name() == "Krug"

def test_group_membership():
    u = user.User(SESSION)
    assert u.group_membership() is not None
    assert u.group_membership() == [ "testgroup1", "testgroup2" ]

def test_user_apps():
    u = user.User(SESSION)
    authorized_apps = u.apps(APP_LIST)
    assert authorized_apps is not None
    assert len(authorized_apps['apps']) == 2
