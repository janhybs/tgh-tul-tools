#!/usr/bin/python
# -*- coding: utf-8 -*-
# author:   Jan Hybs

import os
import sys
import time

from utils.daemon import Daemon


class TGHProcessor(Daemon):
    def __init__(self, dir_to_watch='.'):
        super(TGHProcessor, self).__init__(name='tgh-processor', pidfile='/tmp/tgh-processor')
        self.dir_to_watch = dir_to_watch

    def get_jobs(self, filter=None):
        jobs = os.listdir(self.dir_to_watch)
        jobs = [j for j in jobs if j]
        jobs = [j for j in jobs if j.startswith('job-')]
        jobs = [os.path.join(self.dir_to_watch, j) for j in jobs]
        jobs = [j for j in jobs if os.path.isdir(j)]
        return jobs



    def run(self):
        while True:
            jobs = self.get_jobs()
            print jobs
            time.sleep(1)


def usage(msg=''):
    if msg: print msg
    print 'usage: main.py start|stop|restart|debug <dir_to_watch>'
    sys.exit(1)

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 1:
        usage('Specify action!')

    action = str(args[0]).lower()
    if action.lower() not in ('start', 'stop', 'restart', 'debug'):
        usage('Invalid action')

    if action == 'start':
        if len(args) < 2: usage('Missing <dir_to_watch> arg')
        dir_to_watch = os.path.abspath(args[1])

        print 'Watching dir "{:s}"'.format(dir_to_watch)
        processor = TGHProcessor(dir_to_watch=dir_to_watch)
        processor.start()
        sys.exit(0)

    if action == 'restart':
        if len(args) < 2: usage('Missing <dir_to_watch> arg')
        dir_to_watch = os.path.abspath(args[1])

        processor = TGHProcessor(dir_to_watch=dir_to_watch)
        print 'Stopping service...'
        processor.stop()
        print 'Watching dir "{:s}"'.format(dir_to_watch)
        processor.start()
        sys.exit(0)

    if action == 'stop':
        processor = TGHProcessor()
        print 'Stopping service...'
        processor.stop()
        sys.exit(0)

    if action == 'debug':
        if len(args) < 2: usage('Missing <dir_to_watch> arg')
        dir_to_watch = os.path.abspath(args[1])

        print 'Debugging service'
        processor = TGHProcessor(dir_to_watch=dir_to_watch)
        processor.run()





    # # processor.start()
    # # processor.stop()
    # processor.run()
    # sys.exit(0)