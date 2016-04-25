__author__ = 'jan-hybs'
from process import Command, CommandResult
import sys
def compile (main_file, cfg):
    return Command([])

def run (comp_res, main_file, cfg, inn, out, err):
    commands = [
        "{:s} '{:s}'".format (cfg['languages']['python'], main_file)
    ]
    cmd = Command (commands, inn, out, err)

    return cmd