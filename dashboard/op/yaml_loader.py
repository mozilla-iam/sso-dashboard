"""File based loader. Will fetch connected apps from yml file instead."""

import logging
import yaml


logger = logging.getLogger()


class Application:
    def __init__(self, app_dict):
        self.app_dict = app_dict
        self.apps = self._load_data()
        self._alphabetize()

    def _load_data(self):
        try:
            stream = yaml.safe_load(self.app_dict)
        except yaml.YAMLError:
            logger.exception("Could not load YAML")
            stream = None
        return stream

    def _alphabetize(self):
        self.apps["apps"].sort(key=lambda a: a["application"]["name"].lower())

    def vanity_urls(self):
        """
        Parse apps.yml, return list of dicts, each dict is
        {'/some-redirect': 'https://some/destination'}
        """
        redirects = []
        try:
            all_apps = self.apps["apps"]
        except (TypeError, KeyError):
            return redirects
        for app_entry in all_apps:
            app = app_entry["application"]
            yaml_vanity_url_list = app.get("vanity_url")
            if not isinstance(yaml_vanity_url_list, list):
                continue
            for redirect in yaml_vanity_url_list:
                redirects.append({redirect: app["url"]})
        return redirects
