#!/usr/bin/python
# -*- coding: utf-8 -*-
# author:   Jan Hybs
# 

runner_sleep =      5 # 10 sec sleep
watchdog_sleep =    30 # 30 sec sleep

runner_pidfile =    '/tmp/tgh-runner.pid'
watchdog_pidfile =  '/tmp/tgh-watchdog.pid'
run_service =       'tgh-service restart'

max_wait_time = 60
wait_timescale = 10