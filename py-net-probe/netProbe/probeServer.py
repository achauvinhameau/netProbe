# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2018-01-28 14:18:15 alex>
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
Manages communication with the central server

>>> import netProbe
>>> srv = netProbe.probeServer()
>>> srv.findServer()
True
>>> srv.ping()
True
"""

import socket
import time
import json
import logging
import zlib
from base64 import b64encode
import os
import re
from subprocess import call, check_output, CalledProcessError

import requests


class probeServer(object):
    """class to talk to the probe server"""

    def __init__(self):
        """
        constructor
        """
        self.sServerName = ""
        self.iServerPort = 5000
        self.sPingURL = ""
        self.sSrvBaseURL = ""
        self.bServerAvail = False
        self.lastCmdRespTime = 0
        self.uid = 0
        self.sHostId = ""

        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=2,
                                                pool_maxsize=4)
        self.session.mount('http', adapter)

    # -----------------------------------------------------------------
    def findServer(self, serverName=None):
        """
        check which server host to contact
        based on server names
           net-probe-srv-prod
           net-probe-srv
           probe-srv
        """

        aServers = ['net-probe-srv-prod',
                    'net-probe-srv',
                    'probe-srv']

        if serverName != None:
            aServers = [serverName]

        for server in aServers:
            try:
                socket.getaddrinfo(server, 80)
                self.sServerName = server
                break
            except socket.gaierror:
                logging.error("cannot find servername {}".format(server))

        if self.sServerName == "":
            logging.error("no suitable server to talk to")
            return False

        self.sSrvBaseURL = "http://{}:{}".format(self.sServerName,
                                                 self.iServerPort)

        return True

    # -----------------------------------------------------------------
    def ping(self):
        """
        calls the ping web service on the selected server in order
        to know if it is available for other transaction
        gather the response time and store the server status

        this channel is used by the server to push actions

        returns None or structure with action
        """
        if self.bServerAvail is False:
            self.uid = 0
            self.sHostId = "unknown"

        if self.sServerName == "":
            return None

        if self.sPingURL == "":
            self.sPingURL = self.sSrvBaseURL+'/ping'

        delta = -1
        self.lastCmdRespTime = -1

        dReturn = {'status' : 'OK'}

        try:
            now = time.time()
            if self.uid > 0:
                data = {
                    'uid' : self.uid,
                    'hostId' : self.sHostId
                }
                r = self.session.post(self.sPingURL, data, timeout=5)

                # logging.info("status code = {}".format(r.status_code))

                if r.status_code == 200:
                    delta = time.time() - now
                    s = json.loads(r.text)
                    if s.__contains__('answer') and s['answer'] != "OK":
                        self.bServerAvail = False
                        return None

                    # action in the return ?
                    if s.__contains__('action'):
                        dReturn['action'] = s['action']
                else:
                    self.bServerAvail = False
                    return None

            else:
                # self.session.get(self.sPingURL)
                # delta = time.time() - now
                # bConnected = False
                return None

            self.lastCmdRespTime = delta
            self.bServerAvail = True
        except requests.ConnectionError:
            logging.error("reaching srv : connection refused")
            self.bServerAvail = False
            return None

        return dReturn

    # -----------------------------------------------------------------
    def getLastCmdDeltaTime(self):
        """
        returns last command response time in seconds
        """
        return self.lastCmdRespTime

    # -----------------------------------------------------------------
    def getStatus(self):
        """
        returns communication with server status
        """
        return self.bServerAvail

    # -----------------------------------------------------------------
    def discover(self, sHostId, sIpV4, sIpV6, sVersion):
        """
        calls the discover web service on the server in order to
        announce the probe itself
        if the probe is known...
        :param sHostId: hostid string to uniquely identify the probe
        :param sIpV4: IP v4 address of the probe
        :param sIpV6: IP v6 address of the probe
        :param sVersion: current version of the probe software
        """

        self.sHostId = sHostId

        data = {
            'hostId':sHostId,
            'ipv4':sIpV4,
            'ipv6':sIpV6,
            'version':sVersion
        }

        req = self.sSrvBaseURL+'/discover'

        try:
            r = self.session.post(req, data, timeout=2)
        except requests.exceptions.RequestException:
            logging.error("reaching srv : connection refused")
            self.bServerAvail = False
            return False

        s = json.loads(r.text)

        if r.status_code == 200:
            if s.__contains__('uid') and s.__contains__('answer') and s['answer'] == "OK":
                self.uid = s['uid']
                self.bServerAvail = True
                self.session.close()
                logging.info("discover: my id is {}".format(self.uid))
                return True
            else:
                logging.error("bad response from server, missing uid")

        logging.error("error from server in discover {}:{}".format(r.status_code, s['reason']))
        self.bServerAvail = False
        self.session.close()
        return False

    # -----------------------------------------------------------------
    def getConfig(self):
        """
        get configuration for this probe from server
        """

        if self.bServerAvail is False or self.uid == 0:
            return None

        data = {
            'uid' : self.uid
        }

        answer = {}

        # get main configuration
        try:
            r = self.session.post(self.sSrvBaseURL+'/myConfig', data, timeout=5)

            if r.status_code == 200:
                s = json.loads(r.text)
                if s.__contains__('answer') and s['answer'] != "OK":
                    if s.__contains__('reason'):
                        logging.error("bad answer on myConfig from job ws : {}".format(s['reason']))
                    self.bServerAvail = False
                    return None

                answer['config'] = s['config']

        except requests.ConnectionError:
            logging.error("get configuration : connection error")
            return None

        try:
            r = self.session.post(self.sSrvBaseURL+'/myjobs', data, timeout=5)
            
            if r.status_code == 200:
                s = json.loads(r.text)
                if 'answer' in s and s['answer'] != "OK":
                    if 'reason' in s:
                        logging.error("bad answer from job ws : {}".format(s['reason']))
                    self.bServerAvail = False
                    return None

                if s.__contains__('jobs'):
                    answer['jobs'] = s['jobs']

        except requests.ConnectionError:
            logging.error("get jobs : connection error")
            return None

        # add watchdog job
        wj = {
            'lock': 'none',
            'job': 'watchdog',
            'version': 1,
            'active': 'True',
            'freq': 5,
            'data': {},
            'id': 2000001,
            'restart': 1
        }

        answer['jobs'].append(wj)

        return answer

    # -----------------------------------------------------------------
    def pushResults(self, aResult):
        """push results to the server
        aResult should be an array
        """

        logging.info("push results")

        if not isinstance(aResult, list):
            raise Exception("pushResult not provided an array")
        
        if self.bServerAvail is False or self.uid == 0:
            return None

        data = {
            "uid" : self.uid,
            "time" : time.time()
        }

        if len(aResult) > 1:
            data['compressed'] = "yes"
            data['data'] = b64encode(zlib.compress(json.dumps(aResult)))
        else:
            data['compressed'] = "no"
            data['data'] = b64encode(json.dumps(aResult[0]))

        try:
            r = self.session.post(self.sSrvBaseURL+'/results', data, timeout=5)
            
            if r.status_code == 200:
                s = json.loads(r.text)
                if s.__contains__('answer') and s['answer'] != "OK":
                    if s.__contains__('reason'):
                        logging.error("bad answer from result ws : {}".format(s['reason']))
                    self.bServerAvail = False
                    return None

        except requests.ConnectionError:
            logging.error("push results : connection error")
            return None

        return True

    # -----------------------------------------------------------------
    def upgrade(self):
        """upgrade the software
        """

        bOnARM = True

        logging.info("check for software upgrade")

        if os.path.isfile("/bin/uname"): 
            s = check_output(["/bin/uname", "-m"])
            if re.match("arm", s) is None:
                bOnARM = False
                if not os.path.exists("/home/pi/py-net-probe"):
                    logging.info(" avoid on non ARM/PI platform")
                    return False
        else:
            logging.info(" no /bin/uname")
            return False

        try:
            data = {
                'uid' : self.uid
            }
            r = self.session.post(self.sSrvBaseURL+'/upgrade', data, stream=True, timeout=5)
            if r.status_code == 201:
                logging.info("no need to upgrade")
                return False

            if r.status_code != 200:
                logging.info("error in upgrade")
                return False

            if bOnARM:
                logging.info("turning FS to RW")
                call(["/bin/mount", "-o", "remount,rw", "/"])

            with open("/home/pi/new.deb", 'wb') as fd:
                for chunk in r.iter_content(1024):
                    fd.write(chunk)

        except requests.ConnectionError:
            logging.error("reaching srv : connection refused")

        try:
            logging.info("check downloaded package")
            s = check_output(["/usr/bin/dpkg-deb", "-f", "/home/pi/new.deb"])
            if re.match("Package: netprobe", s) != None:
                # package is correct, install it
                logging.info("install new version")
                call(["/usr/bin/dpkg", "-i", "/home/pi/new.deb"])
            else:
                logging.error("bad package deb")

        except CalledProcessError as e:
            logging.error("error in call for dpkg")
            logging.error(e)
            return True

        os.unlink("/home/pi/new.deb")

        if bOnARM:
            logging.info("turning FS back to RO")
            call(["/bin/sync"])
            call(["/bin/mount", "-o", "remount,ro", "/"])

        logging.info("exiting")
        return True
