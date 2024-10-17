import logging
from flask import make_response
from flask import redirect
from flask import request

from dashboard.op import yaml_loader

logger = logging.getLogger()


class Router(object):
    def __init__(self, app, app_list):
        self.app = app
        self.url_list = yaml_loader.Application(app_list.apps_yml).vanity_urls()

    def setup(self):
        for url in self.url_list:
            for vanity_url in url.keys():
                try:
                    self.app.add_url_rule(vanity_url, vanity_url, self.redirect_url)
                    self.app.add_url_rule(vanity_url + "/", vanity_url + "/", self.redirect_url)
                except Exception:
                    logger.exception(f"Could not add {vanity_url}")

    def redirect_url(self):
        vanity_url = "/" + request.url.split("/")[3]

        for match in self.url_list:
            for key in match.keys():
                if key == vanity_url:
                    resp = make_response(redirect(match[vanity_url], code=301))
                    resp.headers["Cache-Control"] = (
                        "no-store, no-cache, must-revalidate, " "post-check=0, pre-check=0, max-age=0"
                    )
                    resp.headers["Expires"] = "-1"
                    return resp
                else:
                    pass
