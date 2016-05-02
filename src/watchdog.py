#!/usr/bin/python
# -*- coding: utf-8 -*-
# author:   Jan Hybs

from utils.daemon import Daemon
from subprocess import Popen, PIPE
from optparse import OptionParser
import os, sys, getpass, time

from config import watchdog_pidfile, runner_pidfile, run_service


class TGHWatchDogDaemon(Daemon):
    def __init__(self, file_to_watch, name, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        super(TGHWatchDogDaemon, self).__init__(name, pidfile, stdin, stdout, stderr)
        self.file_to_watch = file_to_watch

    def run(self):
        while True:
            # if file exists, service is not probably running
            if not os.path.isfile(self.file_to_watch):
                print 'File {self.file_to_watch} does not exists. Running service command:' .format(self=self)

                # start service
                print 'running "{}"'.format(run_service)
                process = Popen(run_service, shell=True)
                out, err = process.communicate()
                print 'output: '
                print out, err

            # sleep for 5 sec
            print 'sleeping'
            time.sleep(15)


if __name__ == "__main__":
    parser = OptionParser()
    parser.set_usage("%prog start|stop|restart|debug")
    options, args = parser.parse_args()

    print 'Running as "{}"'.format(getpass.getuser())
    print 'Watching file "{}"'.format(runner_pidfile)

    # daemon = TGHWatchDogDaemon(runner_pidfile, pidfile=watchdog_pidfile, name='TGH-watchdog-D', stdout='/home/jan-hybs/Dokumenty/projects/tgh-tul-tools/src/out.log')
    l = '/home/jan-hybs/Dokumenty/projects/tgh-tul-tools/src/out.log'
    daemon = TGHWatchDogDaemon(runner_pidfile, pidfile=watchdog_pidfile, name='TGH-watchdog-D', stdout=l, stderr=l)
    if not args:
        parser.print_usage()
        exit(1)
        
    action = args[0]
    method = getattr(daemon, action)
    if method:
        method()
        exit(0)
    parser.print_usage()
    exit(1)

