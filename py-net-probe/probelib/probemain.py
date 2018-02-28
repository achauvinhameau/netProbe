# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2018-02-28 21:39:57 alex>
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
probemain is the minima probe library class to help creating probes
"""

import os
import sys
import logging
import signal
import time
import sched

sys.path.insert(0, os.getcwd())
from netProbe import ipConf
import database

class probemain(object):
    """
    minimal probe class
    """

    # -----------------------------------------
    def __init__(self, name):
        """
        constructor
        """
        self.ip = None
        self.bNow = False

        self.name = name
        _logFormat = '%(asctime)-15s '+str(name)+' [%(levelname)s] %(filename)s:%(lineno)d - %(message)s'

        # log level
        logLevel = logging.ERROR

        if os.environ.__contains__("PI_LOG_LEVEL"):
            lvl = str(os.environ["PI_LOG_LEVEL"])
            if lvl == 'INFO':
                logLevel = logging.INFO
            if lvl == 'DEBUG':
                logLevel = logging.DEBUG
            if lvl == 'WARNING':
                logLevel = logging.WARNING
            if lvl == 'ERROR':
                logLevel = logging.ERROR

        logging.basicConfig(format=_logFormat,
                            level=logLevel)

        logging.info("starting probe")

        if os.environ.__contains__("PI_DB_TEST"):
            self.db = database.dbTest.dbTest()
            if os.environ.__contains__("PI_SCHED_NOW"):
                self.bNow = True
        else:
            # redis server
            if os.environ.__contains__("PI_REDIS_SRV"):
                self.db = database.dbRedis.dbRedis(os.environ["PI_REDIS_SRV"])
            else:
                self.db = database.dbRedis.dbRedis()

        # create global scheduler
        self.scheduler = sched.sched()
        self.scheduler.clean()

        self.bRunning = True

        self.releaseLocalLock()

        self.pushSimpleLogMsg("INFO", "starting")

        signal.signal(signal.SIGTERM, self.trap_signal)
        signal.signal(signal.SIGINT, self.trap_signal)

    # -----------------------------------------
    def checkNet(self):
        """check IP configuration of probe if no default route !
        """

        logging.info("check if default route is present")
        self.ip = ipConf()

        if self.ip.hasDefaultRoute() is False:
            logging.warning("no default route")

    # -----------------------------------------
    def getEthName(self):
        """get the name of the default route interface
        """

        return self.ip.getIfName()

    # -----------------------------------------
    def getIP(self):
        """returns the ip module

        """
        return self.ip

    # -----------------------------------------
    def mainLoop(self):
        """main scheduler loop

        """

        while self.bRunning:
            ppid = os.getppid()
            if ppid == 1:
                logging.info("ppid == 1, zombie, exiting")
                self.bRunning = False
            else:
                f = self.scheduler.step(self)
                if (f>60):
                    f = 60
                time.sleep(f)

        logging.info("end probe {}".format(self.name))

    # -----------------------------------------
    def trap_signal(self, _, _d):
        """catch the signals to handle the restart of the probe module

        """
        logging.info("exiting after signal received")
        self.pushSimpleLogMsg("INFO", "stopping")

        self.bRunning = False

        self.endJob()

    # -----------------------------------------
    def addJob(self, freq, f, data, sLock="none"):
        """add a job in the scheduler

        """
        if self.bNow is True:
            self.scheduler.add(self.name, freq, f, data, 1, sLock)
        else:
            self.scheduler.add(self.name, freq, f, data, 2, sLock)

    # -----------------------------------------
    def addJobExtended(self, freq, schedData, f, data, sLock="non"):
        """add a job in the scheduler with extended scheduler constraints

        """
        if self.bNow is True:
            self.scheduler.addExtended(self.name, freq, schedData, f, data, 1, sLock)
        else:
            self.scheduler.addExtended(self.name, freq, schedData, f, data, 2, sLock)

    # -----------------------------------------
    def getConfig(self, name, f, testf):
        """get config in database and extract 'name' jobs

        """
        config = self.db.getJobs(name)

        for c in config:
            if not c.__contains__('active'):
                logging.error("no active field on job, False by defalut")
                c['active'] = "False"

            if c['active'] == "True":
                if c['job'] == name:
                    data = c['data']

                    if os.environ.__contains__("PI_RUN_ONCE"):
                        data['run_once'] = True
 
                    # by default we check the lock before run
                    sLock = "check"
                    if "lock" in c:
                        sLock = c['lock']

                    if testf(data):
                        if c.__contains__('schedule'):
                            self.addJobExtended(int(c['freq']), c['schedule'], f, data, sLock)
                        else:
                            self.addJob(int(c['freq']), f, data, sLock)
                        yield c
                    else:
                        logging.error("condition not present, job will not run")
                else:
                    logging.error("should not happen, job={}".format(c['job']))
            else:
                logging.info("job inactive")

    # -----------------------------------------
    @classmethod
    def fTestNone(cls, _):
        """ test method by default """
        return True

    # -----------------------------------------
    @classmethod
    def f_testOK(cls, _):
        """testing method that is always ok

        """
        return True

    # -----------------------------------------
    @classmethod
    def f_testv4(cls, data):
        """testing method for insertion in the job list, check if ip version 4

        """
        return 'version' in data and data['version'] == 4

    # -----------------------------------------
    @classmethod
    def _setValueFromConfig(cls, _config, field, default=0, _min=-1000, _max=1000):
        if _config.__contains__(field):
            r = _config[field]
            r = max(_min, r)
            r = min(_max, r)
            return r
        return default

    # -----------------------------------------
    def pushResult(self, result, _type="result"):
        """push a result back to the database for main process to handle

        """
        if not isinstance(result, dict):
            raise Exception("pushResult not provided a dict")

        r = {
            "data" : result,
            "name" : str(self.name),
            "date" : time.time(),
            "type" : _type
        }

        self.db.pushResult(r)

    # -----------------------------------------
    def pushLogMsg(self, msg):
        """push a structured log message for information purpose

        """

        self.pushResult(msg, "log_msg")

    # -----------------------------------------
    def pushSimpleLogMsg(self, level, msg):
        """push a simple log message for information purpose

        """

        m = {
            "level": str(level).upper(),
            "message": msg
        }

        self.pushLogMsg(m)

    # -----------------------------------------
    def acquireLocalLock(self):
        """ask for a local lock

        returns True if lock is acquired, False otherwise

        """

        # if a lock is set, block other action
        if self.db.checkLock("local", str(self.name)):
            logging.debug("already locked on {}".format(str(self.name)))
            return False

        # if free, set the lock
        self.db.setLock(str(self.name), "local")

        if self.db.isProbeRunning():
            logging.info("lock acquired, but another running")
            return False

        return True

    # -----------------------------------------
    def releaseLocalLock(self):
        """
        clean lock
        """

        self.db.releaseLock("local")
        return "OK"

    # -----------------------------------------    
    @classmethod
    def endJob(cls):
        """
        endJob
        """
        return True
