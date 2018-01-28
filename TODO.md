server
======
* push regular stats to back office on probe connected or discovered, last hello...
* configuration with fields by probe, not only globals

probe engine
============
* stop probe when not anymore in configuration
* disable the upgrade + config in the init.cfg
* send default router IP address to help locating new probes on internal network
* add configuration change in updates of jobs
* add jobs restart in updates
* add next exec in probe stats
* minimum delay between 2 iteration on modules
* global lock between probes
* push messages back to server

probe
=====
* http probe can use a target IP address different than URL server name

raspberry
=========

History
=======
move to changelog once released

1.9
-----
* https add no ssl check
* local lock between modules
* watchdog
* post boot script for system upgrade
* version as int for easy comparison, upgrade path
* add fields for specific outputer in configuration