# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2017-04-09 15:49:56 alex>
#
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
# import time
import json
import sys

# import pprint

class dbTest(object):
    """
    database class for testing only
    """

    def __init__(self, host=None):
        """
        constructor
        """
        self.db = None

    def connect(self, host=None):
        """
        """

        self.db = True

    @classmethod
    def cleanJob(self, jobName):
        """suppress the list from the database

        """
        logging.info("delete {}".format(jobName))


    @classmethod
    def addJob(self, jobName, job):
        """add a job in the job list

        """
        logging.info("add job {} {}".format(jobName,json.dumps(job)))

    @classmethod
    def getJobs(self, jobName):
        """extracts all jobs and return an array

        """
        logging.info("getJobs")

        s = sys.stdin.read()
        a = []

        a=json.loads(s)

        return a

    @classmethod
    def dumpJob(self, jobName):
        """dump the content of the db for jobname, return a generator

        """
        logging.info("dumpJob")

    @classmethod
    def pushResult(self, result):
        """add a result in the queue for the main process
        result is a dict

        """
        if not isinstance(result, dict):
            raise Exception("pushResult not provided a dict")

        logging.info("push result {}".format(result))

    @classmethod
    def popResult(self):
        """pop a result from the queue
        return None if nothing in the queue
        """
        logging.info("pop result")

    @classmethod
    def lenResultQueue(self):
        """get queue size
        """
        logging.info("lenResultQueue")
        return 0
