# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2018-02-28 21:29:53 alex>
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
 probe for the temperature of the PI
"""

# import time
import logging
import os.path
# import pprint

from .probemain import probemain

class probe_temp(probemain):
    """temperature class for probe

    """

    # -----------------------------------------
    def __init__(self, bTest=False):
        """constructor

        """
        probemain.__init__(self, "TEMP")

        self.checkNet()

        if not bTest:
            self.getConfig("temp", self.job_temp)
            self.mainLoop()

    # -----------------------------------------
    def getConfig(self, name, f, testf=None):
        """get the configuration from the database if f_testv4 passed

        """
        jobs = super(probe_temp, self).getConfig(name, f, self.fTestNone)
        for _ in jobs:
            logging.info("add temperature job to scheduler")

    # -----------------------------------------
    def job_temp(self, _):
        """temperature job

        """

        result = {}
        _fileName = '/sys/class/thermal/thermal_zone0/temp'

        if not os.path.isfile(_fileName):
            return

        # -------- Termperature from PI thermal sensor  --------------
        tempC = int(open(_fileName).read()) / 1e3
        result['temp-pi-celsius'] = tempC
        result['temp-pi-fahrenheit'] = tempC*9/5+32

        logging.info("temperature results : {}".format(result))

        self.pushResult(result)
