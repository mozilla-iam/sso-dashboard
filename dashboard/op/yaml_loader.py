"""File based loader. Will fetch connected apps from yml file instead."""

import os
import yaml

class Application(object):
    def __init__(self):
        self.config_file = self.__find("apps.yml", ".")
        self.apps = self.__load_data()

    def __load_authorized(self, session):
        pass

    def __load_data(self):
        stream = {}
        with open(self.config_file, 'r') as stream:
            try:
                stream = yaml.safe_load(stream)
            except yaml.YAMLError as e:
                print(e)
        return stream

    def __find(self, name, path):
        for root, dirs, files in os.walk(path):
            if name in files:
                return os.path.join(root, name)

    def __has_vanity(self, app):
        try:
            app['application']['vanity_url']
            return True
        except:
            return False

    def stats(self):
        okta = 0
        auth0 = 0
        for app in self.apps['apps']:
            if app['application']['op'] == 'okta':
                okta = okta + 1
            if app['application']['op'] == 'auth0':
                auth0 = auth0 + 1
        return { 'auth0': auth0, 'okta': okta }

    def vanity_urls(self):
        redirects = []
        for app in self.apps['apps']:
            if self.__has_vanity(app):
                for redirect in app['application']['vanity_url']:
                    redirects.append(
                        {
                            redirect: app['application']['url']
                         }
                    )
        return redirects
