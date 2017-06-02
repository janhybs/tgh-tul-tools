#!/usr/bin/python
# -*- coding: utf-8 -*-
# author:   Jan Hybs

import json, os
import random
import yaml

from config import max_wait_time

class Config(object):
    watch_dir = None
    problems = None
    data = None
    root = None
    config_dir = None


class Langs(object):
    items = {}
    json_file = None
    
    @classmethod
    def reload(cls):
        from jobs.job_request import Lang
        with open(cls.json_file, 'r') as fp:
            items = yaml.load(fp)
            for k, v in items.items():
                cls.items[k] = Lang(v)

    @classmethod
    def init(cls, f):
        cls.json_file = f
        cls.reload()


    @classmethod
    def get(cls, id):
        """
        :rtype : Lang
        """
        return cls.items.get(id, None)


class Problems(object):
    items = {}
    json_file = None
    
    @classmethod
    def reload(cls):
        from jobs.job_request import Problem

        with open(cls.json_file, 'r') as fp:
            items = yaml.load(fp)
            for k, v in items.items():
                cls.items[k] = Problem(v)

    @classmethod
    def init(cls, f):
        cls.json_file = f
        cls.reload()


    @classmethod
    def get(cls, id):
        """
        :rtype : Problem
        """
        return cls.items.get(id, None)


class ProcessException(Exception):
    """
    :type info : jobs.job_control.CaseResult
    """
    def __init__(self, info):
        super(ProcessException, self).__init__()
        self.info = info


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


def tryjson(f):
    content = read(f)
    try:
        return json.loads(content)
    except Exception as e:
        return content


def random_range(max, count, min=1):
    r = list(range(min, max + min))
    random.shuffle(r)
    return r[0:count]


class GlobalTimeout(object):
    _global_time = max_wait_time
    _out_of_time = 0.1
    _time_left = _global_time

    @classmethod
    def reset(cls, scale=1.0):
        cls._time_left = cls._global_time * scale
        print('Time reset:     [remaining: {:1.2f}]'.format(cls.time_left()))

    @classmethod
    def decrease(cls, duration):
        cls._time_left -= duration
        print('Time decreased: [remaining: {:1.2f}]'.format(cls.time_left()))

    @classmethod
    def time_left(cls):
        return 0.01 if cls.invalid() else cls._time_left


    @classmethod
    def invalid(cls):
        return cls._time_left < cls._out_of_time


class SmartFile(object):
    """
    :type filename     : str
    """
    def __init__(self, show_content=False):
        self.filename = None
        self.show_content = False

    def __call__(self, filename):
        self.filename = filename
        self.servername = None

    def create_server_path(self, job, attempt_dir):
        if not self.exists():
            return

        # is filename in job root?
        if self.filename.startswith(job.root):
            self.servername = os.path.join(attempt_dir, os.path.relpath(self.filename, job.root))
        # path is already in servername format (ref inn out)
        else:
            self.servername = self.filename

    def value(self, as_json=False):
        if self.exists():
            if as_json:
                with open(self.filename, 'r') as fp:
                    return json.load(fp, encoding="utf-8")
            with open(self.filename, 'r') as fp:
                return fp.read()
        return None

    def to_json(self):
        if not self.exists():
            return dict(
                path=self.filename,
                server=None,
                size=0
            )

        if self.show_content:
            return dict(
                path=self.filename,
                content=self.value(),
                size=os.path.getsize(self.filename),
                server=self.servername,
            )
        return dict(
                path=self.filename,
                size=os.path.getsize(self.filename),
                server=self.servername,
            )

    def __nonzero__(self):
        return bool(self.filename) and os.path.exists(self.filename)

    exists = __nonzero__
