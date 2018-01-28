# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2017-10-12 21:38:21 alex>
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
 version propose
"""

import re

import logging


# -------------------------------------
def versionToInt(sVersion):
    """return int value for the version for easy compare
    """
    v = 0

    r = re.match(r"(\d+)\.(\d+)(\.(\d+))?", sVersion)

    if r != None:
        if r.lastindex >= 1:
            v = 1000000*int(r.group(1))

        if r.lastindex >= 2:
            v += 1000*int(r.group(2))

        if r.lastindex >= 3:
            v += int(r.group(4))

    return v


# -------------------------------------
def defNextVersion(sCurrentVersion, sNextVersion):
    """return next version to download
    :param string: probe next version from configuration (maximum value)
    :return: string with the next version to download
    """
    iCurrentVersion = versionToInt(sCurrentVersion)
    iProposedVersion = versionToInt(sNextVersion)

    if iCurrentVersion >= iProposedVersion:
        return sCurrentVersion

    if iProposedVersion < versionToInt('1.9.0'):
        return sNextVersion

    # 1.9.0 needs to be download as prereq to OS upgrade
    if iCurrentVersion < versionToInt('1.9.0'):
        return '1.9.0'

    # 1.9.1 is OS upgrade
    if iCurrentVersion < versionToInt('1.9.1'):
        return '1.9.1'

    # simple stable version
    if iCurrentVersion < versionToInt('1.9.2'):
        return '1.9.2'

    return sNextVersion
