# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2017-09-24 14:25:05 alex>
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

import sys
import os
import nose
import json
import logging

sys.path.append(os.getcwd())
import database

# ---------------------------------------------
@nose.tools.timed(10)
def test_create_db():
    """ create database in redis """

    db = database.dbRedis.dbRedis()

    if db == None:
        assert False

# ---------------------------------------------
@nose.tools.timed(10)
def test_disconnect():
    """ test disconnect from db"""

    db = database.dbRedis.dbRedis()

    if db == None:
        assert False

    db.disconnect()

    try:
        db.checkDB()
    except Exception:
        return

    assert False, "connection should be closed"


# ---------------------------------------------
def test_create_db_nohost():
    """ connection error to redis """

    try:
        db = database.dbRedis.dbRedis(host="192.168.16.13", backoff_test=True)
    except Exception:
        return

    assert False, "server found :)"


# ---------------------------------------------
def test_addjob():
    """ add job in the database """
    db = database.dbRedis.dbRedis()

    if db == None:
        assert False

    db.cleanJob("test")
    db.addJob("test",
              {
                  'name': 'test'
              }
    )

    if db.dumpJob("test").next() != '{"name": "test"}':
        assert False

    db.getJobs("test")

# ---------------------------------------------
def test_pushResult():
    """ push a test result in the db """
    db = database.dbRedis.dbRedis()

    if db == None:
        assert False

    db.pushResult({"test": "valeur"})

    db.lenResultQueue()
    db.popResult()

    try:
        db.pushResult(12)
    except Exception:
        return
    assert False, "result should be dict"

# ---------------------------------------------
def test_clean():
    """ clean database """
    db = database.dbRedis.dbRedis()

    if db == None:
        assert False

    db.cleanJob("test")
    if sum(1 for x in db.dumpJob("test")) != 0:
        assert False

    db.addJob("test", {'name' : 'test'})

    if db.dumpJob("test").next() != '{"name": "test"}':
        assert False

    db.cleanJob("test")
    if sum(1 for x in db.dumpJob("test")) != 0:
        assert False

# ---------------------------------------------
def test_lock():
    """ lock in database """
    db = database.dbRedis.dbRedis()

    if db == None:
        assert False

    db.setLock("test_module", "local")
    db.checkLock("other", "test_module")
    db.checkLock("local", "test_module")
    db.releaseLock("local")
    db.cleanLock()

# ---------------------------------------------
def test_incr():
    """ incr in database """
    db = database.dbRedis.dbRedis()

    if db == None:
        assert False

    db.incrRunningProbe()
    if not db.isProbeRunning():
        assert False, "should have a probe counter"

    db.decrRunningProbe()

    if db.isProbeRunning():
        assert False, "should not have a probe counter"

    db.cleanLock()
    db.checkLock("local", "test_module")

    if db.isProbeRunning():
        assert False, "should not have a probe counter"

# ---------------------------------------------
def test_dbTest():
    """ coverage for db.py and dbTest.py """
    db = database.dbTest.dbTest()
    db.connect()

    db.addJob("test", {'name': 'test'})

    db.dumpJob("test")

    db.cleanJob("test")

    db.setLock(1, 2)
    db.releaseLock(1)
    db.checkLock()
    db.incrRunningProbe()
    db.decrRunningProbe()
    db.isProbeRunning()
    db.cleanLock()

    db.pushResult({"test": "valeur"})
    db.lenResultQueue()
    db.popResult()

    try:
        db.pushResult(12)
    except Exception:
        return
    assert False, "result should be dict"

# ---------------------------------------------
def all(b=True):
    if b:
        test_addjob()
        test_clean()
        test_create_db()
        test_disconnect()

        test_pushResult()

        test_lock()
        test_incr()

        test_create_db_nohost()

    test_dbTest()

if __name__ == '__main__':
    _logFormat = '%(asctime)-15s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s'
    logging.basicConfig(format=_logFormat,
                        level=logging.INFO)

    all(True)
    # all(False)
