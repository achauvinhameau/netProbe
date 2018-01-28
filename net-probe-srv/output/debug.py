# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2017-09-24 15:35:25 alex>
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
 debug output module
"""

import logging

from .output import output

class debug(output):
    """ class to handle debug output """

    # ----------------------------------------------------------
    def __init__(self):
        """constructor"""

        output.__init__(self, "debug")

    # ----------------------------------------------------------
    def send(self, data):
        """send to console"""
        if data.__contains__('timestamp'):
            del data['timestamp']

        logging.info("{}".format(data))
