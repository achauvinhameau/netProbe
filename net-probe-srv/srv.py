# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2018-02-28 21:00:46 alex>
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
 server module for the probe system
"""

__version__ = "1.9.7"
__date__ = "28/02/18-20:45:19"

import logging
import signal
import os
from output import outputer

from config import conf

LOGGER = logging.getLogger('apscheduler.executors.default')
LOGGER.setLevel(logging.ERROR)
LOGGER = logging.getLogger('werkzeug')
LOGGER.setLevel(logging.ERROR)
LOGGER = logging.getLogger('urllib3')
LOGGER.setLevel(logging.ERROR)

# ----------- parse args
try:
    import argparse
    parser = argparse.ArgumentParser(description='server for the raspberry probe system')

    parser.add_argument('--config', '-c', metavar='file', default='1.conf', type=str, help='configuration file', nargs='?')

    parser.add_argument('--log', '-l', metavar='level', default='INFO', type=str, help='log level DEBUG, INFO, WARNING, ERROR', nargs=1, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])

    parser.add_argument('--debug', '-d', help='debug mode for engine',
                        action='store_true')

    parser.add_argument('--check', action='store_true',
                        help='check the configuration file and exit')

    args = parser.parse_args()

except ImportError:
    log.error('parse error')
    exit()

# ----- set the log level and format
LOGGER = logging.getLogger('apscheduler')
LOGGER.setLevel(logging.ERROR)

_logFormat = '%(asctime)-15s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s'
logLevel = logging.ERROR

if args.log[0] == 'DEBUG':
    logLevel = logging.DEBUG
if args.log[0] == 'WARNING':
    logLevel = logging.WARNING
if args.log[0] == 'ERROR':
    logLevel = logging.ERROR
if args.log[0] == 'INFO':
    logLevel = logging.INFO

logging.basicConfig(format=_logFormat, level=logLevel)
# logging.basicConfig(level=logLevel)

if not isinstance(args.debug, bool):
    logging.error('debug arg is not taking argument')
    exit()

logging.info("starting server, version {}, {}".format(__version__, __date__))
logging.debug("pid {}".format(os.getpid()))

try:
    if conf.loadFile(args.config) == False:
        logging.error('exiting')
        exit()
except Exception as ex:
    logging.error("{}".format(" ".join(ex.args)))
    exit()

if args.check == True:
    logging.info("check configuration : syntax seems ok")

    outs = []
    for o in outputer:
        outs.append(o.getType())

    print("outputs: {}".format(", ".join(outs)))

    print("templates: {}".format(", ".join(conf.getListTemplate())))

    for p in conf.getListProbes():
        print("probe : {}".format(p[0]))
        print("  id: *{}".format(p[1]))
        print("  jobs: {}".format(p[2]))
        print("  templates: {}\n".format(p[3]))

    print("configuration {} check OK".format(args.config))
    print("exiting...")
    exit()

from netProbeSrv import app
from netProbeSrv import main, ping, version, discover, results
from netProbeSrv import job, myConfig
from netProbeSrv import pushAction, admin
from netProbeSrv import upgrade


# -----------------------------------------
def trap_HUP_signal(sig, heap):
    """ trap signal for config reload """

    conf.reload()


signal.signal(signal.SIGHUP, trap_HUP_signal)

if __name__ == '__main__':
    app.debug = args.debug
    app.secret_key = "piprobe-{}".format(__version__)
    app.run(host=conf.server_name, threaded=True)
