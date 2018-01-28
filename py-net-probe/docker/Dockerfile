# Docker file for testing the probe
#
# Time-stamp: <2017-10-12 21:48:38 alex>
#
# docker build -t netprobe .
# docker run -d netprobe
#    --volume /tmp/py:/py
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

FROM debian:jessie

LABEL description "python image near the PI infrastructure with raspbian"
LABEL maintainer "ach@meta-x.org"
LABEL version "1.8"

COPY start.sh /

RUN set -ex \
    && apt-get -y upgrade \
    && apt-get -y update \
    && apt-get -y install apt-utils dialog apt-transport-https \
    \
    && apt-get -y install gcc vim python-pip python-dev \
    && apt-get -y install ntp \
    \
    && apt-get -y install git \
    && pip install --upgrade pip \
    \
    && pip install netifaces \
    && pip install redis \
    && pip install psutil \
    && pip install pycrypto \
    \
    && apt-get -y install iperf3 \
    \
    && mkdir -p /home/pi/py-net-probe \
    \
    && git clone https://github.com/CoreSecurity/impacket \
    && mv /impacket/impacket `python -c "import sys; print sys.path[1]"` \
    && rm -rf /impacket \
    \
    && chmod +x /start.sh \
    \
    && apt-get -y remove gcc vim python-pip python-dev git \
    && rm -rf /usr/lib/gcc

COPY netprobe.deb /
RUN set -ex \
    && dpkg -i /netprobe.deb \
    && rm -f /netprobe.deb

CMD ["/start.sh"]