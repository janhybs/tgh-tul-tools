#!/usr/bin/python
# -*- coding: utf-8 -*-
# author:   Jan Hybs
import json

import os
import sys
import time
from jobs.job_control import JobControl, JobResult
from jobs.job_request import JobRequest
from utils import plucklib

from utils.daemon import Daemon
from utils.globals import Langs, Problems, ProcessException, Config, ensure_path
from utils.logger import Logger
from subprocess import call

from config import runner_pidfile, runner_sleep


class TGHProcessor(Daemon):
    def __init__(self, config_json=None):
        super(TGHProcessor, self).__init__(name='tgh-processor', pidfile=runner_pidfile)

        if not config_json:
            return

        with open(config_json, 'r') as fp:
            self.config = json.load(fp)

        Config.watch_dir = self.config['jobs']
        Config.problems = self.config['problems']
        Config.data = self.config['data']
        Config.config_dir = self.config['config']

    @staticmethod
    def get_jobs():
        """
        :rtype : list[jobs.job_request.JobRequest]
        """
        jobs = os.listdir(Config.watch_dir)
        jobs = [j for j in jobs if j.startswith('job-')]
        jobs = [os.path.join(Config.watch_dir, j) for j in jobs]
        jobs = [j for j in jobs if os.path.isdir(j)]
        jobs = [j for j in jobs if 'config.json' in os.listdir(j)]
        jobs = [j for j in jobs if '.delete-me' in os.listdir(j)]

        json_jobs = [JobRequest(os.path.join(j, 'config.json')) for j in jobs]

        return json_jobs

    def run(self):
        Langs.init(os.path.join(Config.config_dir, 'langs.json'))
        Problems.init(os.path.join(Config.config_dir, 'problems.json'))

        while True:
            jobs = self.get_jobs()
            if jobs:
                Logger.instance().debug('{} job/s found'.format(len(jobs)))
                for job in jobs:
                    Logger.instance().debug('Processing {}'.format(job))
                    try:
                        # delete file to let PHP now we are working on it
                        os.unlink(job.delete_me_file)
                        result = JobControl.process(job)
                    except ProcessException as e:
                        result = [e.info]
                    except Exception as e:
                        result = dict(
                            result=JobResult.UNKNOWN_ERROR,
                            error=str(e),
                        )
                        result = [result]

                    # add info about result
                    self.save_result(job, result)
            else:
                Logger.instance().debug('no jobs found')
            time.sleep(runner_sleep)

    def save_result(self, job, result):
        # copy files
        user_dir = os.path.join(Config.data, job.nameuser, job.problem.id)
        ensure_path(user_dir, is_file=False)

        attempts = os.listdir(user_dir)
        attempt_no = [int(x.split("-")[0]) for x in attempts] or [0]
        next_attempt = max(attempt_no) + 1
        attempt_dir = '{:02d}-{}-{}'.format(next_attempt, job.username, self.get_result_letter(result))

        dest_dir = os.path.join(user_dir, attempt_dir)
        dest_output_dir = os.path.join(dest_dir)
        ensure_path(dest_output_dir, is_file=False)

        summary = self.get_result_summary(job, result, next_attempt).encode('utf8')
        with open(os.path.join(dest_dir, 'result.txt'), 'wb') as fp:
            fp.write(summary)

        # create global result
        main_result = dict()
        main_result['summary'] = summary
        main_result['attempt_dir'] = dest_dir
        main_result['result'] = result
        main_result['max_result'] = max_result = max(plucklib.pluck(result, 'result'))

        # save results
        result_json = json.dumps(main_result, indent=4)
        with open(job.result_file, 'w') as fp:
            fp.write(result_json)

        call(['cp', '-r', job.output_root, dest_output_dir])
        call(['cp', job.result_file, dest_dir])
        call(['cp', job.main_file, dest_dir])

        return summary, attempt_dir

    @staticmethod
    def get_result_letter(result):
        max_result = max(plucklib.pluck(result, 'result'))
        return JobResult.reverse1(max_result)

    @staticmethod
    def get_result_summary(job, result, attempt_no):
        summary = list()
        summary.append(u'{:15s}{job.problem.name} ({job.problem.id})'.format('uloha', job=job))
        summary.append(u'{:15s}{job.lang.name} ({job.lang.version})'.format('jazyk', job=job))
        summary.append(u'{:15s}{job.username}'.format('student', job=job))
        summary.append(u'{:15s}{job.timestamp}'.format('datum', job=job))
        summary.append(u'{:15s}{}.'.format('pokus', attempt_no))
        summary.append('')

        for res in result:
            res_code = JobResult.reverse2(res['result'])
            summary.append(u'  [{}] sada {res[id]:20s} {res[duration]:6.3f} ms'.format(res_code, res=res, job=job))

            if res['result'] in (JobResult.COMPILE_ERROR, JobResult.RUN_ERROR, JobResult.UNKNOWN_ERROR):
                summary.append('    Error: {res[error]}'.format(res=res))

            if res['result'] in (JobResult.WRONG_OUTPUT, ):
                summary.append('       CHYBNY_VYSTUP na zaklade {}'.format(
                    'porovnani souboru' if res['method'] == 'file-comparison' else 'vysledku referencniho skriptu'
                ))
                if res['method'] != 'file-comparison':
                    summary.append('       {}'.format(json.dumps(res['output'])))

        summary.append('')
        summary.append('')
        grade = 'SPRAVNE' if max(plucklib.pluck(result, 'result')) <= JobResult.CORRECT_OUTPUT else 'CHYBNE'
        summary.append('Odevzdane reseni je ' + grade)

        return '\n'.join(summary)


def usage(msg=''):
    if msg: print msg
    print 'usage: main.py start|stop|restart|debug <config.json>'
    sys.exit(1)

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 1:
        usage('Specify action!')

    action = str(args[0]).lower()
    if action.lower() not in ('start', 'stop', 'restart', 'debug'):
        usage('Invalid action')

    if action in ('start', 'restart', 'debug'):
        if len(args) < 2: usage('Missing <config.json> arg')
        config_json = os.path.abspath(args[1])

        processor = TGHProcessor(config_json=config_json)
        if action == 'debug':
            Logger.instance().info('Debugging service')
            processor.run()
            sys.exit(0)

        if action == 'restart':
            Logger.instance().info('Stopping service...')
            processor.stop()
        Logger.instance().info('Watching dir "{:s}"'.format(Config.watch_dir))
        processor.start()
        sys.exit(0)

    if action == 'stop':
        processor = TGHProcessor()
        Logger.instance().info('Stopping service...')
        processor.stop()
        sys.exit(0)

