# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2017-09-24 14:37:56 alex>
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
 elasticseatch output module
"""

from .output import output

from elasticsearch import Elasticsearch, ElasticsearchException
import logging
import os

class elastic(output):
    """ class to handle elastic output """

    # -----------------------------------------
    @classmethod
    def _setValueFromConfig(cls, _config, field, default=0, _min=-1000, _max=1000):
        if _config.__contains__(field):
            r = _config[field]
            r = max(_min, r)
            r = min(_max, r)
            return r

        return default

    # ----------------------------------------------------------
    def __init__(self, conf):
        """constructor"""

        output.__init__(self, "elastic")

        if (os.environ.__contains__("PI_TEST_NO_OUTPUT")):
            logging.info("no elastic connect, test only")
            return

        sConfIndex = "pyprobe"

        if not conf.__contains__('server'):
            assert False, "elastic configuration missing server"
        self.es_server = conf['server']

        if conf.__contains__('index'):
            sConfIndex = conf['index']

        iConfShard = int(self._setValueFromConfig(conf,
                                                  'shard',
                                                  default=3,
                                                  _min=1,
                                                  _max=12))

        iConfReplica = int(self._setValueFromConfig(conf,
                                                    'replica',
                                                    default=1,
                                                    _min=0, _max=5))

        try:
            self.es = Elasticsearch(host=self.es_server)

            self.es.indices.create(index=sConfIndex,
                                   body={
                                       'settings': {
                                           'number_of_shards': iConfShard,
                                           'number_of_replicas': iConfReplica
                                       }
                                   },
                                   ignore=400)
        except ElasticsearchException:
            logging.error("cannot connect to elastic server")

    # ----------------------------------------------------------
    def send(self, data):
        """send to elastic"""

        logging.info("send to elasticsearch")

        try:
            res = self.es.index(index="pyprobe", doc_type='result', body=data)
            if res['created'] != True:
                logging.error("error on insert in ES {}".format(res))
        except ElasticsearchException:
            logging.error("error sending back to elastic server")

    # ----------------------------------------------------------
    def __str__(self):
        """return the string of the outputer for debug purposes"""
        return "elastic outputer {}".format(self.es_server)
