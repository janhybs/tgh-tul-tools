#!/usr/bin/python
# -*- coding: utf-8 -*-
# author:   Jan Hybs

from optparse import OptionParser
from random import randint
import random
import os, sys, json


parser = OptionParser()
parser.add_option("-p", "--program-size", dest="size", help="program size", default=None)
parser.add_option("-v", "--validate", action="store_true", dest="validate", help="program size", default=None,)
parser.add_option("-r", dest="rand", action="store_true", default=False, help="Use non-deterministic algo")

options, args = parser.parse_args()

random.seed(1234)

if options.rand:
    random.seed()

if options.size is not None:
    for i in range(int(options.size)):
        print randint(1, 100)
    sys.exit(0)

if options.validate is not None:
    in_file = [int(x) for x in open(args[0], 'r').read().split() if x]
    out_ref = sum(in_file)
    try:
        out_file = int(open(args[1], 'r').read().strip())
        
        if out_file == out_ref:
            result = {
                'result': 'ok',
                'difference': 0
            }
            print json.dumps(result, indent=4)
            sys.exit(0)
        else:
            result = {
                'result': 'error',
                'difference': abs(out_ref - out_file)
            }
            print json.dumps(result, indent=4)
            sys.exit(1)
    except Exception as e:
        result = {
            'result': 'error',
            'details': 'invalid output file structure',
            'difference': -1
        }
        print json.dumps(result, indent=4)
        sys.exit(1)

# normal algo
n = list()
for line in sys.stdin:
    n.append(int(line.strip()))

print sum(n)