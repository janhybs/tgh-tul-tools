__author__ = 'jan-hybs'
from process import Command
import os
import sys

def compile (main_file, cfg):
    root = os.path.dirname (main_file)
    output = os.path.join (root, 'error', 'compile.out')
    errput = os.path.join (root, 'error', 'compile.err')
    commands = [
        "cd '{:s}'".format (root),
        "{:s} '{:s}'".format (cfg['languages']['gmcs'], main_file)
    ]
    cmd = Command (commands, inn=None, out=output, err=errput)

    return cmd

def run (comp_res, main_file, cfg, inn, out, err):
    (root, ext) = os.path.splitext (main_file)
    exe_name = root + '.exe'
    commands = [
        "{:s} {:s}".format (cfg['languages']['mono'], exe_name)
    ]
    print "cmds: "+str(commands)
    cmd = Command (commands, inn, out, err)

    return cmd
