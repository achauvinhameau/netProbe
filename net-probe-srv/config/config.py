# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2017-09-24 15:56:55 alex>
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
 config class
"""

import json
import logging
import output
from output import outputer
import time
from .confOutputer import confOutputer

# import pprint

class config(object):
    """ class to manipulate the configuration """

    # ----------------------------------------------------------
    def __init__(self):
        """constructor

        """
        self.aHostTable = {}
        self.aTemplates = {}
        # self.outputMethodName = "none"
        self.fileName = "none"
        self.iTemplateJobsId = 1000
        self.fwVersion = {}
        self.lastLoad = 0
        self.config_cache = -1

        self.confOutputer = confOutputer()

        return

    # ----------------------------------------------------------
    def checkHost(self, sId):
        """check if the host is in the database

        """

        if self.aHostTable.__contains__(sId):
            logging.info("checkHost OK {}".format(sId))
            return True
        else:
            logging.info("checkHost KO {}".format(sId))
            return False

    # ----------------------------------------------------------
    def applyTemplateToHost(self, hostData, tName):
        """apply the template tName to the hostData

        """

        if not self.aTemplates.__contains__(tName):
            logging.warning("add a non existant template {} {}".format(hostData['id'], tName))
            return

        logging.info("applyTemplateToHost {} {}".format(hostData['probename'], tName))

        hjs = None

        t = self.aTemplates[tName]
        if not t.__contains__('jobs'):
            return

        # already some jobs on the probe ? maybe an update only
        if hostData.__contains__('probename'):
            probename = hostData['probename']

            for hkey in self.aHostTable:
                h = self.aHostTable[hkey]

                if h.__contains__('probename') and h['probename'] == probename:
                    if h.__contains__('jobs'):
                        hjs = h['jobs']
                        break

        for j in t['jobs']:
            newJob = j.copy()
            newJob['id'] = 0

            if hjs != None:
                for hj in hjs:
                    if hj.__contains__('template'):
                        if hj['template'] == tName and hj['data'] == newJob['data']:
                            newJob['id'] = hj['id']

            if newJob['id'] == 0:
                newJob['id'] = self.iTemplateJobsId
                self.iTemplateJobsId += 1

            newJob['template'] = tName

            if hostData.__contains__('jobs'):
                hostData['jobs'].append(newJob)
            else:
                hostData['jobs'] = [newJob]


    # ----------------------------------------------------------
    def addHost(self, hostData):
        """add a host to the database, if template specified, apply
           first the template
        """

        sId = str(hostData['id'])

        if hostData.__contains__('template'):
            for t in hostData['template']:
                self.applyTemplateToHost(hostData, t)

        _probeData = {
            "jobs": {},
            "probename": "unknown",
            "firmware": "current",
            "hostname": "unknown_probe",
            "fields": None
        }

        if hostData.__contains__('jobs'):
            _probeData['jobs'] = hostData['jobs']
            # check if active present, or put it to True
            for j in hostData['jobs']:
                if not j.__contains__('active'):
                    j['active'] = "True"

        if hostData.__contains__('firmware'):
            _probeData['firmware'] = hostData['firmware']

        if hostData.__contains__('hostname'):
            _probeData['hostname'] = hostData['hostname']

        # if specific fields for outputer exists
        if hostData.__contains__('fields'):
            _probeData['fields'] = hostData['fields']

        if hostData.__contains__('probename'):
            _probeData['probename'] = hostData['probename']

            for hkey in self.aHostTable:
                h = self.aHostTable[hkey]

                if h.__contains__('probename') and h['probename'] == _probeData['probename']:
                    # if same name but different id, insert a new key
                    if (hkey != sId):
                        del(self.aHostTable[hkey])
                        hkey = sId
                    self.aHostTable[hkey] = _probeData
                    logging.info("update probename {}".format(_probeData['probename']))
                    return

        if sId != "" and sId != None and sId != False:
            logging.info("add host {} to the DB".format(_probeData['probename']))
            self.aHostTable[sId] = _probeData

    # ----------------------------------------------------------
    def addTemplate(self, templateData):
        """add a template from the configuration file to the database

        """

        if not templateData.__contains__('name'):
            assert False, "no name section in template"

        sName = templateData['name']
        logging.info(sName)

        if templateData.__contains__('jobs'):
            jobs = templateData['jobs']
        else:
            jobs = {}

        self.aTemplates[sName] = {"jobs" : jobs}

    # ----------------------------------------------------------
    def confReadGlobal(self, conf):
        """handle the global part of the configuration file

        """

        if not conf.__contains__('global'):
            logging.info("no global section in the configuartion file")
            return

        confGlobal = conf['global']
        if confGlobal.__contains__('firmware'):
            confFW = confGlobal['firmware']
            self.fwVersion = {}
            for v in confFW.keys():
                self.fwVersion[v] = confFW[v]

            if not self.fwVersion.__contains__('current'):
                logging.error("configuration firmware does not contains 'current'")
                self.fwVersion['current'] = 'unknown'

        if confGlobal.__contains__('config_cache'):
            self.config_cache = int(confGlobal['config_cache'])

    # ----------------------------------------------------------
    def confAddTemplates(self, conf):
        """ add templates from conf

        """
        if conf.__contains__('template'):
            for t in conf['template']:
                self.addTemplate(t)

    # ----------------------------------------------------------
    def confAddProbes(self, conf):
        """ add probes from config

        """

        if not conf.__contains__('probe'):
            logging.error("cannot find probe configuration, exiting")
            assert False, "no probe config"

        for p in conf['probe']:
            self.addHost(p)

    # ----------------------------------------------------------
    def loadFile(self, sFile):
        """load host file and update configuraion

        """

        logging.info("load config file {}".format(sFile))

        if self.lastLoad > 0 and time.time() - self.lastLoad < self.config_cache:
            logging.debug("cache too young ({:.0f}<{}), abort".format(time.time() - self.lastLoad, self.config_cache))
            return

        try:
            f = file(sFile, 'r')
        except IOError:
            logging.error("cannot access config file {}".format(sFile))
            return False

        c = f.read()
        f.close()

        conf = ''
        try:
            conf = json.loads(c)
        except Exception as ex:
            assert False, "configuration file load exception : {}".format(", ".join(ex.args))

        self.lastLoad = time.time()

        self.confReadGlobal(conf)
        self.confAddTemplates(conf)

        # clean outputer array before inserting new configuration
        while (len(outputer) > 0):
            outputer.pop()

        if conf.__contains__('output'):
            for outputConf in conf['output']:
                if outputConf['active'] == "True":
                    self.confOutputer.addDebug(outputConf)
                    self.confOutputer.addElastic(outputConf)
                    self.confOutputer.addLogstash(outputConf)
                    self.confOutputer.addUkn(outputConf)
        else:
            outputer.append(output.debug())

        self.confAddProbes(conf)

        self.fileName = sFile

        logging.info("config file loaded in DB {}".format(sFile))

    # ----------------------------------------------------------
    def reload(self):
        """reload the configuration

        """
        if self.fileName == "none":
            assert False, "no file loaded previously"

        self.loadFile(self.fileName)

    # ----------------------------------------------------------
    def getJobsForHost(self, sId):
        """return the jobs configuration for the host

        """

        probename = sId
        jobs = None

        if self.aHostTable.__contains__(sId):
            jobs = self.aHostTable[sId]['jobs']
            probename = self.aHostTable[sId]['probename'] 

        logging.info("get jobs for {}".format(probename))

        if jobs == None:
            logging.error("should not ask for unknown host in the configuration")

        return jobs

    # ----------------------------------------------------------
    def getFieldsForHost(self, sId):
        """return the fileds configuration for the host

        """

        probename = sId
        fields = None

        if self.aHostTable.__contains__(sId):
            fields = self.aHostTable[sId]['fields']
            probename = self.aHostTable[sId]['probename']

        logging.info("get fields for {}".format(probename))

        return fields

    # ----------------------------------------------------------
    def getConfigForHost(self, sId):
        """return the configuration for the host

        """

        probename = sId
        r = None

        if self.aHostTable.__contains__(sId):
            r = self.aHostTable[sId]
            probename = self.aHostTable[sId]['probename'] 

        logging.info("get configuration for {}".format(probename))

        if r == None:
            logging.error("should not ask for unknown host in the configuration")

        return r

    # ----------------------------------------------------------
    def getFWVersionForHost(self, sId):
        """return the configuration for the host

        """

        probename = sId
        r = None

        if self.aHostTable.__contains__(sId):
            r = self.aHostTable[sId]['firmware']
            probename = self.aHostTable[sId]['probename'] 

        logging.info("get firwmare for {}".format(probename))

        if r == None:
            logging.error("should not ask for unknown host in the configuration")
    
        return r

    # ----------------------------------------------------------
    def getNameForHost(self, sId):
        """return the probe name for the host

        """

        logging.debug("get name for {}".format(sId))

        if self.aHostTable.__contains__(sId):
            return self.aHostTable[sId]['probename']
        else:
            return "unknown"

    # ----------------------------------------------------------
    def getListTemplate(self):
        """return the templates name

        """
        for t in self.aTemplates.keys():
            yield t

    # ----------------------------------------------------------
    def getListProbes(self):
        """return the probes name

        """
        for p in self.aHostTable.keys():
            templates = ""
            for j in self.aHostTable[p]['jobs']:
                if j.__contains__('template'):
                    templates += j['template']+", "
            yield [ self.aHostTable[p]['probename'],
                    p[-8:],
                    len(self.aHostTable[p]['jobs']),
                    templates[:-2]]

    # ----------------------------------------------------------
    def getCurrentFWVersion(self):
        """returns the current firmware version

        """

        return self.getFWVersion('current')

    # ----------------------------------------------------------
    def getFWVersion(self, version):
        """returns the firmware version

        """

        if self.fwVersion.__contains__(version):
            return self.fwVersion[version]
        else:
            return None

    # ----------------------------------------------------------
    def dump(self):
        """show the configuration host table

        """
        return self.aHostTable
