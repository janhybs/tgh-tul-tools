#!/usr/bin/python
# -*- coding: utf-8 -*-
# author:   Jan Hybs

import json, os


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
        import json
        print json.dumps(info, indent=4)


def read(f):
    if not os.path.exists(f):
        return ''

    fp = open(f, 'r')
    s = fp.read()
    fp.close()
    return s


def remove_empty(f):
    if not os.path.exists(f):
        return

    if os.stat(f).st_size == 0:
        return os.unlink(f)


def ensure_path(f, is_file=True):
    if not f:
        return
    p = os.path.dirname(f) if is_file else f
    if not os.path.exists(p):
        os.makedirs(p)


def compare(a, b):
    result = None
    eof = False
    with open(a, 'rb') as f1, open(b, 'rb') as f2:
        while True:

            # read lines
            l1 = f1.readline()
            l2 = f2.readline()
            eof = l1 == ''

            # right strip white chars (\r\n, \n, \r, max differ)
            l1 = l1.rstrip()
            l2 = l2.rstrip()

            if l1 == '' and l2 == '':
                result = 0

                if eof:
                    break

            if l1 != l2:
                result = 1
                break

    return True if result == 0 else False