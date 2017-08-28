from flask import make_response
from flask import redirect
from flask import request

from op import yaml_loader


class Router(object):
    def __init__(self, app):
        self.app = app
        self.url_list = yaml_loader.Application().vanity_urls()

    def setup(self):
        for url in self.url_list:
            try:
                self.app.add_url_rule(url.keys()[0], url.keys()[0], self.redirect_url)
                self.app.add_url_rule(url.keys()[0] + "/", url.keys()[0] + "/", self.redirect_url)
            except Exception as e:
                print(e)

    def redirect_url(self):
        vanity_url = '/' + request.url.split('/')[3]

        for match in self.url_list:
            if match.keys()[0] == vanity_url:
                resp = make_response(redirect(match[vanity_url], code=301))
                resp.headers['Cache-Control'] = ('no-store, no-cache, must-revalidate, '
                                                 'post-check=0, pre-check=0, max-age=0')
                resp.headers['Expires'] = '-1'
                return resp
            else:
                pass
