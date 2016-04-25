#!/usr/bin/python
# -*- coding: utf-8 -*-
# author:   Jan Hybs

from daemon import Daemon
from subprocess import Popen, PIPE
from optparse import OptionParser
import os, sys, getpass, time


class TGHWatchDogDaemon(Daemon):
    def __init__(self, file_to_watch, name, pidfile):
        super(TGHWatchDogDaemon, self).__init__(name, pidfile)
        self.file_to_watch = file_to_watch

    def run(self):
        while True:

            # if file exists, service is not probably running
            if os.path.isfile(self.file_to_watch):

                # start service
                process = Popen('tgh-service start', shell=True, stdout=PIPE)
                out, err = process.communicate()
                print 'output: '
                print out
                print 'error: '
                print err

                # remove file
                os.remove(self.file_to_watch)

            # sleep for 1 minute
            time.sleep(5)


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="file_to_watch", help="file path which will be watched", metavar="DIR")
    parser.set_usage("%prog start|stop|restart --file FILENAME [options]")
    (options, args) = parser.parse_args()

    if options.file_to_watch is None or not args:
        parser.print_usage()
        sys.exit(1)

    options.file_to_watch = os.path.abspath(options.file_to_watch)

    print 'Running as "{}"'.format(getpass.getuser())
    print 'Watching dir "{}"'.format(options.file_to_watch)

    daemon = TGHWatchDogDaemon(options.file_to_watch, pidfile='/tmp/tgh-watchdog.pid', name='TGH-watchdog-D')
    print args
    if args[0] == 'start':
        daemon.start()
    elif args[0] == 'restart':
        daemon.restart()
    elif args[0] == 'stop':
        daemon.stop()
    sys.exit(0)

