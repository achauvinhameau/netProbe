# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2017-04-17 14:29:32 alex>
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
 client module for the probe system
"""

__version__ = "1.7.5"
__date__ = "15/04/17-17:09:14"
__author__ = "Alex Chauvin"

import time
import logging
import os
# import pprint
import signal

import netProbe
import sched
import hostId
import database
import json
import platform
from subprocess import call, check_output, CalledProcessError
import re

from config import conf

from probe import restartProbe, stopAllProbes, checkProbes, statsProbes

aModules = ['icmp', 'health', 'http', 'iperf', 'temp', 'ntp', 'traceroute', 'smb']

# ----------- parse args
try:
    import argparse
    parser = argparse.ArgumentParser(description='raspberry net probe system')

    parser.add_argument('--log', '-l', metavar='level', default='INFO', type=str, help='log level', nargs='?', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])

    parser.add_argument('--probe', '-p', metavar='probe_loglevel', default='ERROR', type=str, help='log level for probes', nargs=1, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])

    parser.add_argument('--redis', '-r', metavar='none', help='redis server', default=None, nargs='?')

    parser.add_argument('--server', '-s', metavar='none', help='PiProbe server', default=None, nargs='?')

    args = parser.parse_args()

except ImportError:
    log.error('parse error')
    exit()

# limit log level for request module
LOGGER = logging.getLogger('requests')
LOGGER.setLevel(logging.ERROR)
LOGGER = logging.getLogger('urllib3')
LOGGER.setLevel(logging.ERROR)

_logFormat = '%(asctime)-15s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s'
logLevel = logging.ERROR

if args.log == 'INFO':
    logLevel=logging.INFO
if args.log == 'DEBUG':
    logLevel=logging.DEBUG
if args.log == 'WARNING':
    logLevel=logging.WARNING
if args.log == 'ERROR':
    logLevel=logging.ERROR

logging.basicConfig(format=_logFormat, level=logLevel)
# logging.basicConfig(level=logLevel)

# log level for probes
if args.probe[0] != 'ERROR':
    os.environ["PI_LOG_LEVEL"] = args.probe[0]

logging.info("starting probe")

logging.info(" version {}".format(__version__))
logging.debug("pid {}".format(os.getpid()))

# check wether the uid is root (for icmp)
if os.getuid() != 0:
    logging.error("not root")
    exit()

srv = {}
stats = netProbe.stats()
bConnected = False
bRunning = True
probeJobs = {}
probeProcess = {}

stats.setVar("probe version", __version__)

# checks if we are in a standard docker container with redis linked
# the PI_REDIS_SRV env var is set for the subprocess probes
if (os.environ.__contains__("REDIS_PORT_6379_TCP_ADDR")):
    args.redis = os.environ["REDIS_PORT_6379_TCP_ADDR"]

if (args.redis != None):
    os.environ["PI_REDIS_SRV"] = args.redis
    logging.info("set the redis server address to {}".format(os.environ["PI_REDIS_SRV"]))

db = database.dbRedis.dbRedis(args.redis)

# -----------------------------------------
def serverConnect():
    """
    connects to main server, if not available, wait and loop
    """

    global srv
    # global stats
    global bConnected
    # global bRunning

    # check IP configuration of probe
    # if no default route !
    #
    ip = netProbe.ipConf()

    if ip.hasDefaultRoute() == False:
        logging.error("no default route, abort")
        exit(1)
    else:
        logging.info("ip route OK")

    # get hostId
    #
    hid = hostId.hostId(ip.getLinkAddr()+ip.getIfIPv4())

    stats.setIPv4(ip.getIfIPv4())
    stats.setIPv6(ip.getIfIPv6())

    bConnected = False

    iSleepConnectDelay = 0

    while bConnected == False:
        if bRunning == False:
            logging.error("stop main probe")
            exit()

        logging.info("sleep for {:0.0f}s".format(iSleepConnectDelay))
        time.sleep(iSleepConnectDelay)

        if iSleepConnectDelay == 0:
            iSleepConnectDelay = 1
        else:
            if iSleepConnectDelay < 60:
                iSleepConnectDelay = iSleepConnectDelay * 1.5
            else:
                iSleepConnectDelay = 60

        # connect to probe server
        #
        srv = netProbe.probeServer()

        if srv.findServer(args.server):
            logging.info("srv IP found in tables")
        else:
            logging.error("server not found in DNS or host table")
            continue

        # send identification to get id & certificate
        #
        if srv.discover(hid.get(), ip.getIfIPv4(), ip.getIfIPv6(), __version__) == True:
            bConnected = True

        if bConnected and srv.ping() == False:
            logging.error("service ping not working")
            continue

        # init the variable for deconnexion check
        stats.setVar("ping-server-retry", 0)


#
# -----------------------------------------
def ping():
    """
    call the ping ws of the server
    called by the scheduler
    """

    # global stats
    global bConnected

    if bConnected == False:
        return

    r = srv.ping()

    if r == None:
        _iRetry = stats.getVar("ping-server-retry")
        logging.warning("ping without answer, retry={}".format(_iRetry))
        if _iRetry > 2:
            bConnected = False
        else:
            stats.setVar("ping-server-retry", _iRetry+1)
        return

    fLastDelta = srv.getLastCmdDeltaTime()

    if fLastDelta < 0:
        bConnected = False
        logging.error("lost server connection, restart")
        return

    logging.info("ping delta time = {:0.2f}ms".format(fLastDelta*1000))
    stats.setVar("ping-server-delay", fLastDelta*1000)

    # action handle, if some action has been pushed by the server
    if r.__contains__('action') and isinstance(r['action'], dict):
        action(r['action'])

# -----------------------------------------
def pushJobsToDB(jobName):
    """ change the job definition for the probe job in the db called only
    if the job config has been updated
    """
    # global db
    # global probeJobs
    # global stats

    # suppress the old definition in db
    db.cleanJob(jobName)

    for i in probeJobs.keys():
        j = probeJobs[i]
        if j['job'] == jobName:
            del j['restart']
            db.addJob(jobName, j)
            stats.setJob(j)

# -----------------------------------------
def getConfig():
    """
    get my probe config from the server
    """
    # global probeJobs
    global bConnected
    # global aModules

    if bConnected == False:
        return

    logging.info("get configuration from server")

    # if we need to restart one job, we fill this dictionary
    restart = {}

    config = srv.getConfig()
    if config == None:
        logging.error("can't get my config")
        bConnected = False
        return None

    if not config.__contains__('jobs'):
        logging.error("can't get my jobs")
        bConnected = False
        return None

    if not config.__contains__('config'):
        logging.error("can't get my config")
        bConnected = False
        return None

    # handle configuration
    # do we have to change the hostname ?
    currentHostname = platform.node()
    newHostname = config['config']['hostname']
    if currentHostname != newHostname:
        logging.info("changing hostname to {}".format(newHostname))

        if os.path.isfile("/bin/uname"): 
            _s = check_output(["/bin/uname", "-m"])
            if re.match("arm", _s) == None:
                logging.info(" avoid on non ARM platform")
            else:
                try:
                    logging.info("turning FS to RW")
                    call(["/bin/mount", "-o", "remount,rw", "/"])

                    f = file("/etc/hostname", 'w')
                    f.write(newHostname)
                    f.close()

                    logging.info("turning FS to RO")
                    call(["/bin/mount", "-o", "remount,ro", "/"])

                    os.system("/bin/hostname {}".format(newHostname))
                except IOError:
                    logging.error("accessing hostname file /etc/hostname")
        else:
            logging.info(" no /bin/uname")
        
    # handle jobs
    for c in config['jobs']:
        # update job or create
        if probeJobs.__contains__(c['id']):
            a = probeJobs[c['id']]
            if c['version'] > a['version']:
                a['restart'] = 1
                a['version'] = c['version']
                a['data'] = c['data']
            else:
                a['restart'] = 0
        else:
            a = c
            a['restart'] = 1

        if a['restart'] == 1:
            probeJobs[c['id']] = a

            for m in aModules:
                if a['job'] == m:
                    restart[m] = 1

    if len(restart) == 0:
        return

    for m in aModules:
        if restart.__contains__(m):
            pushJobsToDB(m)
            restartProbe(m, probeProcess)

# -----------------------------------------
def mainLoop():
    """
    main scheduler loop
    """
    # global scheduler
    # global bConnected
    # global stats

    while bConnected:
        f = scheduler.step()
        time.sleep(f)

# -----------------------------------------
def trap_signal(sig, heap):
    """ trap all signals for stop """

    global bRunning
    global bConnected

    logging.info("exit signal received, wait for next step")

    bRunning = False
    bConnected = False

#
# -----------------------------------------
def action(a):
    global bRunning
    global bConnected
    # global probeProcess
    global aModules
    # global srv

    if a['name'] == "restart":
        args = a['args']
        if args['module'] == "all":
            logging.info("restart received from server, exiting")
            # stopAllProbes(probeProcess)

            bRunning = False
            bConnected = False
            return

        if args['module'] == "job":
            job = args['job']
            logging.info("restart job {} received from server".format(job))

            if job in aModules:
                restartProbe(job, probeProcess)
                return
            else:
                logging.error("job not found {}".format(job))
                return

    if a['name'] == "upgrade":
        srv.upgrade()
        return

    logging.info("action not handled {}".format(a))

# -----------------------------------------
def popResults(_db):
    """pop the results from the database queue and push these to the server

    """
    # global stats
    # global bConnected

    if bConnected == False:
        return

    a = []

    l = _db.lenResultQueue()
    logging.info("result queue len {}".format(l))

    if l < 5:
        nb = 3
    else:
        nb = int(l/2)

    for _ in range(nb):
        r = _db.popResult()
        if r != None:
            j = json.loads(r)
            stats.setLastRun(j['name'].lower(), j['date'])
            a.append(j)

    if len(a) > 0:
        srv.pushResults(a)

# -----------------------------------------
def pushStats(srv):
    """call the stats.push

    """
    # global stats
    # global bConnected

    if bConnected == False:
        return

    stats.push(srv)

# -----------------------------------------

signal.signal(signal.SIGTERM, trap_signal)
signal.signal(signal.SIGINT, trap_signal)

# create global scheduler
#
scheduler = sched.sched()

while bRunning:
    scheduler.clean()

    serverConnect()

    getConfig()

    # job to refresh the configuration from the server every hour
    scheduler.add("get configuration", conf.get("scheduler", "get_conf"), getConfig, None, 2)

    # push the results stored in the redis queue every 8 seconds
    scheduler.add("push results", conf.get("scheduler", "push_results"), popResults, db, 2)

    # ping the server for connectivity check every minute
    scheduler.add("ping server", conf.get("scheduler", "ping_server"), ping, None, 2)

    # check if probe process has exited every 30"
    scheduler.add("check probes process", conf.get("scheduler", "check_probes"), checkProbes, probeProcess)

    # push the stats of the probes every minute for the server
    scheduler.add("stats probes", conf.get("scheduler", "stats_probes"), statsProbes, [probeProcess, stats], 2)

    # push the collected stats to the server every 5 minutes
    scheduler.add("stats push", conf.get("scheduler", "stats_push"), pushStats, srv)

    # ask for the upgrade every hour to the server
    scheduler.add("upgrade", conf.get("scheduler", "upgrade"), srv.upgrade, None)

    mainLoop()

logging.info("stop all jobs")
stopAllProbes(probeProcess)
logging.info("exiting")
