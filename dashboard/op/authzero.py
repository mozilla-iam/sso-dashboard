"""Class for handling the auth0 specific interactions."""


from auth0.v2.management import Auth0
import http.client
import json
import jwt

class TokenOperations(object):
    def __init__(self, jwt):
        self.jwt = jwt

    def decode(self, secret):
        #decoded = jwt.decode(self.jwt, verify=False)
        ###TBD figure out what's up with RS256
        try:
            decoded = jwt.decode(
                self.jwt,
                secret,
                audience='https://manage-dev.mozilla.auth0.com/api/custom',
                algorithms=['HS256']
            )
            return decoded
        except jwt.ExpiredSignatureError:
            raise


class AccessToken(object):
    def __init__(self, config):
        self.config = config
        self.headers = {'content-type': "application/json"}

    def http_client(self):
        conn = http.client.HTTPSConnection(self.config.OIDC_DOMAIN)
        return conn

    def payload(self):
        payload = {
            "client_id": self.config.OIDC_CLIENT_ID,
            "client_secret": self.config.OIDC_CLIENT_SECRET,
            "audience": "https://manage-dev.mozilla.auth0.com/api/custom",
            "grant_type": "client_credentials",
            "config": {
                "require_jti": "true"
            }
        }

        return json.dumps(payload)

    def get_token(self):
        conn = self.http_client()
        request = conn.request(
            "POST", "/oauth/token", self.payload(), self.headers
        )

        res = conn.getresponse()
        data = res.read()
        data = data.decode("utf-8")
        return json.loads(data)

    def blacklist_token(self, access_token):
        """TBD after doing JTI stuff."""
        t = TokenOperations(self.get_token())

        """payload = {
          "aud": "https://{domain}/api/v2/".format(
              domain=self.config.OIDC_DOMAIN
          ),
          "jti": ""
        }"""
        pass


class Managment(object):
    def __init__(self, token, domain):
        self.domain = 'auth-dev.mozilla.auth0.com'
        self.token = token
        self.client = None

    def get_client(self):
        self.client = Auth0(self.domain, self.token)
        return self.client
