# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2017-09-24 16:15:14 alex>
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
 results WS
"""

from flask import make_response, jsonify, request
from netProbeSrv import app
from output import outputer

from liveDB import lDB
# from config import conf
# import time
import logging
# import pprint
import json
import zlib
from base64 import b64decode
import datetime
from ws_global import wsCheckParams, wsCheckHostUID

@app.route('/results', methods=['POST'])
def ws_results():
    """
    answers ok if everything is good
    """

    logging.debug("/results")

    _r = wsCheckParams(["uid", "data"])
    if _r != None:
        return _r

    uid = int(request.form['uid'])
    host = lDB.getHostByUid(uid)
    if host == None:
        logging.error("probe not known {}".format(uid))
        return make_response(jsonify({"answer" : "KO", "reason":"probe not known"}), 404)

    probename = lDB.getNameForHost(host)
    fields = lDB.getFieldsForHost(host)

    bCompressed = False
    if request.form.__contains__('compressed') and request.form['compressed'] == "yes":
        bCompressed = True

    data = []

    b64d = b64decode(request.form['data'])

    try:
        if bCompressed:
            s = zlib.decompress(b64d)
            data = json.loads(s)
        else:
            data.append(json.loads(b64d))
    except Exception as ex:
        logging.error("{}".format(" ".join(ex.args)))
        return make_response(jsonify({"answer" : "KO", "reason":"no json"}), 417)
    
    for d in data:
        if not d.__contains__('date'):
            logging.error("missing date")
            return make_response(jsonify({"answer" : "KO", "reason":"missing date"}), 417)

        d['timestamp'] = datetime.datetime.utcfromtimestamp(d['date']).isoformat()
        d['probeuid'] = uid
        d['probename'] = probename

        for o in outputer:
            logging.debug("output to {}".format(o))
            # check for fields
            if fields != None:
                ot = o.getType()
                if ot in fields:
                    d['data'].update(fields[ot])
            o.send(d)

    return make_response(jsonify({"answer" : "OK"}), 200)
