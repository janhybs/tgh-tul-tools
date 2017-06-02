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
        popen_args = self.processor.run()      # type: PopenArgs

        if prepare:
            popen_args.command += ['-p', str(prepare)]

        if rnd:
            popen_args.command += ['-r', str(random.randint(1, 10**10))]

        if validate:
            popen_args.command += ['-v']
            popen_args.command.extend(validate)
            # dyn_action += ' -v "{}" "{}"'.format(*validate)

        return popen_args

    @staticmethod
    def _generate_ref_request(request):
        from jobs.job_request import JobRequest
        return JobRequest(dict(
            root=os.path.join(Config.problems, request.problem.id),
            filename=request.problem.ref_script,
            lang_id=request.problem.ref_lang.id
        ))


class Command(object):

    class CommandResult(object):
        def __init__(self, returncode=0, process=None, duration=0.0, terminated=False, global_terminated=False):
            self.returncode = returncode
            self.process = process
            self.duration = duration
            self.terminated = terminated
            self.global_terminated = global_terminated

    def __init__(self, args, inn, out, err):
        self.inn_file = inn
        self.out_file = out
        self.err_file = err
        self.inn = None
        self.out = None
        self.err = None

        self.process = None
        self.args = args
        self.command = '; '.join(args.command)
        self.timer = Timer()
        self.terminated = False
        self.scale = 1.0

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
        timeout = min([max_wait_time, timeout]) * self.scale

        def target():
            Logger.instance().info('Running command with time limit {:1.2f} s: {} in {}'.format(timeout, self.args.command, self.args.cwd))
            self.process = Popen(self.args.command, stdout=self.out, stderr=self.err, stdin=self.inn, cwd=self.args.cwd)
            Logger.instance().info('started PID {}'.format(self.process.pid))
            self.process.wait()  # process itself is not limited but there is global limit
            Logger.instance().info('Command finished with %d' % self.process.returncode)

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
                print(e)

            try:
                self.process.kill()
            except Exception as e:
                print(e)
            thread.join()

    def run(self, timeout=max_wait_time):
        """
        :rtype: jobs.job_processing.Command.CommandResult
        """
        # empty command such as interpret language compilation
        if not self.args.command:
            return Command.CommandResult()

        self.open_streams()
        self.timer.tick()
        self._run(timeout)
        self.timer.tock()
        self.close_streams()

        # save global termination
        GlobalTimeout.decrease(self.timer.duration)

        # return run result
        return Command.CommandResult(
            returncode=self.process.returncode,
            duration=self.timer.duration*1000,
            terminated=self.terminated,
            global_terminated=self.terminated and GlobalTimeout.invalid()
        )


class PopenArgs(object):
    def __init__(self, cwd=None, *args):
        self.cwd = cwd
        self.command = list(args)


class LanguageProcess(object):
    def __init__(self, request):
        """
        :type request: jobs.job_request.JobRequest
        """
        self.request = request
        self.cd_compile = None
        self.cd_run = None

    def compile(self):
        r = self.request
        return PopenArgs(r.root,
                         r.lang.compile, r.filename)
        # return [
        #     'cd "{r.root}"'.format(r=self.request),
        #     '{r.lang.compile} "{r.filename}"'.format(r=self.request)
        # ]

    def run(self):
        r = self.request
        return PopenArgs(None,
                         os.path.join(self.request.root, 'main'))
        # return [os.path.join(self.request.root, 'main')]


class LanguageC(LanguageProcess):
    def compile(self):
        r = self.request
        return PopenArgs(r.root,
                         r.lang.compile, '-o', 'main', r.filename)
        # return [
        #     'cd "{r.root}"'.format(r=self.request),
        #     '{r.lang.compile} -o main "{r.filename}"'.format(r=self.request)
        # ]


class LanguageCpp(LanguageProcess):
    def compile(self):
        r = self.request
        return PopenArgs(r.root,
                         r.lang.compile, '-o', 'main', r.filename)
        # return [
        #     'cd "{r.root}"'.format(r=self.request),
        #     '{r.lang.compile} -o main "{r.filename}"'.format(r=self.request)
        # ]


class LanguageCpp11(LanguageProcess):
    def compile(self):
        r = self.request
        return PopenArgs(r.root,
                         r.lang.compile, '-o', 'main', '-std=c++11', r.filename)
        # return [
        #     'cd "{r.root}"'.format(r=self.request),
        #     '{r.lang.compile} -o main -std=c++11 "{r.filename}"'.format(r=self.request)
        # ]


class LanguageCS(LanguageProcess):
    def compile(self):
        r = self.request
        return PopenArgs(r.root,
                         r.lang.compile, r.filename, '-o', 'main')
        # return [
        #     'cd "{r.root}"'.format(r=self.request),
        #     '{r.lang.compile} "{r.filename}" -o main'.format(r=self.request)
        # ]

    def run(self):
        r = self.request
        return PopenArgs(r.root,
                         r.lang.run, r.main_file_name)
        # return [
        #     'cd "{r.root}"'.format(r=self.request),
        #     '{r.lang.run} "{r.main_file_name}"'.format(r=self.request)
        # ]


class LanguageJava(LanguageProcess):
    def compile(self):
        r = self.request
        return PopenArgs(r.root,
                         r.lang.compile, r.filename)
        # return [
        #     'cd "{r.root}"'.format(r=self.request),
        #     '{r.lang.compile} "{r.filename}"'.format(r=self.request)
        # ]

    def run(self):
        r = self.request
        return PopenArgs(r.root,
                         r.lang.run, 'main')
        # return [
        #     'cd "{r.root}"'.format(r=self.request),
        #     '{r.lang.run} main'.format(r=self.request)
        # ]


class LanguagePascal(LanguageProcess):
    def compile(self):
        r = self.request
        return PopenArgs(r.root,
                         r.lang.compile, r.filename)
        # return [
        #     'cd "{r.root}"'.format(r=self.request),
        #     '{r.lang.compile} "{r.filename}"'.format(r=self.request)
        # ]


class LanguagePython27(LanguageProcess):
    def compile(self):
        return PopenArgs()

    def run(self):
        r = self.request # changed
        return PopenArgs(r.root,
                         r.lang.run, r.main_file)
        # return [
        #     '{r.lang.run} "{r.main_file}"'.format(r=self.request)
        # ]


class LanguagePython35(LanguageProcess):
    def compile(self):
        return PopenArgs()

    def run(self):
        r = self.request # changed
        return PopenArgs(r.root,
                         r.lang.run, r.main_file)
        # return [
        #     '{r.lang.run} "{r.main_file}"'.format(r=self.request)
        # ]


class LangMap(object):
    lang_map = {
        'C': LanguageC,
        'CPP':LanguageCpp,
        'CPP11':LanguageCpp11,
        'CS':LanguageCS,
        'JAVA':LanguageJava,
        'PASCAL':LanguagePascal,
        'PYTHON27':LanguagePython27,
        'PYTHON35':LanguagePython35,
    }

    @staticmethod
    def get(name):
        """
        :rtype : class LanguageProcess
        """
        return LangMap.lang_map.get(name)
