# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2018-01-28 13:14:36 alex>
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
 probe for the http protocol using urllib2
"""

import logging
import ssl
import urllib2
import time
import re
import os

from .probemain import probemain

class probe_http(probemain):
    """ http class for probe
    """

    # -----------------------------------------
    def __init__(self):
        """constructor

        """
        probemain.__init__(self, "HTTP")

        self.bSSLcheck = True

        self.checkNet()
        self.getConfig("http", self.job_http)
        self.mainLoop()

    # -----------------------------------------
    def getConfig(self, name, f, testf=None):
        """get the configuration from the database if f_testv4 passed

        """
        jobs = super(probe_http, self).getConfig(name, f, self.f_testOK)
        for j in jobs:
            logging.info("add job to scheduler for {} each {} sec".format(j['data']['url'], j['freq']))

    # -----------------------------------------
    def job_http(self, _config):
        """http job

        """
        sReContent = ""

        sURL = _config['url']
        if _config.__contains__('timeout'):
            fTimeout = float(_config['timeout'])
        else:
            fTimeout = 10.0

        if _config.__contains__('content'):
            sReContent = str(_config['content'])

        if 'ssl_check' in _config:
            self.bSSLcheck = bool(_config['ssl_check'] == "True")

        result = {
            "http-timeout" : fTimeout,
            "http-url" : sURL
        }

        sError = "no-error"
        sReturnCode = "error"
        
        fNow = time.time()
        fTime = 0

        try:
            if not self.bSSLcheck:
                ssl._create_default_https_context = ssl._create_unverified_context

            f = urllib2.urlopen(sURL, data=None, timeout=fTimeout)
            fTime = time.time() - fNow

            sReturnCode = str(f.getcode())
            
            # check content of the returned page
            if sReContent != "":
                content = f.read()
                if os.environ.__contains__("PI_RUN_ONCE"):
                    print(content)
                #print sReContent
                r = re.search(sReContent, content)

                if r != None:
                    result['contentMatch'] = "OK"
                else:
                    result['contentMatch'] = "KO"

            aInfo = f.info()
            s = aInfo.get('Content-Type')
            if s != None:
                result['http-contentType'] = s

            i = aInfo.get('Content-Length')
            if i != None:
                result['http-contentLen'] = int(i)

            s = aInfo.get('Server')
            if s != None:
                result['http-server'] = s

        except urllib2.URLError as e:
            sError = str(e.reason)
        except Exception as ex:
            sError = str(", ".join(ex.args))

        if fTime == 0:
            fTime = fTimeout

        result['http-code'] = sReturnCode
        result['http-error'] = sError
        result['http-time'] = float(fTime.__format__('0.4f'))

        logging.info("http result : {}".format(result))
        self.pushResult(result)

        if 'run_once' in _config:
            logging.info("run only once, exit")
            exit()
