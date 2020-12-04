import http.client
import json
# Commenting out in since CISv1 is no longer up and running
# todo: this will need to get modified to reach out to person api v2
# import urllib

from dashboard import config


class API(object):
    """Retrieve data from person api as needed.  Will eventually replace Mozillians API"""

    def __init__(self):
        """
        :param session: the flask session to update with userinfo
        """
        self.config = config.OIDCConfig()
        self.person_api_url = self._get_url()

    def get_bearer(self):
        conn = http.client.HTTPSConnection(self.config.OIDC_DOMAIN)
        payload = json.dumps(
            {
                "client_id": self.config.OIDC_CLIENT_ID,
                "client_secret": self.config.OIDC_CLIENT_SECRET,
                "audience": "https://{}".format(self._get_url()),
                "grant_type": "client_credentials",
            }
        )

        headers = {"content-type": "application/json"}

        conn.request("POST", "/oauth/token", payload, headers)
        res = conn.getresponse()
        data = res.read()
        return json.loads(data.decode("utf-8"))

    def get_userinfo(self, auth_zero_id):
        return
        # # Commenting out in since CISv1 is no longer up and running
        # # todo: this will need to get modified to reach out to person api v2
        # user_id = urllib.parse.quote(auth_zero_id)
        # conn = http.client.HTTPSConnection("{}".format(self.person_api_url))
        # token = "Bearer {}".format(self.get_bearer().get("access_token"))

        # headers = {"authorization": token}

        # conn.request("GET", "/v1/profile/{}".format(user_id), headers=headers)

        # res = conn.getresponse()
        # data = res.read()
        # return json.loads(json.loads(data.decode("utf-8")).get("body"))

    def _get_url(self):
        if self.config.OIDC_DOMAIN == "auth.mozilla.auth0.com":
            return "person-api.sso.mozilla.com"
        else:
            return "person-api.sso.allizom.org"
