#!/usr/bin/env python
# -*- coding: utf-8 -*-
# docker centos mod pyt

import sys
import os
import threading
from subprocess import Popen, PIPE
import json
import importlib
import datetime
import time
import getpass
from optparse import OptionParser
from daemon import Daemon

parser = OptionParser()
parser.add_option("-f", "--force", dest="force", action="store_true", default=False,
                  help="start daemon even while running as root")
parser.add_option("-d", "--dir", dest="dir_to_watch", help="dir path which will be watched", metavar="DIR")
parser.add_option("-c", "--cfg", dest="languages", help="path to json file containing paths to programming languages",
                  metavar="CFG")
parser.set_usage("%prog start|stop|restart --dir DIRNAME [options]")

MAX_DURATION = 60
DIFF_OUTPUT = {
    '0': 'spravny-vystup',
    '1': 'chybny-vystup',
    '2': 'zadny-vystup',
    '3': 'chyba-pri-behu',
    '4': 'chybny-vystup',
    '5': 'prekrocen-casovy-limit'
}
DIFF_OUTPUT_SHORT = {
    '0': 'OK',  # accepted
    '1': 'ER',  # error
    '2': 'CO',  # compilation error
    '3': 'ER',  # run error
    '4': 'WR',  # wrong answer
    '5': 'TI'  # timeout
}
RESULT_LETTER = {
    '0': 'A',  # accepted
    '1': 'E',  # error
    '2': 'E',  # compilation error
    '3': 'E',  # run error
    '4': 'W'  # wrong answer
}

LANGUAGES = {
    "python": "python",  # python 27 path
    "gmcs": "gmcs",  # cs compiler path
    "mono": "mono",  # cs executor path
    "javac": "javac",  # java compiler path
    "java": "java",  # java executor path
    "g++": "g++",  # c++ compiler path
    "gcc": "gcc",  # c compiler path
    "fpc": "fpc"  # pascal compiler path
}


class Timer(object):
    # def __init__(self, name=None):
    # self.name = name
    #     self.duration = None
    #
    # def __enter__(self):
    #     self.tstart = time.time()
    #
    # def __exit__(self, type, value, traceback):
    #     if self.name:
    #         print '[%s]' % self.name,
    #     print 'Elapsed: %s' % (time.time() - self.tstart)

    def __init__(self, name=None):
        self.time = 0
        self.name = name
        self.duration = 0

    def tick(self):
        self.time = time.time()

    def tock(self):
        self.duration = time.time() - self.time

    def __repr__(self):
        if self.name is None:
            return "{:1.6f}".format(self.duration)
        return "{:s}: {:1.6f}".format(self.name, self.duration)


class CommandResult(object):
    def __init__(self, exit=None, error=None, cmd=None):
        self.exit = exit
        self.error = error
        self.cmd = cmd

    def isempty(self):
        return self.exit is None

    def isok(self):
        return self.exit == 0

    def isnotwrong(self):
        return self.isok() or self.isempty()

    def __repr__(self):
        return "[CommandResult exit:{:d} {:s} {}]".format(self.exit, self.error, self.cmd)

    @staticmethod
    def loadfile(path, mode='r'):
        if not os.path.isfile(str(path)):
            return ''

        with open(path, mode) as f:
            return f.read()


class Command(object):
    def __init__(self, args, inn=None, out=None, err=None):
        # args.append ("exit") # terminate just in case
        self.command = '; '.join(args)
        self.timer = Timer(self.command)
        self.process = None
        self.fatal_error = None

        self.shell = True
        self.inn = self.inn_path = inn
        self.out = self.out_path = out
        self.err = self.err_path = err

        self.duration = 0
        self.timeout = MAX_DURATION
        self.terminated = False

    def open_files(self):
        self.inn = PIPE if self.inn is None else open(self.inn, "rb")
        self.out = PIPE if self.out is None else open(self.out, "wb")
        self.err = PIPE if self.err is None else open(self.err, "wb")

    def close_files(self):
        if not self.inn is PIPE:
            self.inn.close()
        if not self.out is PIPE:
            self.out.close()
        if not self.err is PIPE:
            self.err.close()

    def __repr__(self):
        return "[Command: {} ({:d} s)]".format(self.command, self.timeout)

    def run(self, timeout=MAX_DURATION):
        self.timeout = timeout
        if not self.command:
            return CommandResult()

        print self
        self.open_files()

        def target():
            try:
                self.process = Popen([self.command], stdout=self.out, stderr=self.err, stdin=self.inn, shell=self.shell)
                self.process.communicate()
            except Exception as e:
                # if shell is False exception can be thrown
                print 'Fatal error'
                print e
                self.fatal_error = str(e) + "\n"
                self.fatal_error += str(self) + "\n"
                if hasattr(e, 'child_traceback'):
                    self.fatal_error += str(e.child_traceback)

        # create thread
        thread = threading.Thread(target=target)

        # run thread
        self.timer.tick()
        thread.start()
        thread.join(self.timeout)
        self.timer.tock()

        # kill longer processes
        if thread.is_alive():
            self.process.terminate()
            self.terminated = True
            thread.join()


        # files
        self.close_files()

        # on error return error
        if self.fatal_error is not None:
            return CommandResult(1, str(self.fatal_error), self)

        if self.terminated:
            return CommandResult(5, "Process was terminated (did not finish in time)", self)


        # return process if no FATAL error occurred
        err_msg = (CommandResult.loadfile(self.err_path) + CommandResult.loadfile(self.out_path)).lstrip()
        return CommandResult(self.process.returncode, err_msg, self)


def get_module(cls):
    return importlib.import_module("langs." + cls)


def change_ext(filename, new_ext):
    (root, ext) = os.path.splitext(os.path.basename(filename))
    return root + new_ext


def mkdirs(path, mode):
    oldmask = os.umask(0)
    os.makedirs(path, mode)
    os.umask(oldmask)


def compare(a, b):
    result = None
    eof = False
    with open(a, 'rb') as f1, open(b, 'rb') as f2:
        while True:

            # read lines
            l1 = f1.readline()
            l2 = f2.readline()
            eof = l1 == ''

            # right strip white chars (\r\n, \n, \r, max differ)
            l1 = l1.rstrip()
            l2 = l2.rstrip()

            if l1 == '' and l2 == '':
                result = 0

                if eof:
                    break

            if l1 != l2:
                result = 1
                break
    return result


def enc(v):
    return v.encode('utf-8')


def process(cfg):
    # print cfg['lang']['id']
    # print cfg
    # print '------------------------------------'

    # dynamically get module
    lang = cfg['lang']['id']
    problem = cfg['problem']['id']
    root = cfg['root']
    result_file = cfg['result']
    main_file = os.path.join(root, cfg['filename'])

    try:
        mod = get_module(lang)
    except Exception as e:
        print e



    # get dirs
    inn_dir = os.path.join(root, 'input')
    ref_out_dir = os.path.join(root, 'ref')
    res_out_dir = os.path.join(root, 'output')
    res_err_dir = os.path.join(root, 'error')

    # get files
    inn_files = cfg['problem']['input']
    ref_out_files = [os.path.join(ref_out_dir, inn['id'] + '.out') for inn in inn_files]
    res_out_files = [os.path.join(res_out_dir, inn['id'] + '.out') for inn in inn_files]
    res_err_files = [os.path.join(res_err_dir, inn['id'] + '.err') for inn in inn_files]
    # inn_files     = [os.path.join (inn_dir,     inn['id'] + '.in')  for inn in inn_files]
    for inn in inn_files:
        inn['path'] = os.path.join(inn_dir, inn['id'] + '.in')

    # if not os.path.exists(res_out_dir):
    # mkdirs (res_out_dir, 0o775)
    #
    # if not os.path.exists(res_err_dir):
    #     mkdirs (res_err_dir, 0o775)

    exec_res = []
    diff_res = []
    result_msg = ""
    result_msg += "{:12s} {} ({})\n".format('uloha', enc(cfg['problem']['name']), problem)
    result_msg += "{:12s} {}\n".format('jazyk', lang)
    result_msg += "{:12s} {}\n".format('student', cfg['user']['username'])
    result_msg += "{:12s} {}\n".format('datum', datetime.datetime.now())
    result_msg += "{:12s} {}.\n".format('pokus', cfg['attempt'])

    result_msg += '\n'

    errors = []
    outputs = []


    # compilation
    comp_cmd = mod.compile(main_file, cfg)
    comp_res = comp_cmd.run(MAX_DURATION)
    cur_exec_res = None

    if comp_res.isnotwrong():

        # execution on all input files
        for i in range(len(inn_files)):
            # run

            print inn_files[i]
            cur_exec_cmd = mod.run(comp_res, main_file, cfg, inn_files[i]['path'], res_out_files[i], res_err_files[i])
            cur_exec_res = cur_exec_cmd.run(inn_files[i]['time'])

            # append details
            exec_res.append(cur_exec_res.exit)
            errors.append(CommandResult.loadfile(res_err_files[i]))

            result_string_short = 'ER'
            result_string_long = 'Error'
            # compare outputs
            if cur_exec_res.isok():
                cur_diff_res = compare(res_out_files[i], ref_out_files[i])
                result_string_short = DIFF_OUTPUT_SHORT[str(cur_diff_res)]
                result_string_long = DIFF_OUTPUT[str(cur_diff_res)]
            else:
                cur_diff_res = 2
                try:
                    result_string_short = DIFF_OUTPUT_SHORT[str(cur_exec_res.exit)]
                except Exception:
                    result_string_short = 'ER'

                try:
                    result_string_long = DIFF_OUTPUT[str(cur_exec_res.exit)]
                except Exception:
                    result_string_long = 'Error'

            outputs.append({'path': os.path.basename(res_out_files[i]), 'exit': max([cur_exec_res.exit, cur_diff_res])})
            diff_res.append(cur_diff_res)

            result_msg += "[{:2s}] {:2d}. sada: {:20s} {:6.3f} ms {:s} \n".format(
                result_string_short, i + 1,
                os.path.basename(res_out_files[i]),
                cur_exec_res.cmd.timer.duration * 1000,
                result_string_long
            )

    if comp_res.isnotwrong() and max(exec_res) == 0 and max(diff_res) == 0:
        result_msg += "\nodevzdane reseni je spravne\n"
        res_code = 0
    else:
        result_msg += "\nodevzdane reseni je chybne:\n"
        res_code = 1
        if not comp_res.isnotwrong():
            result_msg += "\tchyba pri kompilaci({}):\n{}\n".format(comp_res.exit, comp_res.error)
            res_code = 2

        if len(exec_res) and max(exec_res) != 0:
            result_msg += "\tchyba pri behu programu: kod ukonceni {:d}\n\t".format(max(exec_res))
            result_msg += "\n\t".join(errors)
            res_code = 3

        if len(diff_res) and max(diff_res) != 0:
            result_msg += "\tchybny vystup"
            res_code = 4

    result = {'exit': res_code, "outputs": outputs, 'suffix': RESULT_LETTER[str(res_code)], 'result': result_msg}
    return (result_file, result)


class TGHCheckDaemon(Daemon):
    def set_args(self, dir_to_watch, allow_root):
        self.dir_to_watch = dir_to_watch
        self.allow_root = allow_root

    def run(self):
        while True:
            jobs = os.listdir(self.dir_to_watch)
            print jobs
            for current_job in jobs:
                config_path = os.path.join(self.dir_to_watch, current_job, 'config.json')
                service_alive = os.path.join(self.dir_to_watch, current_job, 'service.alive')

                if os.path.exists(config_path) and os.path.isfile(config_path):
                    try:
                        with open(config_path, 'r') as f:
                            config = json.load(f, encoding="utf-8")
                            config['languages'] = LANGUAGES
                    except Exception as e:
                        print e

                    if config:
                        print 'valid job detected'
                        # remove flag as soon as possible
                        os.remove(service_alive)
                        try:
                            (result_file, result) = process(config)
                            print result['result']
                            # write result
                            with open(result_file, 'w') as f:
                                json.dump(result, f, indent=True)
                            os.chmod(result_file, 0o666)
                        except Exception as e:
                            print e

                        # delete path as confirmation job is done
                        os.remove(config_path)
                        # sys.exit (0)
            time.sleep(2)


# su - tgh-worker -c "python /var/www/html/443/scripts/process.py start /home/jan-hybs/PycharmProjects/TGH-testing-server/443/jobs"
def usage(msg=None):
    if msg is not None:
        print msg
    print "usage: %s start|stop|restart dir_to_watch [--force]" % sys.argv[0]
    sys.exit(2)


if __name__ == "__main__":
    (options, args) = parser.parse_args()

    if options.dir_to_watch is None or not args:
        parser.print_usage()
        sys.exit(1)

    options.dir_to_watch = os.path.abspath(options.dir_to_watch)

    print 'Running as "{}"'.format(getpass.getuser())
    print 'Watching dir "{}"'.format(options.dir_to_watch)

    if (getpass.getuser() == 'root' or os.getuid() == 0) and options.force is False:
        print 'You cannot run this daemon as root'
        print 'Use command su - <username> to run this daemon or add command --force if you are certain'
        sys.exit(1)

    if options.languages is not None:
        with open(options.languages) as f:
            LANGUAGES = json.load(f)

    daemon = TGHCheckDaemon(pidfile='/tmp/tgh-runner.pid', name='TGH-Runner-D')

    if args[0] == 'start':
        daemon.set_args(options.dir_to_watch, options.force)
        daemon.start()
    elif args[0] == 'restart':
        daemon.set_args(options.dir_to_watch, options.force)
        daemon.restart()
    elif args[0] == 'stop':
        daemon.stop()
    elif args[0] == 'debug':
        daemon.set_args(options.dir_to_watch, options.force)
        daemon.run()
    sys.exit(0)

