# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2018-01-28 14:26:25 alex>
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
 probe for the watchdog
"""

import logging
import os

from .probemain import probemain

class probe_watchdog(probemain):
    """ watchdog class
    """

    # -----------------------------------------
    def __init__(self):
        """constructor

        """
        probemain.__init__(self, "WATCHDOG")

        self.getConfig("watchdog", self.job_watchdog)
        self.mainLoop()

    # -----------------------------------------
    def getConfig(self, name, f, testf=None):
        """get the configuration from the database

        """
        jobs = super(probe_watchdog, self).getConfig(name, f, self.f_testOK)
        for j in jobs:
            logging.info("add job to scheduler each {} sec".format(j['freq']))

    # -----------------------------------------
    def job_watchdog(self, _config):
        """watchdog job
        write something each call to /dev/watchdog

        """

        sWatchDogFile = "/dev/watchdog"

        if not os.path.exists(sWatchDogFile):
            logging.error("no watchdog file {}".format(sWatchDogFile))
            return

        try:
            f = open(sWatchDogFile, 'w')
            f.write("A")
            f.close()
            logging.debug("reset watchdog")
        except IOError:
            logging.error("accessing {}".format(sWatchDogFile))
            return False

        if 'run_once' in _config:
            logging.info("run only once, exit")
            exit()

