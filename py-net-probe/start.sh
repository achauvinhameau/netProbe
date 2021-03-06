#!/bin/sh
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

cd $(dirname $0)

if [ -f post-boot.sh ]
then
 /bin/sh post-boot.sh
 rm -f post-boot.sh
fi

while [ true ]
do
 echo "starting"
 python ./main.py
 sync
 mount -o remount,ro /
 if [ $? -ne 0 ]
 then
   reboot
 fi
 sleep 10
done
