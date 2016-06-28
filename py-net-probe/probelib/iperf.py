# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2016-06-26 21:53:21 alex>
#

"""
 probe for the iperf client
"""

import logging
import time
import subprocess
import json

from .probemain import probemain

class probe_iperf(probemain):
    """ iperf class for probe
    """

    WAY_BOTH = 1
    WAY_OUTPUT = 2
    WAY_INPUT = 3

    # -----------------------------------------
    def __init__(self):
        """constructor

        """
        probemain.__init__(self, "IPERF")

        self.iDuration = 5
        self.iWay = self.WAY_BOTH
        self.iTOS = 0
        self.iPort = 5201

        self.checkNet()
        self.getConfig("iperf", self.job_iperf)
        self.mainLoop()

    # -----------------------------------------
    def getConfig(self, name, f):
        """get the configuration from the database

        """
        jobs = super(probe_iperf, self).getConfig(name, f, self.f_testOK)
        for j in jobs:
            logging.info("add job to scheduler for {} each {} sec".format(j['data']['server'], j['freq']))

    # -----------------------------------------
    def job_iperf(self, _config):
        """iperf job

        """

        self.sTarget = _config['server']

        if _config.__contains__('duration'):
            self.iDuration = int(_config['duration'])

        if _config.__contains__('tos'):
            self.iTOS = int(_config['tos'])

        if _config.__contains__('port'):
            self.iPort = int(_config['port'])

        if _config.__contains__('way'):
            if _config['way'] == "input":
                self.iWay = self.WAY_INPUT
            else:
                if _config['way'] == "output":
                    self.iWay = self.WAY_OUTPUT
                else:
                    if _config['way'] == "both":
                        self.iWay = self.WAY_BOTH

        result = {
            "iperf-target" : self.sTarget,
        }

        aParams = ["iperf3", "-c", self.sTarget, "-J", "-t", str(self.iDuration), "-S", str(self.iTOS)]

        if self.iWay == self.WAY_OUTPUT or self.iWay == self.WAY_BOTH:
            try:
                p = subprocess.Popen(aParams, stdout=subprocess.PIPE)
                o = json.loads(p.communicate()[0])
            except:
                logging.error("launching iperf")
                return

            if p.returncode != 0:
                logging.error("communication with iperf server on {}".format(self.sTarget))
                return

            result["iperf-port"] = int(o['start']['connecting_to']['port'])
            result["iperf-version"] = str(o['start']['version'])
            result["iperf-proto"] = str(o['start']['test_start']['protocol'])
            result["iperf-duration"] = int(o['end']['sum_received']['seconds'])
            result["iperf-out-Mbps"] = o['end']['sum_received']['bits_per_second'] / 1000000
            result["iperf-out-retrans"] = int(o['end']['sum_sent']['retransmits'])

            if self.iWay == self.WAY_BOTH:
                time.sleep(0.5)

        if self.iWay == self.WAY_INPUT or self.iWay == self.WAY_BOTH:
            aParams.append('-R')

            try:
                p = subprocess.Popen(aParams, stdout=subprocess.PIPE)
                o = json.loads(p.communicate()[0])
            except:
                logging.error("launching iperf")
                return

            if p.returncode != 0:
                logging.error("communication with iperf server on {}".format(self.sTarget))
                return

            result["iperf-port"] = int(o['start']['connecting_to']['port'])
            result["iperf-version"] = str(o['start']['version'])
            result["iperf-proto"] = str(o['start']['test_start']['protocol'])
            result["iperf-duration"] = int(o['end']['sum_received']['seconds'])
            result["iperf-in-Mbps"] = o['end']['sum_received']['bits_per_second'] / 1000000
            result["iperf-in-retrans"] = int(o['end']['sum_sent']['retransmits'])

            logging.info("iperf result : {}".format(result))
            self.pushResult(result)