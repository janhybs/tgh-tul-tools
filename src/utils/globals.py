#!/usr/bin/python
# -*- coding: utf-8 -*-
# author:   Jan Hybs

import json


class Langs(object):
    items = {}

    @classmethod
    def init(cls, f):
        with open(f, 'r') as fp:
            items = json.load(fp)
            for k, v in items.items():
                cls.items[k] = Lang(v)


    @classmethod
    def get(cls, id):
        """
        :rtype : Lang
        """
        return cls.items.get(id, None)


class Problems(object):
    items = {}

    @classmethod
    def init(cls, f):
        with open(f, 'r') as fp:
            items = json.load(fp)
            for k, v in items.items():
                cls.items[k] = Problem(v)


    @classmethod
    def get(cls, id):
        """
        :rtype : Problem
        """
        return cls.items.get(id, None)


class Lang(object):
    def __init__(self, o={}):
        self.id = o.get('id', None)
        self.extension = o.get('extension', None)
        self.name = o.get('name', None)
        self.version = o.get('version', None)
        self.compile = o.get('compile', None)
        self.run = o.get('run', None)


class Problem(object):
    def __init__(self, o={}):
        self.id = o.get("id", None)
        self.name = o.get("name", None)
        self.ref_script = o.get("ref_script", None)
        self.ref_lang = Langs.get(o.get("ref_lang", None))
        self.multiple_solution = o.get("multiple_solution", None)
        self.problem_size_descritption = o.get("problem_size_descritption", None)
        self.input = [ProblemInput(p) for p in o.get("input", [])]


class ProblemInput(object):
    def __init__(self, o={}):
        self.id = o.get('id', None)
        self.time = o.get('time', None)
        self.problem_size = o.get('problem_size', None)
        self.random = o.get('random', None)
        self.dynamic = self.problem_size is not None or self.random is not None


class ProcessException(Exception):
    def __init__(self, info):
        super(ProcessException, self).__init__()
        self.info = info


def read(f):
    import os
    if not os.path.exists(f):
        return ''

    fp = open(f, 'r')
    s = fp.read()
    fp.close()
    return s


def remove_empty(f):
    import os
    if not os.path.exists(f):
        return

    if os.stat(f).st_size == 0:
        return os.unlink(f)