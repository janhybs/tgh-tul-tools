#!/usr/bin/python
# -*- coding: utf-8 -*-
# author:   Jan Hybs
import json

import os
import sys
import time
from jobs.job_control import JobControl
from jobs.job_request import JobRequest

from utils.daemon import Daemon
from utils.globals import Langs, Problems


class TGHProcessor(Daemon):
    def __init__(self, watch_dir='.', root='.'):
        super(TGHProcessor, self).__init__(name='tgh-processor', pidfile='/tmp/tgh-processor')
        self.watch_dir = watch_dir
        self.root = os.path.abspath(root)
        self.config_dir = os.path.join(root, 'config')

    def get_jobs(self, filter=None):
        """

        :rtype : list[jobs.job_request.JobRequest]
        """
        jobs = os.listdir(self.watch_dir)
        jobs = [j for j in jobs if j.startswith('job-')]
        jobs = [os.path.join(self.watch_dir, j) for j in jobs]
        jobs = [j for j in jobs if os.path.isdir(j)]
        jobs = [j for j in jobs if 'config.json' in os.listdir(j)]

        json_jobs = [JobRequest(os.path.join(j, 'config.json')) for j in jobs]

        return json_jobs

    def run(self):
        Langs.init(os.path.join(self.config_dir, 'langs.json'))
        Problems.init(os.path.join(self.config_dir, 'problems.json'))
        JobControl.root = self.root
        # while True:
        jobs = self.get_jobs()
        for job in jobs:
            JobControl.process(job)

            # time.sleep(5)


def usage(msg=''):
    if msg: print msg
    print 'usage: main.py start|stop|restart|debug <watch_dir> <root>'
    sys.exit(1)

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 1:
        usage('Specify action!')

    action = str(args[0]).lower()
    if action.lower() not in ('start', 'stop', 'restart', 'debug'):
        usage('Invalid action')

    if action in ('start', 'restart', 'debug'):
        if len(args) < 2: usage('Missing <watch_dir> arg')
        if len(args) < 3: usage('Missing <root> arg')
        watch_dir = os.path.abspath(args[1])
        root = os.path.abspath(args[2])

        processor = TGHProcessor(watch_dir=watch_dir, root=root)
        if action == 'debug':
            print 'Debugging service'
            processor.run()
            sys.exit(0)

        if action == 'restart':
            print 'Stopping service...'
            processor.stop()
        print 'Watching dir "{:s}"'.format(watch_dir)
        processor.start()
        sys.exit(0)

    if action == 'stop':
        processor = TGHProcessor()
        print 'Stopping service...'
        processor.stop()
        sys.exit(0)

