# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2017-09-24 15:53:12 alex>
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
 config liveDB
 used to store the current status of probes
"""

# import json
import logging
import time

from config import conf
# import pprint

class liveDB(object):
    """ class to manipulate the liveDB """

    # ----------------------------------------------------------
    def __init__(self):
        """constructor

        """
        self.aProbeTable = {}
        self.uid = 0
        return

    # ----------------------------------------------------------
    def getUniqueId(self, sId):
        """ returns a unique id for the probe. If the probe is already
        registered returns the associated uid

        """
        if self.aProbeTable.__contains__(sId):
            host = self.aProbeTable[sId]
            if host.__contains__('uid'):
                return host['uid']

        self.uid = self.uid+1
        return self.uid

    # ----------------------------------------------------------
    def addHost(self, sId):
        """
        add a host to the database
        """
        if sId != "" and sId != None and sId != False:
            logging.info("add host to the live DB")
            self.aProbeTable[sId] = {}

    # ----------------------------------------------------------
    def updateHost(self, sId, o):
        """ update host by its identifier """

        if self.aProbeTable.__contains__(sId) == False:
            self.addHost(sId)
    
        if self.aProbeTable[sId].__contains__('name'):
            _name = self.aProbeTable[sId]['name']
        else:
            _name = sId
        # print(self.aProbeTable[sId]['name'])
        new = self.aProbeTable[sId].copy()
        new.update(o)

        self.aProbeTable.update({sId : new})
        logging.info("update host in live DB for {}".format(_name))

    # ----------------------------------------------------------
    def getHostByUid(self, uid):
        """ return HostId by uid """

        for hkey in self.aProbeTable:
            h = self.aProbeTable[hkey]

            if h.__contains__('uid') and h['uid'] == uid:
                return hkey

        return None

    # ----------------------------------------------------------
    def getHostContentByUid(self, uid):
        """return Host content by uid

        """

        for hkey in self.aProbeTable:
            h = self.aProbeTable[hkey]

            if h.__contains__('uid') and h['uid'] == uid:
                return h

        return None

    # ----------------------------------------------------------
    def getHostVersionByUid(self, uid):
        """return Host version by uid

        """

        a = self.getHostContentByUid(uid)
        if a == None:
            return None

        if not a.__contains__('version'):
            logging.error("host should have a version")
            return None

        return a['version']

    # ----------------------------------------------------------
    @classmethod
    def getConfigForHost(self, host):
        """ return the probe config """

        return conf.getConfigForHost(host)


    # ----------------------------------------------------------
    @classmethod
    def getFieldsForHost(self, host):
        """ return the probe fields for outputers """

        return conf.getFieldsForHost(host)

    # ----------------------------------------------------------
    @classmethod
    def getJobsForHost(self, host):
        """ return the probe job config """

        return conf.getJobsForHost(host)

    # ----------------------------------------------------------
    @classmethod
    def getNameForHost(self, host):
        """ return the probe name """

        return conf.getNameForHost(host)

    # ----------------------------------------------------------
    def getListProbes(self):
        """ return the probes list """

        r = []
        for p in self.aProbeTable:
            s = self.aProbeTable[p]

            if s.__contains__('uid') and s.__contains__('ipv4') and s.__contains__('ipv6') and s.__contains__('version') and s.__contains__('name') and s.__contains__('last'):
                r.append({"uid" : s['uid'],
                          "ipv4" : s['ipv4'],
                          "ipv6" : s['ipv6'],
                          "version" : s['version'],
                          "name": s['name'],
                          "last" : int(time.time() - s['last'])})

        return r

    # ----------------------------------------------------------
    def getAction(self, sId):
        """ return next action for the host if set """

        if self.aProbeTable.__contains__(sId) == False:
            logging.info("sId not found")
            return None

        if self.aProbeTable[sId].__contains__('action'):
            a = self.aProbeTable[sId]['action']
            del self.aProbeTable[sId]['action']
            return a

    # ----------------------------------------------------------
    def cleanOldProbes(self):
        """ remove unseen probe for long time
            started by cron
        """

        for hkey in self.aProbeTable:
            h = self.aProbeTable[hkey]

            if time.time() - h['last'] > 180:
                logging.info("clean probe uid={}".format(h['uid']))
                del(self.aProbeTable[hkey])
                # suppress only one at a time
                return

    # ----------------------------------------------------------
    def dump(self):
        """ show the configuration host table """
        return self.aProbeTable

    # ----------------------------------------------------------
    def cleanDB(self):
        """clean the whole database

        """
        self.aProbeTable = {}
        self.uid = 0
