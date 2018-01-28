# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2018-01-28 13:17:14 alex>
#
# --------------------------------------------------------------------
# PiProbe
# Copyright (C) 2016-2017  Alexandre Chauvin Hameau <ach@meta-x.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# --------------------------------------------------------------------

"""
scheduler for the jobs
"""

import time
import random
import logging
import re

# import pprint

class sched(object):
    """
    scheduler class
    """

    # ------------------------------------
    def __init__(self):
        """
        constructor, calls once the step() method
        """
        self.aSchedJobs = []
        self.clean()

    # ------------------------------------
    def add(self, name, iFreq, func, args=None, startIn=0, sLock="none"):
        """add a job by calling the addExtended
        """
        self.addExtended(name, iFreq, None, func, args, startIn, sLock)

    # ------------------------------------
    def addExtended(self, name, iFreq, schedData, func, args=None, startIn=0, sLock="none"):
        """
        add a job to the schedule with extended information
        :param name: name of the job, for information
        :param iFreq: frequency in seconds
        :param schedData: extended data for scheduling
        :param func: function to call each iteration
        :param args: argument to pass to the job
        :param startIn: next execution of the job in
           0: iFreq
           1: now+1
           2: random between 5s and iFreq
           3: now+3
        :param sLock: is this process exclusive local or global, default not
        """

        iNextExec = time.time()

        _r = random.SystemRandom()

        if startIn == 0:
            iNextExec += iFreq
        else:
            if startIn == 1:
                iNextExec += 1
            else:
                if startIn == 2:
                    if iFreq < 5:
                        iNextExec += 5
                    else:
                        iNextExec += int(_r.random() * (iFreq-5)) + 5
                else:
                    if startIn == 3:
                        iNextExec += 3

        logging.info("add job {} : freq = {}, next = {:0.2f}".format(name, iFreq, iNextExec-time.time()))

        # lock ?
        if sLock not in ["check", "none", "local", "global"]:
            sLock = "none"

        self.aSchedJobs.append({'freq' : iFreq,
                                'schedule' : schedData,
                                'func': func,
                                'args': args,
                                'lock': str(sLock),
                                'nextExec' : iNextExec})

    # ------------------------------------
    def addAt(self, name, iFreq, func, args=None, atTime=0):
        """
        add a job to the schedule, will run once
        :param name: name of the job, for information
        :param iFreq: frequency in seconds
        :param func: function to call each iteration
        :param args: argument to pass to the job
        :param atTime: time for first iteration
        """

        now = time.time()

        if atTime < now:
            assert False, "at time prior to now"

        logging.info("add at job {} : freq = {}, next = {:0.3f}".format(name, iFreq, atTime-now))

        self.aSchedJobs.append({'freq' : iFreq,
                                'func': func,
                                'args': args,
                                'nextExec' : atTime})

    # ------------------------------------
    @classmethod
    def str2atTime(cls, s):
        """ convert a time string to a atTime usable in addAt()
        HH:MM in 24h00 format
        """

        # print s

        (tm_year, tm_mon, tm_day, tm_hour, tm_min, tm_sec, tm_wday, tm_yday, tm_isdst) = time.localtime()

        r = re.match(r"(\d\d):(\d\d)", s)
        if r != None:
            hour = int(r.group(1))
            minute = int(r.group(2))

            if hour < tm_hour:
                # tomorow ?
                tm_day += 1
                tm_hour = hour
                tm_min = minute
            else:
                if hour == tm_hour:
                    if minute < tm_min:
                        # tomorow
                        tm_day += 1
                        tm_hour = hour
                        tm_min = minute
                    else:
                        # today
                        tm_hour = hour
                        tm_min = minute
                else:
                    tm_hour = hour
                    tm_min = minute
                
        return time.mktime((tm_year, tm_mon, tm_day, tm_hour, tm_min, tm_sec, tm_wday, tm_yday, tm_isdst))

    # ------------------------------------
    def step(self, objProbe=None):
        """
        run a step and return the delay till next step
        returns the wait time in seconds

        if no job is in the queue, returns 30
        if next job in more than a second, returns next sched delta time
        if next job is within the sec, wait for the delay and launch job,
           then returns 0
        """
        # if len(self.aSchedJobs) == 0:
        if not self.aSchedJobs:
            return 30

        # sort jobs by next iteration time
        self.aSchedJobs.sort(key=lambda item: item['nextExec'], reverse=True)

        # pick up the next one (since ordered)
        nextJob = self.aSchedJobs[-1:][0]

        # is the time approaching ?
        fNextSched = nextJob['nextExec'] - time.time()

        # in the next second ?
        if fNextSched > 1:
            return fNextSched
        else:
            bExec = True
            minNextIter = time.time()*2

            # do we need to execute the job now ?
            if nextJob['schedule'] != None:
                bExec = False
                schedData = nextJob['schedule']

                (tm_year, tm_mon, tm_day, _, _, _, tm_wday, tm_yday, tm_isdst) = time.localtime()

                for schedEntry in schedData:
                    if not schedEntry.__contains__('type'):
                        logging.error("schedule time without type information, check config at server side")
                        continue

                    if schedEntry['type'] == "inside":
                        timeEnable = 0
                        timeDisable = 0

                        r = re.match(r"(\d\d):(\d\d):(\d\d)", schedEntry['enable'])
                        if r is None:
                            logging.error("schedule enable format error, should be HH:MM:SS and is {}".format(schedEntry['enable']))
                        else:
                            h = int(r.group(1))
                            m = int(r.group(2))
                            s = int(r.group(3))

                            timeEnable = time.mktime((tm_year, tm_mon, tm_day,
                                                      h, m, s,
                                                      tm_wday, tm_yday, tm_isdst))

                            # print(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(timeEnable)))

                        r = re.match(r"(\d\d):(\d\d):(\d\d)", schedEntry['disable'])
                        if r is None:
                            logging.error("schedule disable format error, should be HH:MM:SS and is {}".format(schedEntry['enable']))
                        else:
                            h = int(r.group(1))
                            m = int(r.group(2))
                            s = int(r.group(3))

                            timeDisable = time.mktime((tm_year, tm_mon, tm_day,
                                                       h, m, s,
                                                       tm_wday, tm_yday, tm_isdst))

                            # print(time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(timeDisable)))

                        # are we in this zone
                        now = time.time()
                        #print(now - timeDisable)
                        #print(now - timeEnable)

                        if now >= timeEnable and now <= timeDisable:
                            logging.info("schedule: in zone, exec planned")
                            bExec = True
                            break
                        else:
                            # is next iteration today ?
                            if now < timeEnable:
                                logging.debug("schedule is before now")
                                if timeEnable-now < minNextIter:
                                    minNextIter = timeEnable

                            # check tomorrow
                            if now > timeDisable:
                                logging.debug("schedule is after now")
                                _nextTime = timeEnable + 3600*24
                                if _nextTime < minNextIter:
                                    minNextIter = _nextTime

            _r = random.SystemRandom()

            if bExec:
                if fNextSched > 0:
                    time.sleep(fNextSched)

                # lock handling
                nextJob = self.aSchedJobs[-1]
                
                if nextJob['lock'] == "check":
                    if objProbe.db.checkLock("local"):
                        logging.debug("locked, will try later")
                        return _r.random()

                if nextJob['lock'] == "local":
                    if not objProbe.acquireLocalLock():
                        return _r.random()

                nextJob = self.aSchedJobs.pop()

                # lock handling
                #if nextJob['lock'] == "local":

                nextJob['nextExec'] += nextJob['freq']

                # if probe, tell it is running
                if objProbe != None:
                    objProbe.db.incrRunningProbe()

                if nextJob['args'] is None:
                    nextJob['func']()
                else:
                    nextJob['func'](nextJob['args'])

                # if probe, tell it is not running anymore
                if objProbe != None:
                    objProbe.db.decrRunningProbe()

                if nextJob['lock'] == "local":
                    objProbe.releaseLocalLock()

                self.aSchedJobs.append(nextJob)
                return 0

            else:
                # time is not yet arrived to execute the job
                nextJob = self.aSchedJobs.pop()
                nextJob['nextExec'] = minNextIter + int(_r.random() * (nextJob['freq']))

                logging.info("next iter in {:.0f} secs at {}".format(minNextIter-time.time(),
                                                                     time.strftime("%d/%m/%Y %H:%M:%S",
                                                                                   time.localtime(nextJob['nextExec']))))

                self.aSchedJobs.append(nextJob)
                return 0
                

    # ------------------------------------
    def clean(self):
        """
        suppress all jobs scheduled
        """
        self.aSchedJobs = []
        self.step()
