# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2017-04-09 16:13:33 alex>
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
 version WS
"""

from flask import make_response, jsonify
from netProbeSrv import app

aVersion = {
    "answer" : "OK",
    "version" : "1.9.6",
    "date" : "28/01/18-14:33:15",
    "author" : "Alex Chauvin"
}

@app.route('/version', methods=['GET'])
def ws_version():
    """
    version web service
    """
    # global aVersion
    return make_response(jsonify(aVersion), 200)
