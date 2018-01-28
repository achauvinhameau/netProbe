#
# Time-stamp: <2017-09-24 14:28:09 alex>
#
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

_none:
	@echo make all
	@echo make clean
	@echo make test
	@echo make coverage
	@echo make version
	@echo make cc

all: version test cc
	@echo make git-status

clean:
	@cd net-probe-srv && make -s clean
	@cd py-net-probe && make -s clean
	@rm -f *~ \#*# .*~
	@rm -f ansible/files/*~ ansible/playbooks/*~ ansible/playbooks/*retry
	@rm -f docs/*~

test: clean
	@cd py-net-probe && make -s test
	@cd net-probe-srv && make -s test

git-status: clean
	git status

coverage: clean version
	@cd net-probe-srv && make -s coverage
	@cd py-net-probe && make -s coverage-all
	@coverage combine py-net-probe/.coverage net-probe-srv/.coverage
	@coverage xml
	CODACY_PROJECT_TOKEN=1936f6ba7c3a41ee82aa5e1cbfc16ce6 python-codacy-coverage -r coverage.xml

version:
	@cd net-probe-srv && make -s version
	@cd py-net-probe && make -s version

cc:
	@echo '**** in net-probe-srv'
	@cd net-probe-srv && make -s cc
	@echo '**** in py-net-probe'
	@cd py-net-probe && make -s cc
