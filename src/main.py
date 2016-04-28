#!/usr/bin/python
# -*- coding: utf-8 -*-
# author:   Jan Hybs
import json

import os
import sys
from jobs.job_control import JobControl, JobResult
from jobs.job_request import JobRequest
from utils import plucklib

from utils.daemon import Daemon
from utils.globals import Langs, Problems, ProcessException, Config, ensure_path
from utils.logger import Logger
from subprocess import call, check_output


class TGHProcessor(Daemon):
    def __init__(self, config_json='.'):
        super(TGHProcessor, self).__init__(name='tgh-processor', pidfile='/tmp/tgh-processor')

        with open(config_json, 'r') as fp:
            self.config = json.load(fp)

        Config.watch_dir = self.config['jobs']
        Config.problems = self.config['problems']
        Config.data = self.config['data']
        Config.root = self.config['root']
        Config.config_dir = self.config['config']

    def get_jobs(self, filter=None):
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

        # while True:
        jobs = self.get_jobs()
        if jobs:
            Logger.instance().debug('{} job/s found'.format(len(jobs)))
            for job in jobs:
                Logger.instance().debug('Processing {}'.format(job))
                try:
                    result = JobControl.process(job)
                except ProcessException as e:
                    result = dict(
                        result=0
                    )
                    result = [result]
                except Exception as e:
                    result = dict(
                        result=JobResult.UNKNOWN_ERROR,
                        error=str(e),
                    )
                    result = [result]

                # call(['cp', '-r', job.output_root])
                self.save_result(job, result)
                # time.sleep(5)
        else:
            Logger.instance().debug('no jobs found')

    def save_result(self, job, result):
        # copy files
        user_dir = os.path.join(Config.data, job.nameuser, job.problem.id)
        attempts = os.listdir(user_dir)
        ensure_path(user_dir, is_file=False)

        attempt_no = [int(x.split(".")[0]) for x in attempts] or [0]
        next_attempt = max(attempt_no) + 1

        dest_dir = os.path.join(user_dir, '{:02d}-{}-{}'.format(next_attempt, job.username, self.get_result_letter(result)))
        print dest_dir

        # # save results
        # result_json = json.dumps(result, indent=4)
        # with open(job.result_file, 'w') as fp:
        #     fp.write(result_json)

    def get_result_letter(self, result):
        max_result = max(plucklib.pluck(result, 'result'))


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
        config_json = os.path.abspath(args[2])

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

