# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2018-02-28 21:03:29 alex>
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
 server WS
"""

from liveDB import lDB

from flask import Flask
from flask_apscheduler import APScheduler
from config import conf

import logging


class Config(object):
    JOBS = [
        {
            'id': 'cleanOldProbes',
            'func': lDB.cleanOldProbes,
            'args': None,
            'trigger': 'interval',
            'seconds': 10
        }
    ]

    SCHEDULER_VIEWS_ENABLED = False


app = Flask(__name__)
app.config.from_object(Config())
app.config['MAX_CONTENT_LENGTH'] = 10000
app.config['PERMANENT_SESSION_LIFETIME'] = 120
app.config['SERVER_NAME'] = "{}:{}".format(str(conf.server_name),
                                           str(conf.tcp_port))

scheduler = APScheduler()

scheduler.init_app(app)
scheduler.start()
