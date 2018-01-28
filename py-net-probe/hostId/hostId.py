# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2018-01-28 14:31:45 alex>
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
unique identifier for the probe
"""

import hashlib
import re
import logging
# import pprint

class hostId(object):
    """ class to manipulate host id and get unique identifier
        for the probe """

    id = "none"

    def __init__(self, sUniqueId):
        """
        constructor
        calculate this host id based on the cpuinfo and unique id provided

        :param sUniqueId: unique id string (ie Mac Address)
        """

        try:
            f = open('/proc/cpuinfo', 'r')
        except IOError as e:
            print("ERROR accessing cpuinfo {}".format(e))
            raise Exception('ERROR accessing cpuinfo')

        sCPU = sUniqueId

        aLines = f.readlines()
        f.close()

        iFound = False

        for l in aLines:
            if iFound is False:
                r = re.match("flags[^:]+: (.*)", l)
                if r != None:
                    flags = r.group(1).split()
                    sCPU = sCPU+'@'+"@".join(sorted(flags)[:5])

                r = re.match("cpu MHz[^:]+: ([^.]*)", l)
                if r != None:
                    sCPU = sCPU+'@'+r.group(1)

                r = re.match("model[^:]+: (.*)", l)
                if r != None:
                    sCPU = str(sCPU)+'@'+str(r.group(1))

                r = re.match("processor[^:]+: [1-9]", l)
                if r != None:
                    iFound = True

        self.id = hashlib.sha256(sCPU).hexdigest()

        logging.info("my id = {}".format(self.id))

    def get(self):
        """
        returns the id
        """
        return self.id
