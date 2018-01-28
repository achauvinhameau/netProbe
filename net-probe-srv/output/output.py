# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2017-09-24 15:33:45 alex>
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
 outputer
"""

import logging

class output(object):
    """class to handle output generic

    """

    #TYPE_UNKNOWN = 0
    #TYPE_ELASTICSEARCH = 1
    #TYPE_DEBUG = 2

    # ----------------------------------------------------------
    def __init__(self, _type="unknown"):
        """constructor

        """

        self.type = _type
        self.lKnownMethod = ("debug", "elastic", "logstash")

    # ----------------------------------------------------------
    def getMethodName(self):
        """push output valid methods"""

        for m in self.lKnownMethod:
            yield m

    # ----------------------------------------------------------
    def checkMethodName(self, name):
        """check wether method is known, from configuration"""
        try:
            self.lKnownMethod.index(name)
            return True
        except ValueError:
            return False

        return False

    # ----------------------------------------------------------
    def send(self, data):
        """send"""
        logging.info("send to {} {}".format(self.type, data))
        return

    # ----------------------------------------------------------
    def getType(self):
        """return the type of the outputer"""
        return self.type

    # ----------------------------------------------------------
    def __str__(self):
        """return the string of the outputer for debug purposes"""
        return "{} outputer".format(self.type)
