# Docker file for a logstash server to be bound to the server
# 
# Time-stamp: <2017-01-29 14:03:34 alex>
#
# docker build -t piprobe-logstash .
# docker run -d -p 55514:55514/udp -p 55514:55514/tcp piprobe-logstash
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

FROM logstash

MAINTAINER Alex <achauvinhameau@gmail.com>

EXPOSE 55514/udp
EXPOSE 55514/tcp

COPY logstash.conf /logstash.conf

CMD ["-f", "/logstash.conf"]
