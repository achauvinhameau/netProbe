#
# Time-stamp: <2017-09-24 16:13:07 alex>
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

dirs = netProbeSrv config output liveDB

all:
	@echo make lint
	@echo make flakes
	@echo make clean
	@echo make test
	@echo make coverage

lint: clean
	pylint --rcfile=~/.pylint srv.py $(dirs:%=%/*.py)

flakes: clean
	@pyflakes *py $(dirs:%=%/*.py)

clean:
	@rm -f $(dirs:%=%/*pyc)
	@rm -f $(dirs:%=%/*~)
	@rm -f *pyc
	@rm -f *~

test: clean
	@nosetests tests

coverage: clean
	PI_TEST_NO_OUTPUT=1 coverage run ./tests/test_all.py
	coverage report -m

version:
	@awk '/^    "version" :/ { $$0="    \"version\" : \"'`cat ../VERSION`'\"," }; /^    "date"/ { $$0="    \"date\" : \"'`date +%0d/%0m/%y-%H:%M:%S`'\"," } ; { print }' < netProbeSrv/version.py > /tmp/version.py
	@cp /tmp/version.py netProbeSrv/version.py
	@rm -f /tmp/version.py
	@awk '/^__version/ { $$0="__version__ = \"'`cat ../VERSION`'\"" }; /^__date__/ { $$0="__date__ = \"'`date +%0d/%0m/%y-%H:%M:%S`'\"" } ; { print }' < srv.py > /tmp/srv.py
	@cp /tmp/srv.py srv.py
	@rm -f /tmp/srv.py

cc: clean
	@echo complexity
	@radon cc $(dirs) *py -a -nc
	@echo maintenability
	@radon mi $(dirs) *py -nb
