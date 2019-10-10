#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import absolute_import, print_function

import yaml
import os


class Configuration(object):

    def __init__(self):
        self.content = self.read_config()

    def read_config(self):
        dir_path = os.path.dirname(os.path.abspath(__file__))
        config_file_path = os.path.join(dir_path, "conf.yaml")
        with open(config_file_path, "r") as handle:
            env_map = yaml.load(handle)
            return env_map

    def fetch(self, *args):
        firstly = True
        collection = None
        for arg in args:
            if firstly:
                collection = self.content.get(arg)
                firstly = False
            else:
                collection = collection.get(arg)
        return collection


def fetch(*args):
    return Configuration().fetch(*args)


