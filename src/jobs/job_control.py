#!/usr/bin/python
# -*- coding: utf-8 -*-
# author:   Jan Hybs

import os
import threading
import time
import datetime


from jobs.job_processing import DynamicLanguage, Command, LangMap, PopenArgs
from jobs.job_request import ProblemInput
from utils.globals import remove_empty, compare, tryjson, Config, ensure_path, GlobalTimeout, \
    SmartFile, ProcessException
from utils.logger import Logger
from config import wait_timescale


class CaseResult(object):
    """
    :type problem_input    : jobs.job_request.ProblemInput
    :type problem          : jobs.job_request.Problem
    """
    def __init__(self, case_id, problem, problem_input):
        self.case_id = case_id
        self.problem = problem
        self.problem_input = problem_input

        self.inn_file = SmartFile(show_content=False)
        self.out_file = SmartFile(show_content=False)
        self.err_file = SmartFile(show_content=True)
        self.ref_file = SmartFile(show_content=False)

        self.error = None
        self.command = None
        self.returncode = None
        self.details = None

        self.result = JobCode.UNKNOWN_ERROR
        self.duration = 0.0

        self.random_str = None
        self.problem_size_str = None

    def confirm(self, job, attempt_dir):
        self.error = self.err_file.value()
        self.random_str = ' -r' if self.problem_input.random else ''
        self.problem_size_str = ' -p {}'.format(self.problem_input.problem_size) if self.problem_input.problem_size else ''

        [f.create_server_path(job, attempt_dir) for f in [self.inn_file, self.out_file, self.err_file, self.ref_file]]

    def get_error(self):
        return dict(
            error=self.err_file.value(),
            returncode=self.returncode,
            max_result=self.result.code,
            result=dict(
                code=self.result.code,
                name=self.result.longname,
                duration=self.duration,
                returncode=self.returncode,
                details=self.details
            )
        )

    def to_json(self):
        return dict(
            info=dict(
                case_id=self.case_id,
                problem_size=self.problem_input.problem_size,
                problem_random=self.problem_input.random,
                command=self.command,
                # problem_cases=self.problem_input.cases,
                # problem_multiple_solution=self.problem.multiple_solution,
            ),
            files=dict(
                input=self.inn_file,
                output=self.out_file,
                error=self.err_file,
                reference=self.ref_file,
            ),
            result=dict(
                code=self.result.code,
                name=self.result.longname,
                duration=self.duration,
                returncode=self.returncode,
                details=self.details
            )
        )


class JobCode(object):
    class L(object):
        def __init__(self, code, shortname, longname=None):
            self.code = code
            self.shortname = shortname
            self.longname = longname or self.shortname

        def __repr__(self):
            return self.longname

        def __call__(self, *args, **kwargs):
            return self.code

        def __hash__(self):
            return hash(self.code)

        def __eq__(self, other):
            return self.code == other.code

        def __int__(self):
            return self.code

        def __ge__(self, other):
            return self.code >= other.code

        def __gt__(self, other):
            return self.code > other.code

        def to_json(self):
            return self.code

    # ####################################
    # t ... time limit for case_i
    # d ... duration for case_i
    # ####################################

    # internal value
    OK                      = L(0,  'O', 'OK')
    # internal value
    RUN_OK                  = L(0,  'O', 'OK')

    # solution was correct and d <= t
    CORRECT_OUTPUT          = L(1,  'A', 'ACCEPTED')
    # solution was correct and d <= t * 10
    TIMEOUT_CORRECT_OUTPUT  = L(3,  'T', 'TIMEOUT_ACC')

    # solution was incorrect and d <= t
    WRONG_OUTPUT            = L(5,  'W', 'WRONG')
    # solution was incorrect and d <= t * 10
    TIMEOUT_WRONG_OUTPUT    = L(7,  'W', 'TIMEOUT_WRONG')

    # compilation error
    COMPILE_ERROR           = L(10, 'E', 'COMP_ERROR')
    # runtime error
    RUN_ERROR               = L(20, 'E', 'RUN_ERROR')
    # local timeout for case_i, d > t * 10
    TIMEOUT                 = L(30, 'E', 'LOCAL_TIMEOUT')
    # global timeout, sum of all d > 60
    GLOBAL_TIMEOUT          = L(40, 'E', 'GLOBAL_TIMEOUT')
    # case was skipped due to global timeout
    SKIPPED                 = L(50, 'E', 'SKIPPED')
    # something went wrong, like missing input file and other things
    UNKNOWN_ERROR           = L(100,'E', 'ERROR')


class JobControl(object):
    global_time_limit = 5
    root = None
    monitor_thread = None

    @classmethod
    def process(cls, request):
        """
        :type request: jobs.job_request.JobRequest
        """

        # reset global time for this solution
        GlobalTimeout.reset(request.lang.scale)

        # prepare output
        ensure_path(os.path.join(request.root, 'output'), False)
        if request.reference:
            job = ReferenceJob(request)
        else:
            job = StudentJob(request)

        result = job.process()

        return result

    @classmethod
    def monitor(cls):
        def target():
            start_time = time.time()
            while True:
                print(datetime.timedelta(seconds=int(time.time()-start_time)))
                time.sleep(0.5)

        monitor_thread = threading.Thread(name='monitor-thread', target=target)
        monitor_thread.start()


class StudentJob(object):
    """
    :type module             : jobs.job_processing.LanguageProcess
    """
    def __init__(self, request):
        """
        :type request: jobs.job_request.JobRequest
        """
        self.r = request
        self.module = None
        self.reference = ReferenceJob(request)
        self.program_root = os.path.join(Config.problems, self.r.problem.id)

    def process(self):
        prepared = self.prepare_solution()
        if prepared is not True:
            raise ProcessException(prepared)

        results = list()
        for case in self.r.cases:
            input_spec = next((x for x in self.r.problem.input if x.id == case), None)
            # input_spec = self.r.problem.input[case]
            Logger.instance().debug('  {case_id}: {input_spec}'.format(case_id=input_spec.id, input_spec=input_spec))
            if input_spec.dynamic:
                results.extend(self._dynamic(input_spec))
            else:
                results.append(self._static(input_spec, input_spec.id))
        return results

    def _static(self, input_spec, case_id):
        """
        :type input_spec: jobs.job_request.ProblemInput
        """
        case_result = CaseResult(case_id, self.r.problem, input_spec)

        if GlobalTimeout.invalid():
            case_result.result = JobCode.SKIPPED
            return case_result

        # prepare paths
        ref_out_file = os.path.join(self.program_root, 'output', '{}.out'.format(case_id))
        inn_file = os.path.join(self.program_root, 'input', '{}.in'.format(case_id))
        out_file = os.path.join(self.r.root, 'output', '{}.out'.format(case_id))
        err_file = os.path.join(self.r.root, 'output', '{}.err'.format(case_id))

        # save files
        case_result.inn_file(inn_file)
        case_result.out_file(out_file)
        case_result.err_file(err_file)
        case_result.ref_file(ref_out_file)

        if not os.path.exists(inn_file):
            Logger.instance().warning('    {} Input file does not exists {}'.format(case_id, inn_file))
            case_result.result = JobCode.UNKNOWN_ERROR
            case_result.error = '{} Input file does not exists {}'.format(case_id, inn_file)
            return case_result

        # run command
        run_args = self.module.run()  # type: jobs.job_processing.PopenArgs
        run_command = Command(run_args, inn_file, out_file, err_file)
        run_command.scale = self.r.lang.scale
        run_result = run_command.run(input_spec.time * wait_timescale)

        # grab result
        case_result.duration = run_result.duration
        case_result.returncode = run_result.returncode
        case_result.command = ' '.join(run_args.command) if len(run_args.command) > 0 else '<no command>'

        # timeout
        if run_result.global_terminated:
            case_result.result = JobCode.GLOBAL_TIMEOUT
            Logger.instance().info('    {} Command was terminated (global timeout)!'.format(case_id))
            return case_result

        # timeout
        if run_result.terminated:
            case_result.result = JobCode.TIMEOUT
            Logger.instance().info('    {} Command was terminated!'.format(case_id))
            return case_result

        # run error
        if run_result.returncode != 0:
            case_result.result = JobCode.RUN_ERROR
            Logger.instance().info('    {} error while execution'.format(case_id))
            return case_result

        # run ok
        case_result.result = JobCode.RUN_OK
        remove_empty(err_file)

        # run ref script to test solution's output
        if not self.r.problem.multiple_solution:
            compare_result = self.compare(case_id, ref_out_file, out_file)
            case_result.result = compare_result.get('result')
            case_result.details = compare_result.get('details', None)
            case_result.error = compare_result.get('error', None)
        else:
            compare_result = self.reference.test_solution(case_id)
            case_result.result = compare_result.get('result')
            case_result.details = compare_result.get('comparison', None)
            case_result.error = compare_result.get('error', None)

        # mark timeout results
        max_runtime = input_spec.time * self.r.lang.scale
        if run_result.duration/1000 > max_runtime:
            if case_result.result is JobCode.CORRECT_OUTPUT:
                case_result.result = JobCode.TIMEOUT_CORRECT_OUTPUT

            elif case_result.result == JobCode.WRONG_OUTPUT:
                case_result.result = JobCode.TIMEOUT_WRONG_OUTPUT

        return case_result

    def _dynamic(self, input_spec):
        """
        :type input_spec: jobs.job_request.ProblemInput
        """
        result = list()

        for c in input_spec.input_cases or [1]:
            case_id = '{}.{}'.format(input_spec.id, c)
            # generating reference output
            result.append(self._static(input_spec, case_id))
        return result

    @staticmethod
    def compare(case_id, a, b):
        info = dict()
        try:
            compare_result = compare(a, b)
            if compare_result:
                info['result'] = JobCode.CORRECT_OUTPUT
                Logger.instance().debug('    {} correct output[F]'.format(case_id))
                return info
            else:
                info['result'] = JobCode.WRONG_OUTPUT
                Logger.instance().debug('    {} wrong output[F]'.format(case_id))
                return info
        except Exception as e:
                info['result'] = JobCode.UNKNOWN_ERROR
                info['error'] = str(e)
                info['details'] = 'Error during file comparison'
                return info

    def prepare_solution(self):
        if self.module is not None:
            return True

        compile_out = os.path.join(self.r.root, 'compile.out')
        compile_err = os.path.join(self.r.root, 'compile.err')

        self.module = LangMap.get(self.r.lang.id)(self.r)

        compile_command = Command(self.module.compile(), None, compile_out, compile_err)
        compile_result = compile_command.run()

        if compile_result.returncode != 0:
            case_result = CaseResult('compile-phase', self.r.problem, ProblemInput())
            case_result.result = JobCode.COMPILE_ERROR
            case_result.returncode = compile_result.returncode
            case_result.inn_file(None)
            case_result.out_file(compile_out)
            case_result.err_file(compile_err)
            return case_result

        # clean up
        remove_empty(compile_out)
        remove_empty(compile_err)

        return True


class ReferenceJob(object):
    """
    :type module        : DynamicLanguage
    """
    def __init__(self, request):
        """
        :type request: jobs.job_request.JobRequest
        """
        self.r = request
        self.module = None
        self.program_root = os.path.join(Config.problems, self.r.problem.id)

    def process(self):
        prepared = self.prepare_reference()
        if prepared is not True:
            raise ProcessException(prepared)

        results = list()
        for input_spec in self.r.problem.input:
            Logger.instance().debug('  {case_id}: {input_spec}'.format(case_id=input_spec.id, input_spec=input_spec))
            if input_spec.dynamic:
                results.extend(self._dynamic(input_spec))
            else:
                results.append(self._static(input_spec, input_spec.id))
        return results

    def _dynamic(self, input_spec):
        """
        :type input_spec: jobs.job_request.ProblemInput
        """
        cases = input_spec.cases
        result = list()

        for c in range(1, cases + 1):
            case_id = '{}.{}'.format(input_spec.id, c)
            case_result = CaseResult(case_id, self.r.problem, input_spec)

            inn_file = None
            out_file = os.path.join(self.program_root, 'input', '{}.in'.format(case_id))
            err_file = os.path.join(self.program_root, 'input', '{}.err'.format(case_id))

            # save files
            case_result.inn_file(inn_file)
            case_result.out_file(out_file)
            case_result.err_file(err_file)

            # run command
            run_args = self.module.run(prepare=input_spec.problem_size, rnd=input_spec.random)
            run_command = Command(run_args, inn_file, out_file, err_file)
            run_command.scale = self.r.lang.scale
            run_result = run_command.run()

            # grab result
            case_result.duration = run_result.duration
            case_result.returncode = run_result.returncode
            case_result.command = ' '.join(run_args.command) if len(run_args.command) > 0 else '<no command>'

            # run error
            if run_result.returncode != 0:
                case_result.result = JobCode.RUN_ERROR
                result.append(case_result)
                Logger.instance().debug('    {} error while generating input file'.format(case_id))
                continue

            # run ok
            case_result.result = JobCode.RUN_OK
            result.append(case_result)
            remove_empty(err_file)
            Logger.instance().debug('    {} input file generated'.format(case_id))

            # ---------------------------
            # generating reference output
            result.append(self._static(input_spec, case_id))

        return result

    def _static(self, input_spec, case_id):
        """
        :type input_spec: jobs.job_request.ProblemInput
        """
        case_result = CaseResult(case_id, self.r.problem, input_spec)

        # prepare files
        inn_file = os.path.join(self.program_root, 'input', '{}.in'.format(case_id))
        out_file = os.path.join(self.program_root, 'output', '{}.out'.format(case_id))
        err_file = os.path.join(self.program_root, 'output', '{}.err'.format(case_id))

        # save files
        case_result.inn_file(inn_file)
        case_result.out_file(out_file)
        case_result.err_file(err_file)

        # run command
        run_args = self.module.run()
        run_command = Command(run_args, inn_file, out_file, err_file)
        run_command.scale = self.r.lang.scale
        run_result = run_command.run()

        # grab result
        case_result.duration = run_result.duration
        case_result.returncode = run_result.returncode
        case_result.command = ' '.join(run_args.command) if len(run_args.command) > 0 else '<no command>'

        # run error
        if run_result.returncode != 0:
            case_result.result = JobCode.RUN_ERROR
            Logger.instance().debug('    {} error while generating output file'.format(case_id))
            return case_result

        # run ok
        case_result.result = JobCode.RUN_OK
        remove_empty(err_file)
        Logger.instance().debug('    {} output file created'.format(case_id))

        return case_result

    def prepare_reference(self):
        """
        :rtype : DynamicLanguage or CaseResult
        """
        if self.module is not None:
            return True

        compile_out = os.path.join(self.program_root, 'compile.out')
        compile_err = os.path.join(self.program_root, 'compile.err')

        self.module = DynamicLanguage(self.r)

        compile_command = Command(self.module.compile(), None, compile_out, compile_err)
        compile_result = compile_command.run()

        if compile_result.returncode != 0:
            case_result = CaseResult('compile-phase', self.r.problem, ProblemInput())
            case_result.returncode = compile_result.returncode
            case_result.inn_file(None)
            case_result.out_file(compile_out)
            case_result.err_file(compile_err)
            return case_result

        # clean up
        remove_empty(compile_out)
        remove_empty(compile_err)

        return True

    def test_solution(self, case_id):
        self.prepare_reference()
        verify_inn_file = os.path.join(self.program_root, 'input', '{}.in'.format(case_id))
        verify_out_file = os.path.join(self.r.root, 'output', '{}.out'.format(case_id))

        out_file = os.path.join(self.r.root, 'output', '{}.ver.out'.format(case_id))
        err_file = os.path.join(self.r.root, 'output', '{}.ver.err'.format(case_id))

        run_args = self.module.run(validate=(verify_inn_file, verify_out_file))
        run_command = Command(run_args, None, out_file, err_file)
        run_result = run_command.run()

        # run error
        if run_result.returncode != 0:
            info = dict()
            info['result'] = JobCode.WRONG_OUTPUT
            info['comparison'] = tryjson(out_file)
            Logger.instance().debug('    {} wrong output[S]'.format(case_id))
            remove_empty(out_file)
            remove_empty(err_file)
            return info
        else:
            info = dict()
            info['result'] = JobCode.CORRECT_OUTPUT
            info['comparison'] = tryjson(out_file)
            Logger.instance().debug('    {} correct output[S]'.format(case_id))
            remove_empty(out_file)
            remove_empty(err_file)
            return info
