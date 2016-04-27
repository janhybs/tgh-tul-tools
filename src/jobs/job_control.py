

import os, sys, json
from jobs.job_processing import DynamicLanguage, Command
from jobs.job_request import JobRequest
from utils.globals import ProcessException


class JobResult(object):
    OK = 0
    COMPILE_ERROR = 1
    RUN_ERROR = 2
    RUN_OK = 3
    WRONG_OUTPUT = 4
    CORRECT_OUTPUT = 5


class JobControl(object):
    root = None

    def __init__(self, request):
        """
        :type request: jobs.job_request.JobRequest
        """
        self.r = request
        self.program_root = os.path.join(JobControl.root, 'problems', self.r.problem.id)

    def process(self):
        if self.r.reference:
            return self.process_reference_solution()

    def process_reference_solution(self):
        module = self.prepare_reference()

        i = 0
        for inn in self.r.problem.input:
            i += 1
            if inn.dynamic:
                self.reference_dynamic(module, inn, i)

    def reference_dynamic(self, module, inn, i):
        cases = 1 if inn.random else 10
        result = list()

        for c in range(1, cases+1):
            out_file = os.path.join(self.program_root, 'output', 'case_{}.{}.in'.format(i, c))
            err_file = os.path.join(self.program_root, 'output', 'case_{}.{}.err'.format(i, c))

            run_args = module.run(prepare=c, random=inn.random)
            run_command = Command(run_args, None, out_file, err_file)
            run_result = run_command.run()

            # run error
            if run_result.returncode != 0:
                info = run_result.info
                info['result'] = JobResult.RUN_ERROR
                result.append(info)
                continue

            # run ok
            info = run_result.info
            info['result'] = JobResult.RUN_OK
            result.append(info)




    def prepare_reference_request(self):
        return JobRequest(dict(
            root=self.program_root,
            filename=self.r.problem.ref_script,
            lang_id=self.r.problem.ref_lang,
        ))

    def prepare_reference(self):

        compile_out = os.path.join(self.program_root, 'compile.out')
        compile_err = os.path.join(self.program_root, 'compile.err')

        reference_request = self.prepare_reference_request()
        module = DynamicLanguage(reference_request)

        compile_command = Command(module.compile(), None, compile_out, compile_err)
        compile_result = compile_command.run()

        if compile_result.returncode != 0:
            info = compile_result.info
            info['result'] = JobResult.COMPILE_ERROR
            raise ProcessException(info)

        return module

