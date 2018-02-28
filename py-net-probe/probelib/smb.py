# -*- Mode: Python; python-indent-offset: 4 -*-
#
# Time-stamp: <2018-02-28 21:19:02 alex>
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
 probe for the smb client
"""

import time
import logging
import datetime
import re

# from impacket import version
from impacket.dcerpc.v5 import transport, srvs
from impacket.dcerpc.v5.dtypes import NULL
from impacket.smbconnection import SMBConnection, ntpath, string, FILE_DIRECTORY_FILE, FILE_READ_DATA, FILE_LIST_DIRECTORY, FILE_SHARE_READ, FILE_SHARE_WRITE

from .probemain import probemain

# import pprint

class probe_smb(probemain):
    """ SMB probe
    """

    # -----------------------------------------
    def __init__(self):
        """constructor

        """
        probemain.__init__(self, "SMB")

        self.smbClient = None

        self.aShares = None
        self.dceInfo = None
        self.domain = None
        self.ip = None
        self.password = None
        self.port = None
        self.pwd = None
        self.server = None
        self.share = None
        self.tid = None
        self.username = None
        self.bConnected = None
        self.bGuestConnected = None

        self.__clean()

        self.checkNet()
        self.getConfig("smb", self.job_smb)
        self.mainLoop()

    # -----------------------------------------
    def __clean(self):
        """clean all variables"""
        self.bConnected = False
        self.bGuestConnected = True

        self.dceInfo = {}
        self.aShares = []
        self.tid = None
        self.pwd = '\\'
        self.share = ''

    # -----------------------------------------
    def getConfig(self, name, f, testf=None):
        """get the configuration from the database

        """
        jobs = super(probe_smb, self).getConfig(name, f, self.f_testOK)
        for j in jobs:
            logging.info("add job to scheduler every {} sec".format(j['freq']))

    # --------------------------------------------------
    def connect(self):
        """connect to the server
        """
        try: 
            self.smbClient = SMBConnection(self.server, self.ip, sess_port=self.port)
            self.smbClient.login(self.username, self.password, self.domain, '', '')

        except Exception as e:
            logging.error(str(e))
            self.bConnected = False
            return False

        self.bConnected = True

        self.bGuestConnected = (self.smbClient.isGuestSession() > 0)

        return True

    # --------------------------------------------------
    def isUserLogged(self):
        """is the connection guest
        """
    
        return self.bGuestConnected

    # --------------------------------------------------
    def getDCEInfo(self):
        """information on the DCE/RPC connection
        """
        if self.bConnected is False:
            return

        rpctransport = transport.SMBTransport(self.smbClient.getRemoteHost(), 
                                              filename=r'\srvsvc',
                                              smb_connection=self.smbClient)
        dce = rpctransport.get_dce_rpc()
        dce.connect()                     
        dce.bind(srvs.MSRPC_UUID_SRVS)
        resp = srvs.hNetrServerGetInfo(dce, 102)
        
        r = {
            "platform_id": resp['InfoStruct']['ServerInfo102']['sv102_platform_id'],
            "name": str(resp['InfoStruct']['ServerInfo102']['sv102_name'].replace('\x00', '')),
            "major": resp['InfoStruct']['ServerInfo102']['sv102_version_major'],
            "minor": resp['InfoStruct']['ServerInfo102']['sv102_version_minor'],
            "type": resp['InfoStruct']['ServerInfo102']['sv102_type'],
            "comment": str(resp['InfoStruct']['ServerInfo102']['sv102_comment'].replace('\x00', '')),
            "simultaneous_users": resp['InfoStruct']['ServerInfo102']['sv102_users'],
            "disc": resp['InfoStruct']['ServerInfo102']['sv102_disc'],
            "hidden": resp['InfoStruct']['ServerInfo102']['sv102_hidden'],
            "announce": resp['InfoStruct']['ServerInfo102']['sv102_announce'],
            "anndelta": resp['InfoStruct']['ServerInfo102']['sv102_anndelta'],
            "licenses": resp['InfoStruct']['ServerInfo102']['sv102_licenses'],
            "user_path": str(resp['InfoStruct']['ServerInfo102']['sv102_userpath'].replace('\x00', ''))
        }

        self.dceInfo = r

        del rpctransport
        del dce
        del resp

        return r

    # --------------------------------------------------
    def getWho(self):
        """who is connected -> error
        """

        try:
            rpctransport = transport.SMBTransport(self.smbClient.getRemoteHost(), 
                                                  filename=r'\srvsvc', 
                                                  smb_connection=self.smbClient)
            dce = rpctransport.get_dce_rpc()
            dce.connect()                     
            dce.bind(srvs.MSRPC_UUID_SRVS)
            resp = srvs.hNetrSessionEnum(dce, NULL, NULL, 10)

        except Exception as e:
            logging.error("getWho: {}".format(str(e)))
            return

        for session in resp['InfoStruct']['SessionInfo']['Level10']['Buffer']:
            print("host: %15s, user: %5s, active: %5d, idle: %5d" % (
                session['sesi10_cname'][:-1],
                session['sesi10_username'][:-1], 
                session['sesi10_time'],
                session['sesi10_idle_time']))

    # --------------------------------------------------
    def getShares(self):
        """get shares available on the server
        """
        if self.bConnected is False:
            logging.error("No connection open")
            return

        r = []
        resp = self.smbClient.listShares()
        for respi in resp:
            r.append(respi['shi1_netname'][:-1])

        self.aShares = r

        return r

    # --------------------------------------------------
    def getShare(self, regexp=".*"):
        """get shares available on the server

        """

        if self.bConnected is False:
            logging.error("No connection open")
            return

        resp = self.smbClient.listShares()
        for i, _ in enumerate(resp):
            netname = resp[i]['shi1_netname'][:-1]

            _r = re.match(regexp, netname)
            if _r != None:
                return {
                    "netname": netname,
                    "type": resp[i]['shi1_type'],
                    "remark": resp[i]['shi1_remark'][:-1]
                }

        return False

    # --------------------------------------------------
    def useShare(self, share):
        """use a share
        """
        if self.bConnected is False:
            logging.error("No connection open")
            return False

        if not self.aShares:
            self.getShares()

        if share not in self.aShares:
            logging.error("useShare : share {} not available on server".format(share))
            return False

        try:
            self.tid = self.smbClient.connectTree(share)
        except Exception as e:
            logging.error("useShare: {}".format(str(e)))
            return False

        logging.debug("connected on share {}".format(share))
        self.share = share

    # --------------------------------------------------
    def cd(self, _dir):
        """change directory on the share
        """
        if self.bConnected is False:
            logging.error("No connection open")
            return

        if self.tid is None:
            logging.error("not on a share")
            return

        pwd = ntpath.normpath(string.replace(_dir, '/', '\\'))
        logging.debug("cd to normalize path {}".format(pwd))

        # Let's try to open the directory to see if it's valid
        try:
            fid = self.smbClient.openFile(self.tid, pwd, 
                                          creationOption=FILE_DIRECTORY_FILE,
                                          desiredAccess=FILE_READ_DATA | FILE_LIST_DIRECTORY,
                                          shareMode=FILE_SHARE_READ | FILE_SHARE_WRITE)

            self.smbClient.closeFile(self.tid, fid)
        except Exception as e:
            logging.error("cd: {}".format(str(e)))
            return False

        logging.debug("success cd to {}".format(_dir))
        self.pwd = pwd
        return True

    # --------------------------------------------------
    def lsFiles(self, _filter='*'):
        """list files in the directory
        """
        if self.bConnected is False:
            logging.error("No connection open")
            return False

        if self.share == '':
            logging.error("No share selected, see useShare()")
            return False

        if self.tid is None:
            logging.error("not on a share")
            return False

        logging.debug("ls on share {} in {}".format(self.share, self.pwd))

        pwd = ntpath.join(self.pwd, _filter)

        r = []

        try:
            for f in self.smbClient.listPath(self.share, pwd):
                if f.is_directory() == 0:
                    r.append({
                        "mtime": f.get_mtime_epoch(),
                        "ctime": f.get_ctime_epoch(),
                        "atime": f.get_atime_epoch(),
                        "size": f.get_filesize(),
                        "name": str(f.get_longname())
                    })
        except Exception as ex:
            logging.error("file list: {}".format(str(ex)))

        return r

    # --------------------------------------------------
    def logoff(self):
        """get off the server
        """

        if self.smbClient is None or self.bConnected is False:
            logging.error("No connection open")
        else:
            self.smbClient.logoff()
            del self.smbClient

        self.__clean()

    # --------------------------------------------------
    def __str__(self): 
        """for print
        """
        import pprint

        s = "smb client object:\n"

        s += " configuration:\n"
        s += "  domain/user:pwd: {}/{}:{}\n".format(self.domain, self.username, self.password)
        s += "  server/ip:port: {}/{}:{}\n".format(self.server, self.ip, self.port)
        
        s += "\n status:\n"
        if self.bConnected:
            if self.bGuestConnected:
                s += "  guest connected\n"
            else:
                s += "  user connected\n"
        else:
            s += "  not connected\n"

        if self.dceInfo.__contains__('licenses'):
            s += "\n DCE Info: {}\n".format(pprint.pformat(self.dceInfo))

        if self.aShares:
            s += "\n shares = {}\n".format(pprint.pformat(self.aShares))

        return s

    # -----------------------------------------
    def step_get_file_stats(self, _step, iStep):
        """get_file_stats action

        """
        result = {}

        result["smb-step-{:02d}-action".format(iStep)] = _step['type']

        _ms = time.time()

        sError = "smb-step-{:02d}-error".format(iStep)
        if self.useShare(_step['share']) is False:
            result[sError] = "share not available: {}".format(_step['share'])
            return result
        result["smb-step-{:02d}-share".format(iStep)] = _step['share']

        if self.cd(_step['path']) is False:
            result[sError] = "path not available in share: {}".format(_step['share'])
            return result
        result["smb-step-{:02d}-path".format(iStep)] = str(_step['path'])

        a = self.lsFiles(_step['file'])
        if a is False:
            result[sError] = "file access error: {}".format(_step['file'])
            return result

        if len(a) == 0:
            result[sError] = "file not found: {}".format(_step['file'])
            return result

        result["smb-step-{:02d}-delay-ms".format(iStep)] = round((time.time() - _ms) * 1000)

        result["smb-step-{:02d}-file".format(iStep)] = a[0]['name']
        result["smb-step-{:02d}-atime".format(iStep)] = datetime.datetime.utcfromtimestamp(a[0]['atime']).isoformat()

        result["smb-step-{:02d}-ctime".format(iStep)] = datetime.datetime.utcfromtimestamp(a[0]['ctime']).isoformat()
        result["smb-step-{:02d}-mtime".format(iStep)] = datetime.datetime.utcfromtimestamp(a[0]['mtime']).isoformat()
        result["smb-step-{:02d}-size".format(iStep)] = a[0]['size']

        return result
        #pprint.pprint(a)

    # -----------------------------------------
    def step_get_share(self, _step, iStep):
        """get_share action

        """
        result = {}

        _ms = time.time()

        result["smb-step-{:02d}-action".format(iStep)] = _step['type']

        r = self.getShare(_step['share'])
        if r != False:
            result["smb-step-{:02d}-remark".format(iStep)] = r['remark']
            result["smb-step-{:02d}-netname".format(iStep)] = r['netname']
        else:
            result["smb-step-{:02d}-error".format(iStep)] = "not found: {}".format(_step['share'])

        result["smb-step-{:02d}-delay-ms".format(iStep)] = round((time.time() - _ms) * 1000)
        
        return result

    # -----------------------------------------
    def step_get_dce_info(self, _step, iStep):
        """get DCE action

        """
        result = {}

        _ms = time.time()

        result["smb-step-{:02d}-action".format(iStep)] = _step['type']

        r = self.getDCEInfo()

        result["smb-step-{:02d}-delay-ms".format(iStep)] = round((time.time() - _ms) * 1000)

        result["smb-step-{:02d}-anndelta".format(iStep)] = r['anndelta']
        result["smb-step-{:02d}-announce".format(iStep)] = r['announce']
        result["smb-step-{:02d}-disc".format(iStep)] = r['disc']
        result["smb-step-{:02d}-licenses".format(iStep)] = r['licenses']
        result["smb-step-{:02d}-major".format(iStep)] = r['major']
        result["smb-step-{:02d}-minor".format(iStep)] = r['minor']
        result["smb-step-{:02d}-name".format(iStep)] = r['name']
        result["smb-step-{:02d}-platform_id".format(iStep)] = r['platform_id']
        result["smb-step-{:02d}-simultaneous_users".format(iStep)] = r['simultaneous_users']
        
        return result

    # -----------------------------------------
    def step_read_file(self, _step, iStep):
        """read a file

        """
        result = {}

        result["smb-step-{:02d}-action".format(iStep)] = _step['type']

        if self.useShare(_step['share']) is False:
            result["smb-step-{:02d}-error"] = "share not available: {}".format(_step['share'])
            return result
        result["smb-step-{:02d}-share".format(iStep)] = _step['share']

        fileName = ntpath.normpath(string.replace(_step['file'], '/', '\\'))
        logging.debug("open file {}".format(fileName))

        if _step.__contains__('blocksize'):
            blocksize = min(1024, _step['blocksize'])
            blocksize *= 1024
        else:
            blocksize = 1024*1024

        _ms = time.time()

        try:
            fid = self.smbClient.openFile(self.tid, fileName)

            offset = 0
            endFile = False

            while endFile is False:
                _buffer = self.smbClient.readFile(self.tid, fid, offset, blocksize)
                if len(_buffer) == 0:
                    endFile = True
                offset += len(_buffer)

            result["smb-step-{:02d}-read-KB".format(iStep)] = offset / 1024.0
            result["smb-step-{:02d}-Mbps".format(iStep)] = (offset * 8 / (time.time() - _ms))/1024000

            self.smbClient.closeFile(self.tid, fid)
        except Exception as e:
            logging.error("open file: {}".format(str(e)))
            result["smb-step-{:02d}-error".format(iStep)] = "error in open file: {}".format(_step['file'])

        result["smb-step-{:02d}-delay-ms".format(iStep)] = round((time.time() - _ms) * 1000)

        return result

    # -----------------------------------------
    def job_smb(self, _config):
        """smb job

        """

        _msTotal = time.time()

        if not _config.__contains__('server'):
            logging.error("no server specified")
            return

        if not _config.__contains__('user'):
            _config['user'] = ""

        if not _config.__contains__('password'):
            _config['password'] = ""

        if not _config.__contains__('domain'):
            _config['domain'] = ""

        if not _config.__contains__('ip'):
            _config['ip'] = _config['server']

        if not _config.__contains__('port'):
            _config['port'] = 445

        self.domain = _config['domain']
        self.username = _config['user']
        self.password = _config['password']
        self.server = _config['server']
        self.ip = _config['ip']
        self.port = _config['port']

        result = {
            "smb-domain": self.domain,
            "smb-user": self.username,
            "smb-server" : self.server
        }
        
        if not _config.__contains__('steps'):
            logging.error("no steps specified")
            result['smb-error'] = "no step specified in configuration"
            self.pushResult(result)
            return

        logging.info("connect")
        _ms = time.time()
        if self.connect() is False:
            logging.error("connect error")
            result['smb-error'] = "connect error"
            self.pushResult(result)
            return
        result['smb-connect-delay-ms'] = round((time.time() - _ms) * 1000)

        _ms = time.time()
        self.getShares()
        result['smb-get-shares-delay-ms'] = round((time.time() - _ms) * 1000)

        # exec each steps
        iStep = 1
        while _config['steps'].__contains__("{:02d}".format(iStep)):
            _step = _config['steps']["{:02d}".format(iStep)]
            logging.debug("exec step {:02d}".format(iStep))

            if _step['type'] == "get_file_stats":
                _r = self.step_get_file_stats(_step, iStep)
                result.update(_r)

            if _step['type'] == "get_dce_info":
                _r = self.step_get_dce_info(_step, iStep)
                result.update(_r)

            if _step['type'] == "get_share":
                _r = self.step_get_share(_step, iStep)
                result.update(_r)

            if _step['type'] == "read_file":
                _r = self.step_read_file(_step, iStep)
                result.update(_r)

            iStep += 1

        # get the shares
        # print self.getShares()

        # get dce server info
        # pprint.pprint(self.getDCEInfo())
        
        # self.useShare("notavail")
        # self.useShare("music")

        # self.cd("/Calogero/L'Embellie")

        # pprint.pprint(self.lsFiles())

        logging.info("logout")
        self.logoff()

        result['smb-delay-ms'] = round((time.time() - _msTotal) * 1000)

        import pprint
        pprint.pprint(result)

        # logging.info("smb results : {}".format(result))
        # exit()
        #self.pushResult(result)

        if 'run_once' in _config:
            logging.info("run only once, exit")
            exit()
