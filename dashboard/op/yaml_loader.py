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
                stream = yaml.load(stream)
            except yaml.YAMLError as e:
                print(e)
        return stream

    def __find(self, name, path):
        for root, dirs, files in os.walk(path):
            if name in files:
                return os.path.join(root, name)
