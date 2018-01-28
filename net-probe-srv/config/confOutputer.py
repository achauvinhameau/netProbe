# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2017-09-24 15:30:18 alex>
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
 config class outputer section
"""

import logging

import output
from output import outputer


class confOutputer(object):
    """ outputer section for the configuration file  """

    # ----------------------------------------------------------
    def __init__(self):
        """constructor
        """

    # ----------------------------------------------------------
    @classmethod
    def addDebug(cls, conf):
        """add debug default outputer from the configuration
        """
        if conf['engine'] == "debug":
            outputer.append(output.debug())

    # ----------------------------------------------------------
    @classmethod
    def addUkn(cls, conf):
        """check if the outputer is known

        """

        # create a fake object for checking method name
        o = output.output()

        if not o.checkMethodName(conf['engine']):
            logging.error("unknown output method name '{}', possible values are : {}".format(conf['engine'], ", ".join(o.getMethodName())))
            assert False, "bad output name"

    # ----------------------------------------------------------
    @classmethod
    def addElastic(cls, conf):
        """add elastic search outputer if present in the configuration

        """
        if conf['engine'] != "elastic":
            return

        if conf.__contains__('parameters'):
            outputer.append(output.elastic(conf['parameters'][0]))
        else:
            logging.error("elastic output without parameters, exiting")
            assert False, "missing parameters for elastic output"

    # ----------------------------------------------------------
    @classmethod
    def addLogstash(cls, conf):
        """add logstash outputer if present in the configuration

        """
        if conf['engine'] != "logstash":
            return

        if conf.__contains__('parameters'):
            outputer.append(output.logstash(conf['parameters'][0]))
        else:
            logging.error("logstash output without parameters, exiting")
            assert False, "missing parameters for logstash output"
