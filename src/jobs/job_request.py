#!/usr/bin/python
# -*- coding: utf-8 -*-
# author:   Jan Hybs

import json, os, sys, datetime
from utils.globals import Langs, random_range
from utils.globals import Problems
from pluck import pluck


class JobRequest(object):
    """
    :type problem: Problem
    :type lang   : Lang
    """
    def __init__(self, request_file):
        if type(request_file) is dict:
            request = request_file
        else:
            with open(request_file, 'r') as fp:
                request = json.load(fp)

        self.username = request.get('username', None)
        self.nameuser = request.get('nameuser', None)
        self.reference = request.get('reference', None)
        self.timestamp = datetime.datetime.fromtimestamp(request.get('timestamp', 0))
        self.root = request.get('root', None)
        self.filename = request.get('filename', None)

        self.main_file = os.path.join(self.root, self.filename)
        self.main_file_name, self.main_file_ext = os.path.splitext(self.main_file)

        self.lang = Langs.get(request.get('lang_id', None))
        self.problem = Problems.get(request.get('problem_id', None))
        try:
            self.cases = request.get('cases', pluck(self.problem.input if self.problem else [], 'id'))
        except Exception as e:
            print e
            self.cases = []
            raise 
        

        self.result_file = os.path.join(self.root, 'result.json')
        self.output_root = os.path.join(self.root, 'output')
        self.delete_me_file = os.path.join(self.root, '.delete-me')

    def __repr__(self):
        return '{ref}solution "{self.problem.id}" from "{self.username}"'.format(self=self, ref='reference ' if self.reference else '')


class Lang(object):
    def __init__(self, o={}):
        self.id = o.get('id', None)
        self.extension = o.get('extension', None)
        self.name = o.get('name', None)
        self.version = o.get('version', None)
        self.compile = o.get('compile', None)
        self.run = o.get('run', None)
        self.scale = o.get('scale', 1.0)
        
    def __repr__(self):
        return 'Language {self.id} ({self.version}), scale: {self.scale}x'.format(self=self)


class Problem(object):
    def __init__(self, o={}):
        self.id = o.get("id", None)
        self.name = o.get("name", None)
        self.ref_script = o.get("ref_script", None)
        self.ref_lang = Langs.get(o.get("ref_lang", None))
        self.multiple_solution = o.get("multiple_solution", None)
        self.problem_size_description = o.get("problem_size_description", None)
        self.input = [ProblemInput(p) for p in o.get("input", [])]


class ProblemInput(object):
    def __init__(self, o={}):
        self.id = o.get('id', None)
        self.time = o.get('time', 60)
        self.problem_size = o.get('problem_size', None)
        self.random = o.get('random', None)
        self.dynamic = self.problem_size is not None
        self.cases = o.get('cases', 10 if self.random else 1)
        self.input_cases = sorted(random_range(self.cases, o.get('random_cases', 1)))

    def __repr__(self):
        if self.dynamic:
            return 'Dynamic solution {rnd} random having {self.cases} case/s'.format(
                self=self,
                rnd='with' if self.random else 'without'
            )
        return 'Static solution'

    def dict(self):
        return dict(
            id=self.id,
            problem_size=self.problem_size,
            random=self.random
        )
