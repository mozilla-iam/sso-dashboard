"""File based loader. Will fetch connected apps from yml file instead."""

import logging
import operator
import os
import yaml


logger = logging.getLogger(__name__)


class Application(object):
    def __init__(self):
        self.config_file = self._find("apps.yml", ".")
        self.apps = self._load_data()
        self._render_data()
        self._alphabetize()

    def _load_authorized(self, session):
        pass

    def _load_data(self):
        stream = dict()
        with open(self.config_file, 'r') as stream:
            try:
                stream = yaml.safe_load(stream)
            except yaml.YAMLError as e:
                logger.info(e)
                pass
        return stream

    def _render_data(self):
        for app in self.apps['apps']:
            app['application']['alt_text'] = app['application']['name']
            app['application']['name'] = self._truncate(
                app['application']['name']
            )

    def _alphabetize(self):
        try:
            self.apps['apps'] = sorted(
                self.apps['apps'], key=operator.itemgetter('name')
            )
        except Exception as e:
            logger.info(e)
            pass

    def _find(self, name, path):
        for root, dirs, files in os.walk(path):
            if name in files:
                return os.path.join(root, name)

    def _has_vanity(self, app):
        try:
            app['application']['vanity_url']
            return True
        except Exception:
            return False

    def _truncate(self, app_name):
        """If name is longer than allowed 18 chars truncate the name."""
        app_name = (
            app_name[:16] + '..'
        ) if len(app_name) > 18 else app_name

        return app_name

    def vanity_urls(self):
        redirects = []
        for app in self.apps['apps']:
            if self._has_vanity(app):
                for redirect in app['application']['vanity_url']:
                    redirects.append(
                        {
                            redirect: app['application']['url']
                        }
                    )
        return redirects
