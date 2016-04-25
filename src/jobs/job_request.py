#!/usr/bin/python
# -*- coding: utf-8 -*-
# author:   Jan Hybs

import json, os, sys


class JobRequest(object):
    def __init__(self, request_file):
        with open(request_file, 'r') as fp:
            request = json.load(fp)