#!/usr/bin/python
# -*- coding: utf-8 -*-
# author:   Jan Hybs
from collections import namedtuple
from subprocess import PIPE, Popen
import os, sys, threading, random
from utils.globals import read, ensure_path, Config, GlobalTimeout
from utils.logger import Logger
from utils.timer import Timer

from config import max_wait_time


class DynamicLanguage(object):
    def __init__(self, request):
        """
        :type request: jobs.job_request.JobRequest
        """
        self.original_request = request
        self.dynamic_request = self._generate_ref_request(request)
        self.processor = LangMap.get(request.problem.ref_lang.id)(self.dynamic_request)

    def compile(self):
        return self.processor.compile()

    def run(self, rnd=False, validate=None, prepare=None):
        actions = self.processor.run()
        dyn_action = actions[-1]

        if prepare:
            dyn_action += " -p {}".format(prepare)

        if rnd:
            dyn_action += " -r {}".format(random.randint(1,10**10))

        if validate:
            dyn_action += ' -v "{}" "{}"'.format(*validate)

        actions[-1] = dyn_action

        return actions

    @staticmethod
    def _generate_ref_request(request):
        from jobs.job_request import JobRequest
        return JobRequest(dict(
            root=os.path.join(Config.problems, request.problem.id),
            filename=request.problem.ref_script,
            lang_id=request.problem.ref_lang.id
        ))


class Command(object):

    CommandResult = namedtuple('CommandResult', ('exit', 'info', 'process', 'duration'), verbose=False)

    def __init__(self, args, inn, out, err):
        self.inn_file = inn
        self.out_file = out
        self.err_file = err
        self.inn = None
        self.out = None
        self.err = None

        self.process = None
        self.args = args
        self.command = '; '.join(args)
        self.timer = Timer()
        self.terminated = False

        self.info = None

    def open_streams(self):
        ensure_path(self.inn_file)
        ensure_path(self.out_file)
        ensure_path(self.err_file)

        self.inn = PIPE if self.inn_file is None else open(self.inn_file, "rb")
        self.out = open(self.out_file, "wb")
        self.err = open(self.err_file, "wb")

    def close_streams(self):
        if self.inn_file is not None:
            self.inn.close()
        self.out.close()
        self.err.close()

    def _run(self, timeout):
        timeout = min([max_wait_time, timeout])

        def target():
            Logger.instance().info('Running command with time limit {:1.2f} s: {}'.format(timeout, self.command))
            self.process = Popen([self.command], stdout=self.out, stderr=self.err, stdin=self.inn, shell=True)
            self.process.communicate()
            Logger.instance().info('Command finished')

        thread = threading.Thread(target=target)
        thread.start()
        thread.join(GlobalTimeout.time_left())
        if thread.is_alive():
            Logger.instance().info('Terminating process')
            self.terminated = True
            self.global_terminate = GlobalTimeout.time_left() < 0
            try:
                self.process.terminate()
            except Exception as e:
                pass
            try:
                self.process.kill()
            except Exception as e:
                pass
            thread.join()

    def run(self, timeout=60):
        # empty command such as interpret language compilation
        if not self.command:
            return Command.CommandResult(
                exit=0,
                process=None,
                duration=0,
                info=dict(
                    terminated=False,
                    returncode=0,
                    error='',
                    output=self.out_file,
                    input=self.inn_file,
                    duration=0
                )
            )
        self.open_streams()
        self.timer.tick()
        self._run(timeout)
        self.timer.tock()
        self.close_streams()

        self.info = dict(
            terminated=self.terminated,
            returncode=self.process.returncode,
            error=read(self.err_file),
            output=self.out_file,
            input=self.inn_file,
            duration=self.timer.duration*1000,
        )
        # save global termination
        GlobalTimeout.decrease(self.timer.duration)
        self.info['global_terminated'] = self.terminated and GlobalTimeout.invalid()

        return Command.CommandResult(exit=self.process.returncode, info=self.info, process=self.process, duration=self.timer.duration*1000)


class LanguageProcess(object):
    def __init__(self, request):
        """
        :type request: jobs.job_request.JobRequest
        """
        self.request = request

    def compile(self):
        return [
            'cd "{r.root}"'.format(r=self.request),
            '{r.lang.compile} "{r.filename}"'.format(r=self.request)
        ]

    def run(self):
        return [os.path.join(self.request.root, 'main')]


class LanguageC(LanguageProcess):
    def compile(self):
        return [
            'cd "{r.root}"'.format(r=self.request),
            '{r.lang.compile} -o main "{r.filename}"'.format(r=self.request)
        ]


class LanguageCpp(LanguageProcess):
    def compile(self):
        return [
            'cd "{r.root}"'.format(r=self.request),
            '{r.lang.compile} -o main "{r.filename}"'.format(r=self.request)
        ]


class LanguageCpp11(LanguageProcess):
    def compile(self):
        return [
            'cd "{r.root}"'.format(r=self.request),
            '{r.lang.compile} -o main -std=c++11 "{r.filename}"'.format(r=self.request)
        ]


class LanguageCS(LanguageProcess):
    def compile(self):
        return [
            'cd "{r.root}"'.format(r=self.request),
            '{r.lang.compile} "{r.filename}" -o main'.format(r=self.request)
        ]

    def run(self):
        return [
            'cd "{r.root}"'.format(r=self.request),
            '{r.lang.run} "{r.main_file_name}"'.format(r=self.request)
        ]


class LanguageJava(LanguageProcess):
    def compile(self):
        return [
            'cd "{r.root}"'.format(r=self.request),
            '{r.lang.compile} "{r.filename}"'.format(r=self.request)
        ]

    def run(self):
        return [
            'cd "{r.root}"'.format(r=self.request),
            '{r.lang.run} main'.format(r=self.request)
        ]


class LanguagePascal(LanguageProcess):
    def compile(self):
        return [
            'cd "{r.root}"'.format(r=self.request),
            '{r.lang.compile} "{r.filename}"'.format(r=self.request)
        ]


class LanguagePython(LanguageProcess):
    def compile(self):
        return []

    def run(self):
        return [
            '{r.lang.run} "{r.main_file}"'.format(r=self.request)
        ]


class LangMap(object):
    lang_map = {
        'C': LanguageC,
        'CPP':LanguageCpp,
        'CPP11':LanguageCpp11,
        'CS':LanguageCS,
        'JAVA':LanguageJava,
        'PASCAL':LanguagePascal,
        'PYTHON27':LanguagePython,
    }
    @staticmethod
    def get(name):
        """
        :rtype : LanguageProcess
        """
        return LangMap.lang_map.get(name)
