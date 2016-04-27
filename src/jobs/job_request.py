#!/usr/bin/python
# -*- coding: utf-8 -*-
# author:   Jan Hybs

import json, os, sys, datetime
from utils.globals import Langs, Problems


class JobRequest(object):
    def __init__(self, request_file):
        if type(request_file) is dict:
            request = request_file
        else:
            with open(request_file, 'r') as fp:
                request = json.load(fp)

        self.username = request.get('username', None)
        self.reference = request.get('reference', None)
        self.timestamp = datetime.datetime.fromtimestamp(request.get('timestamp', 0))
        self.root = request.get('root', None)
        self.filename = request.get('filename', None)

        self.main_file = os.path.join(self.root, self.filename)
        self.main_file_name, self.main_file_ext = os.path.splitext(self.main_file)

        self.lang = Langs.get(request.get('lang_id', None))
        self.problem = Problems.get(request.get('problem_id', None))
