#!/usr/bin/python
# -*- coding: utf-8 -*-
# author:   Jan Hybs

import os, sys, json
from jobs.job_processing import DynamicLanguage, Command, LangMap
from utils.globals import ProcessException, remove_empty, compare, read, tryjson, Config, ensure_path
from utils.logger import Logger


class JobResult(object):
    OK = 0
    RUN_OK = 0

    CORRECT_OUTPUT = 1
    WRONG_OUTPUT = 3

    COMPILE_ERROR = 10
    RUN_ERROR = 20
    UNKNOWN_ERROR = 100

    _dict1 = dict()
    _dict2 = dict()

    @staticmethod
    def reverse1(code):
        if not JobResult._dict1:
            JobResult._dict1[JobResult.CORRECT_OUTPUT] = 'A'
            JobResult._dict1[JobResult.WRONG_OUTPUT] = 'W'

            JobResult._dict1[JobResult.UNKNOWN_ERROR] = 'E'
            JobResult._dict1[JobResult.COMPILE_ERROR] = 'E'
            JobResult._dict1[JobResult.RUN_ERROR] = 'E'

            JobResult._dict1[JobResult.RUN_OK] = 'O'
            JobResult._dict1[JobResult.OK] = 'O'

        return JobResult._dict1.get(code, 'E')

    @staticmethod
    def reverse2(code):
        if not JobResult._dict2:
            JobResult._dict2[JobResult.CORRECT_OUTPUT] = 'OK'
            JobResult._dict2[JobResult.WRONG_OUTPUT] = 'ER'

            JobResult._dict2[JobResult.UNKNOWN_ERROR] = 'ER'
            JobResult._dict2[JobResult.COMPILE_ERROR] = 'ER'
            JobResult._dict2[JobResult.RUN_ERROR] = 'ER'

            JobResult._dict2[JobResult.RUN_OK] = 'OK'
            JobResult._dict2[JobResult.OK] = 'OK'

        return JobResult._dict2.get(code, 'ER')


class JobControl(object):
    root = None

    @staticmethod
    def process(request):
        """
        :type request: jobs.job_request.JobRequest
        """
        ensure_path(os.path.join(request.root, 'output'), False)
        print os.path.join(request.root, 'output')
        
        if request.reference:
            job = ReferenceJob(request)
        else:
            job = StudentJob(request)

        return job.process()


class StudentJob(object):
    def __init__(self, request):
        """
        :type request: jobs.job_request.JobRequest
        """
        self.r = request
        self.module = None
        self.reference = ReferenceJob(request)
        self.program_root = os.path.join(Config.problems, self.r.problem.id)

    def process(self):
        self.prepare_solution()
        case_id = 0
        results = list()
        for input_spec in self.r.problem.input:
            case_id += 1
            Logger.instance().debug('  {case_id}: {input_spec}'.format(case_id=case_id, input_spec=input_spec))
            if input_spec.dynamic:
                results.extend(
                    self._dynamic(input_spec, case_id)
                )
            else:
                results.append(
                    self._static(input_spec, input_spec.id)
                )
        return results

    def _static(self, input_spec, case_id):
        """
        :type input_spec: jobs.job_request.ProblemInput
        """
        ref_out_file = os.path.join(self.program_root, 'output', '{}.out'.format(case_id))
        inn_file = os.path.join(self.program_root, 'input', '{}.in'.format(case_id))
        out_file = os.path.join(self.r.root, 'output', '{}.out'.format(case_id))
        err_file = os.path.join(self.r.root, 'output', '{}.err'.format(case_id))

        if not os.path.exists(inn_file):
            Logger.instance().warning('    {} Input file does not exists {}'.format(case_id, inn_file))
            info = dict()
            info['id'] = case_id
            info['result'] = JobResult.UNKNOWN_ERROR
            info['duration'] = 0
            info['error'] = '{} Input file does not exists {}'.format(case_id, inn_file)
            return info

        run_args = self.module.run()
        run_command = Command(run_args, inn_file, out_file, err_file)
        run_result = run_command.run()

        # run error
        if run_result.exit != 0:
            info = run_result.info
            info['id'] = case_id
            info['result'] = JobResult.RUN_ERROR
            Logger.instance().debug('    {} error while execution'.format(case_id))
            return info

        # run ok
        info = run_result.info
        info['id'] = case_id
        info['result'] = JobResult.RUN_OK
        remove_empty(err_file)

        # run ref script to test solution's output
        if not self.r.problem.multiple_solution:
            compare_result = self.compare(info, case_id, ref_out_file, out_file)
            return compare_result
        else:
            comp_result = self.reference.test_solution(case_id)
            info['result'] = comp_result['result']
            info['output'] = comp_result['output']
            info['method'] = comp_result['method']

        return info

    def _dynamic(self, input_spec, i):
        """
        :type input_spec: jobs.job_request.ProblemInput
        """
        cases = input_spec.cases
        result = list()

        for c in range(1, cases + 1):
            case_id = 'case_{}.{}'.format(i, c)
            # generating reference output
            result.append(self._static(input_spec, case_id))
        return result

    def compare(self, info, case_id, a, b):
        info['id'] = case_id
        try:
            compare_result = compare(a, b)
            if compare_result:
                info['result'] = JobResult.CORRECT_OUTPUT
                info['method'] = 'file-comparison'
                Logger.instance().debug('    {} correct output[F]'.format(case_id))
                return info
            else:
                info['result'] = JobResult.WRONG_OUTPUT
                info['method'] = 'file-comparison'
                Logger.instance().debug('    {} wrong output[F]'.format(case_id))
                return info
        except Exception as e:
                info['result'] = JobResult.UNKNOWN_ERROR
                info['method'] = 'file-comparison'
                info['error'] = str(e)
                info['details'] = 'Error during file comparison'
                return info

    def prepare_solution(self):
        if self.module is not None:
            return self.module

        compile_out = os.path.join(self.r.root, 'compile.out')
        compile_err = os.path.join(self.r.root, 'compile.err')

        self.module = LangMap.get(self.r.lang.id)(self.r)

        compile_command = Command(self.module.compile(), None, compile_out, compile_err)
        compile_result = compile_command.run()

        if compile_result.exit != 0:
            info = compile_result.info
            info['result'] = JobResult.COMPILE_ERROR
            raise ProcessException(info)

        # clean up
        remove_empty(compile_out)
        remove_empty(compile_err)

        return self.module


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
        self.prepare_reference()
        results = list()
        case_id = 0
        for input_spec in self.r.problem.input:
            case_id += 1
            Logger.instance().debug('  {case_id}: {input_spec}'.format(case_id=case_id, input_spec=input_spec))
            if input_spec.dynamic:
                results.extend(
                    self._dynamic(input_spec, case_id)
                )
            else:
                results.append(
                    self._static(input_spec, input_spec.id)
                )
        return results

    def _dynamic(self, input_spec, i):
        """
        :type input_spec: jobs.job_request.ProblemInput
        """
        cases = input_spec.cases
        result = list()

        for c in range(1, cases + 1):
            case_id = 'case_{}.{}'.format(i, c)
            inn_file = None
            out_file = os.path.join(self.program_root, 'input', '{}.in'.format(case_id))
            err_file = os.path.join(self.program_root, 'input', '{}.err'.format(case_id))

            run_args = self.module.run(prepare=input_spec.problem_size, random=input_spec.random)
            run_command = Command(run_args, inn_file, out_file, err_file)
            run_result = run_command.run()

            # run error
            if run_result.exit != 0:
                info = run_result.info
                info['id'] = case_id
                info['result'] = JobResult.RUN_ERROR
                result.append(info)
                Logger.instance().debug('    {} error while generating input file'.format(case_id))
                continue

            # run ok
            info = run_result.info
            info['result'] = JobResult.RUN_OK
            info['id'] = case_id
            result.append(info)
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
        inn_file = os.path.join(self.program_root, 'input', '{}.in'.format(case_id))
        out_file = os.path.join(self.program_root, 'output', '{}.out'.format(case_id))
        err_file = os.path.join(self.program_root, 'output', '{}.err'.format(case_id))

        run_args = self.module.run()
        run_command = Command(run_args, inn_file, out_file, err_file)
        run_result = run_command.run()

        # run error
        if run_result.exit != 0:
            info = run_result.info
            info['result'] = JobResult.RUN_ERROR
            info['id'] = case_id
            Logger.instance().debug('    {} error while generating output file'.format(case_id))
            return info

        # run ok
        info = run_result.info
        info['result'] = JobResult.RUN_OK
        info['id'] = case_id
        remove_empty(err_file)
        Logger.instance().debug('    {} output file created'.format(case_id))

        return info

    def prepare_reference(self):
        """
        :rtype : DynamicLanguage
        """
        if self.module is not None:
            return self.module

        compile_out = os.path.join(self.program_root, 'compile.out')
        compile_err = os.path.join(self.program_root, 'compile.err')

        self.module = DynamicLanguage(self.r)

        compile_command = Command(self.module.compile(), None, compile_out, compile_err)
        compile_result = compile_command.run()

        if compile_result.exit != 0:
            info = compile_result.info
            info['result'] = JobResult.COMPILE_ERROR
            raise ProcessException(info)

        # clean up
        remove_empty(compile_out)
        remove_empty(compile_err)

        return self.module

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
        if run_result.exit != 0:
            info = run_result.info
            info['result'] = JobResult.WRONG_OUTPUT
            info['method'] = 'script'
            info['output'] = tryjson(out_file)
            Logger.instance().debug('    {} wrong output[S]'.format(case_id))
            remove_empty(out_file)
            remove_empty(err_file)
            return info
        else:
            info = run_result.info
            info['result'] = JobResult.WRONG_OUTPUT
            info['method'] = 'script'
            info['output'] = tryjson(out_file)
            Logger.instance().debug('    {} correct output[S]'.format(case_id))
            remove_empty(out_file)
            remove_empty(err_file)
            return info
