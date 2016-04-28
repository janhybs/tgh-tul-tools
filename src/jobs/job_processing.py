#!/usr/bin/python
# -*- coding: utf-8 -*-
# author:   Jan Hybs
from collections import namedtuple
from subprocess import PIPE
from psutil import Popen
import os, sys, threading
from utils.globals import read, ensure_path, Config
from utils.timer import Timer

MAX_DURATION = 60


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

    def run(self, random=False, validate=None, prepare=None):
        actions = self.processor.run()
        dyn_action = actions[-1]

        if prepare:
            dyn_action += " -p {}".format(prepare)

        if random:
            dyn_action += " -r"

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

    def run(self):
        self.open_streams()
        self.timer.tick()
        self.process = Popen([self.command], stdout=self.out, stderr=self.err, stdin=self.inn, shell=True)
        self.process.communicate()
        self.timer.tock()
        self.close_streams()

        self.info = dict(
            command=self.args,
            returncode=self.process.returncode,
            error=read(self.err_file),
            output=self.out_file,
            input=self.inn_file,
            duration=self.timer.duration*1000,
        )

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
            '{r.lang.compile} "{r.filename}"'.format(r=self.request)
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

    def run(self):
        return [
            '{r.lang.run} "{r.main_file_name}"'.format(r=self.request)
        ]


class LanguagePython(LanguageProcess):
    def compile(self):
        return []

    def run(self):
        return [
            '{r.lang.run} "{r.main_file}"'.format(r=self.request)
        ]

#
# class CommandResult(object):
#     def __init__(self, exit=None, error=None, cmd=None):
#         self.exit = exit
#         self.error = error
#         self.cmd = cmd
#
#     def is_empty(self):
#         return self.exit is None
#
#     def is_ok(self):
#         return self.exit == 0
#
#     def is_not_wrong(self):
#         return self.isok() or self.isempty()
#
#     def __repr__(self):
#         return "[CommandResult exit:{:d} {:s} {}]".format(self.exit, self.error, self.cmd)
#
#     @staticmethod
#     def loadfile(path, mode='r'):
#         if not os.path.isfile(str(path)):
#             return ''
#
#         with open(path, mode) as f:
#             return f.read()
#
#
# class Command(object):
#     def __init__(self, args, inn=None, out=None, err=None):
#         # args.append ("exit") # terminate just in case
#         self.command = '; '.join(args)
#         self.timer = Timer(self.command)
#         self.process = None
#         self.fatal_error = None
#
#         self.shell = True
#         self.inn = self.inn_path = inn
#         self.out = self.out_path = out
#         self.err = self.err_path = err
#
#         self.duration = 0
#         self.timeout = MAX_DURATION
#         self.terminated = False
#
#     def open_files(self):
#         self.inn = PIPE if self.inn is None else open(self.inn, "rb")
#         self.out = PIPE if self.out is None else open(self.out, "wb")
#         self.err = PIPE if self.err is None else open(self.err, "wb")
#
#     def close_files(self):
#         if self.inn is not PIPE:
#             self.inn.close()
#         if self.out is not PIPE:
#             self.out.close()
#         if self.err is not PIPE:
#             self.err.close()
#
#     def __repr__(self):
#         return "[Command: {} ({:d} s)]".format(self.command, self.timeout)
#
#     def run(self, timeout=MAX_DURATION):
#         self.timeout = timeout
#         if not self.command:
#             return CommandResult()
#
#         print self
#         self.open_files()
#
#         def target():
#             try:
#                 self.process = Popen([self.command], stdout=self.out, stderr=self.err, stdin=self.inn, shell=self.shell)
#                 self.process.communicate()
#             except Exception as e:
#                 # if shell is False exception can be thrown
#                 print 'Fatal error'
#                 print e
#                 self.fatal_error = str(e) + "\n"
#                 self.fatal_error += str(self) + "\n"
#                 if hasattr(e, 'child_traceback'):
#                     self.fatal_error += str(e.child_traceback)
#
#         # create thread
#         thread = threading.Thread(target=target)
#
#         # run thread
#         self.timer.tick()
#         thread.start()
#         thread.join(self.timeout)
#         self.timer.tock()
#
#         # kill longer processes
#         if thread.is_alive():
#             self.process.terminate()
#             self.terminated = True
#             thread.join()
#
#         # files
#         self.close_files()
#
#         # on error return error
#         if self.fatal_error is not None:
#             return CommandResult(1, str(self.fatal_error), self)
#
#         if self.terminated:
#             return CommandResult(5, "Process was terminated (did not finish in time)", self)
#
#         # return process if no FATAL error occurred
#         err_msg = (CommandResult.loadfile(self.err_path) + CommandResult.loadfile(self.out_path)).lstrip()
#         return CommandResult(self.process.returncode, err_msg, self)


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