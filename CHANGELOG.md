Changelog
=========

1.9 - 28/02/2018
-----
* add server name and tcp port number in configuration file


1.8 - 17/05/2017
-----
* changed hostId calculation, suppress IP => impact on existing installed probes
* avoid multiple conf read, add timer
* CIFS probe
* add IP address in stats frames
* fix: http response time push as float (not string)
* DNS probe
* schedule on job definition

1.7 - 23/04/2017
-----
* upgrade path in configuration file
* correct upgrade on PI
* add hostname in conf and on PI
* fix: correct schedule handling on probes
* probe test mode without redis
* NTP probe
* add iperf exec result to stats
* add traceroute probe

1.6 - 25/03/2017
-----
* pushAction for upgrading specific probe
* information on discovered probes to outputer
* fix : template id for configuration no properly set when multiple data used
* configuration check tool
* integration of codacy and syntax fix
* change md5 to sha for probe id

1.5 - 11/02/2017
-----
* stabilize code
* docker part for client and server
* resize flash card for easy install
* new probe discover to outputers
* add licence to code (GPL)

1.4 - 14/01/2017
-----
* fix : check probe connectivity with the server in the ping job
* add probe configuration for timers in init.cfg
* clean dead probes on the server
* clean the probe DB after inactivity
* templates for probe config (can include multiple at probe level)
* add vcgencmd display_power 0 to disable display
* disable audio on the PI
* rpi-update at install time
* adjust gpu memory on PI
* disable wifi
* suppress urllib3 logs
* add upgrade feature on probe
* dhcp specific client id
* docker configuration file for test
* add tool to shrink the flash card size for easy deployment


1.3 - 20/11/2016
----------------
* upgrade the software to the probe
* docker test probe

1.2
-----
* FIX : configuration reload not working
* set the configuration file name on command line for the server part
* set last seen on ping
* force reload the configuration on sighup
* add an "active" flag on a job in the server configuration
* exit the probe from the server action
* restart job from the server action
* add an exit command for the main process to restart everything
* don't run a job with active flag set to false
* add job process statistics in the stat message
* add cpu temp in health

1.1.1 (fix)
-----------
* check on regular basis the job processes for zombies and restart...
* detect if main.py has crashed in each probe
