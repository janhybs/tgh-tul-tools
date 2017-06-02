#!/usr/bin/python
# -*- coding: utf-8 -*-
# author:   Jan Hybs
# 

runner_sleep =       3  # 5 sec sleep
watchdog_sleep =    30  # 30 sec sleep

runner_pidfile =    '/tmp/tgh-runner.pid'
watchdog_pidfile =  '/tmp/tgh-watchdog.pid'
run_service =       'tgh-service restart'

max_wait_time =     30  # maximum wait time for entire students job in sec
wait_timescale =     2  # multiplicative factor to wait extra long time to get 
                        # return codes 
                        #   - TIMEOUT_CORRECT_OUTPUT
                        #   - TIMEOUT_WRONG_OUTPUT
