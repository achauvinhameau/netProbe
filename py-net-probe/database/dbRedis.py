# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2018-02-28 21:16:10 alex>
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
 probe database for configuration and data
"""

import logging
import time
import json
import redis

from .db import db

class dbRedis(db):
    """
    database class based on redis (db=1)
    """

    # -----------------------------------------
    def __init__(self, host="localhost", backoff_test=False):
        """
        constructor
        """
        db.__init__(self)

        if backoff_test:
            self.backOff = -1
        else:
            self.backOff = 1
        self.dbRedisId = 1

        self.connect(host)

    # -----------------------------------------
    def connect(self, host="localhost"):
        """
        connect to the redis server
        wait until it connects
        :param host: name of the host where redis server is running
        """

        while True:
            logging.info("connect to redis {}".format(host))

            self.db = redis.Redis(db=self.dbRedisId,
                                  max_connections=1,
                                  socket_timeout=2,
                                  host=host)

            try:
                self.db.ping()
                break

            except redis.ConnectionError as e:
                self.backOff *= 1.5
                if self.backOff > 30 or self.backOff < 0:
                    self.db = None
                    raise Exception('redis not running? abort')
                logging.error("redis : {}, next try in {:.2f}".format(e.message,
                                                                      self.backOff))
                time.sleep(self.backOff)

        self.backOff = 1

    # -----------------------------------------
    def checkDB(self):
        """check if db is set"""
        if self.db is None:
            raise Exception("redis not started")

    # -----------------------------------------
    def cleanJob(self, jobName):
        """suppress the list from the database

        """
        self.checkDB()
        return self.db.delete(jobName)

    # -----------------------------------------
    def addJob(self, jobName, job):
        """add a job in the job list

        """
        self.checkDB()
        self.db.rpush(jobName, json.dumps(job))

    # -----------------------------------------
    def getJobs(self, jobName):
        """extracts all jobs and return an array

        """
        self.checkDB()

        a = []
        l = self.db.llen(jobName)
        if l > 0:
            for i in range(l):
                s = self.db.lindex(jobName, i)
                a.append(json.loads(s))

        return a

    # -----------------------------------------
    def dumpJob(self, jobName):
        """dump the content of the db for jobname, return a generator

        """
        self.checkDB()

        l = self.db.llen(jobName)
        if l > 0:
            for i in range(l):
                yield self.db.lindex(jobName, i)

    # -----------------------------------------
    def pushResult(self, result):
        """add a result in the queue for the main process
        result is a dict

        """
        if not isinstance(result, dict):
            raise Exception("pushResult not provided a dict")

        self.checkDB()

        self.db.rpush("results", json.dumps(result))

    # -----------------------------------------
    def popResult(self):
        """pop a result from the queue
        return None if nothing in the queue
        """
        self.checkDB()
        return self.db.lpop("results")

    # -----------------------------------------
    def lenResultQueue(self):
        """get queue size
        """
        self.checkDB()
        return self.db.llen("results")

    # -----------------------------------------
    def setLock(self, sModule, sType):
        """add a lock in the local database

        """

        super(dbRedis, self).setLock(sModule, sType)
        self.checkDB()

        r = {
            "module": sModule,
            "date": time.time()
        }

        if sType == "local":
            logging.debug("set local lock on {}".format(sModule))
            self.db.set("lock_local", json.dumps(r), ex=3600)

    # -----------------------------------------
    def releaseLock(self, sType):
        """
        release a lock specified by the sType
        """

        super(dbRedis, self).releaseLock(sType)
        self.checkDB()

        if sType == "local":
            logging.debug("clear local lock")
            self.db.delete("lock_local")

    # -----------------------------------------
    def checkLock(self, sType="none", sModule="none"):
        """checks if a lock is in the queue

        returns True if a local lock is present on another module
        """
        super(dbRedis, self).checkLock()
        self.checkDB()

        if sType == "local":
            l = self.db.get("lock_local")
            if l is None:
                return False

            # we have a lock, on wich module ?
            r = json.loads(l)

            return bool(r['module'] != sModule)

        return False

    # -----------------------------------------
    def incrRunningProbe(self):
        """ increment counter of probes running (centralized in the redis PI server
        """
        super(dbRedis, self).incrRunningProbe()

        self.checkDB()

        self.db.incr("local_running")

    # -----------------------------------------
    def decrRunningProbe(self):
        """ decrement counter of probes running (centralized in the redis PI server
        """

        super(dbRedis, self).decrRunningProbe()

        self.checkDB()

        self.db.decr("local_running")

    # -----------------------------------------
    def isProbeRunning(self):
        """ is a probe already running? Usefull when asking for lock
        """

        self.checkDB()

        v = self.db.get("local_running")
        if v is None:
            return False

        if int(v) == 0:
            return False

        return True

    # -----------------------------------------
    def cleanLock(self):
        """suppress lock and set counter to 0

        """

        super(dbRedis, self).cleanLock()

        self.checkDB()

        self.db.delete("local_running")
        self.releaseLock("lock_local")

    # -----------------------------------------
    def disconnect(self):
        """disconnect from redis

        """

        self.db = None
