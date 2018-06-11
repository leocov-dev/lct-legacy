import sys
import os
import platform
import traceback
import socket
import getpass
import urllib
import urllib2
import json

import pymel.core as pm
from pymel import versions

sys.dont_write_bytecode = True


class Editor(object):

    def __init__(self, *args, **kwargs):
        """ Initialize class and variables """

    @classmethod
    def update_model_editors(cls, *args, **kwargs):
        ''' '''
        model_panel_list = pm.lsUI(editors=True)
        for model_panel in model_panel_list:
            if 'modelPanel' in model_panel:
                try:
                    pm.modelEditor(model_panel, edit=True, **kwargs)
                except:
                    Utility.lc_print_exception()


class Utility(object):

    @classmethod
    def lc_log_file(cls, sting=None, *args, **kwargs):
        ''' '''
        pass

    @classmethod
    def lc_print(cls, string, mode=None, *args, **kwargs):
        ''' '''
        if mode == 'warning':
            # print '\n'
            pm.warning(' \n# {}\n#'.format(string))
        elif mode == 'error':
            # print '\n'
            pm.error(' \n# {}\n#'.format(string))
        else:
            sys.stdout.write('\n# lct: {0} #'.format(string))

    @classmethod
    def lc_print_exception(cls, message='Something went wrong', *args, **kwargs):
        """ """
        msg = '# Stack Trace:\n'

        e = sys.exc_info()[1]
        tb = traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback)
        for line in tb:
            msg = msg + '>>> {}'.format(line)

        try:
            log = "{}\n\n{}".format(SystemInfo().get_text(), msg)
            logger = LogManager('lct error log', log)
            logger.SendLog()
        except:
            print '\n'
            print '###############################'
            print '### Error sending exception ###'
            print '### Please send script log  ###'
            print '###    to log@leocov.com    ###'
            print '###############################'
        finally:
            cls.lc_print('{0}\n{1}'.format(message, msg), mode='error')

    @classmethod
    def maya_version_check(cls, *args, **kwargs):
        '''
        check the maya version code
        '''
        minVersion = 2014
        if int(versions.shortName()) < minVersion:
            return False
        return True

    @classmethod
    def addFramePadding(cls, frame='', pad='0000', *args,
                        **kwargs):  # there is a better way to do this with "{0:03d}".format(num) or format(num, '03')
        '''
            returns a string
            adds frame padding if neccessary
        '''

        padLen = len(pad)
        frameLen = len(str(frame))

        if frameLen > padLen:
            return str(frame)

        else:
            paddedFrame = '{0}{1}'.format(pad, frame)
            min = abs(padLen - len(paddedFrame))
            paddedFrame = paddedFrame[min:len(paddedFrame) + 1]

            return str(paddedFrame)

    @classmethod
    def centerPvt(cls, sel, *args, **kwargs):
        ''' center geometry pivot (scale, rotate, translate) to 0,0,0 '''
        for obj in sel:
            pm.move(obj.rotatePivot, [0, 0, 0])
            pm.move(obj.scalePivot, [0, 0, 0])

    @classmethod
    def filterByToken(cls, list=[], token='', *args, **kwargs):
        ''' filter a list based on a suffix token '''
        filtered = []
        for obj in list:
            buffer1 = obj.split('_')  # split obj names up around underscore character
            for elem in buffer1:
                elem = elem.rstrip(
                    '0123456789')  # removes numbers from the end of the token so Occlude1 becomes Occlude
                token = token.rstrip('0123456789')
                if elem.capitalize() == token.capitalize():  # compares token and obj's - .capitalize() turns testABC into Testabc
                    filtered.append(obj)

        return filtered

    @classmethod
    def setTransformVisibility(cls, list=[], visibility=True, *args, **kwargs):
        ''' set visibility of any transforms in list'''
        for item in list:
            if item.nodeType() == 'transform':
                pm.setAttr(item + '.visibility', visibility)

        return list

    @classmethod
    def build_tool_command(cls, moduleBase, toolName, inline=True, *args, **kwargs):
        ''' '''
        runCommand = 'None'

        if inline:  # if you need to preserve the command as a single line when printing or writing to a file
            runCommand = 'import ' + moduleBase + '.' + toolName + '.' + toolName + ' as ' + toolName + '\\nreload(' + toolName + ')\\n' + toolName + '.' + toolName + 'UI()'
        else:
            runCommand = 'import ' + moduleBase + '.' + toolName + '.' + toolName + ' as ' + toolName + '\nreload(' + toolName + ')\n' + toolName + '.' + toolName + 'UI()'

        return runCommand

    @classmethod
    def buildPublishList(cls, inline=True, *args, **kwargs):
        ''' build a list of the scripts that are published and some relevent commands '''
        moduleBase = 'lct.src'
        data = []
        toolDictionary = {}

        srcPath = os.path.normpath(os.path.join(os.path.dirname(__file__), os.pardir))

        for subDir in os.listdir(srcPath):
            full = os.path.normpath(os.path.join(srcPath, subDir))
            if os.path.isdir(full):
                if os.path.exists(os.path.normpath(os.path.join(full, subDir + '.conf'))):
                    conf_file = os.path.join(full, subDir + '.conf')
                    conf = {}
                    execfile(conf_file, conf)

                    if conf['publish'] == True:
                        publish = conf['publish']
                        annotation = conf['annotation']
                        prefix = conf['prefix']
                        height = conf['height']
                        toolName = subDir

                        runCommand = cls.build_tool_command(moduleBase, toolName, inline)

                        # list
                        set = [subDir, prefix, annotation, publish, runCommand, height]
                        data.append(set)

                        # dictionary - work in progress
                        toolProperties = {'toolName': subDir, 'prefix': prefix, 'annotation': annotation,
                                          'publish': publish, 'runCommand': runCommand, 'height': height}
                        toolDictionary[subDir] = toolProperties

        return data

    @classmethod
    def exec_tool(cls, toolName, *args, **kwargs):
        ''' '''
        moduleBase = 'lct.src'
        runCommand = cls.build_tool_command(moduleBase, toolName, inline=False)
        exec (runCommand)

    @classmethod
    def relaunch_all_open_tools(cls, *args, **kwargs):
        '''
        '''
        toolList = cls.buildPublishList(inline=False)
        for tool in toolList:
            toolName = tool[0]
            if pm.control(toolName, exists=True):
                cls.exec_tool(toolName)

    @classmethod
    def close_all_open_tools(cls, silent=True, *args, **kwargs):
        '''
        '''
        toolList = cls.buildPublishList(inline=False)
        for tool in toolList:
            toolName = tool[0]
            if pm.control(toolName, exists=True):
                pm.deleteUI(toolName)
        if not silent:
            cls.lc_print('Closing all tools', mode='warning')


class LogManager(object):
    '''
    manage log output from lcToolbox
    '''

    def __init__(self, kind, message):
        """ Initialize class and variables """
        self.kind = kind
        self.message = message
        self.log_url = ""

    def SendLog(self):
        '''
        send a log to a url for processing
        '''
        try:
            if self.kind and self.message:
                data = {}
                data['kind'] = self.kind
                data['user'] = SystemInfo().user
                data['log'] = "<br/>".join(self.message.split("\n"))

                values = urllib.urlencode(data)

                response = urllib2.urlopen(url=self.log_url, data=values).read()
                if response != 'success':
                    Utility.lc_print("PHP Response was Failure", mode='warning')

        except:
            e = sys.exc_info()[1]
            tb = traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback)
            out = ''
            for line in tb:
                out = out + '>>> {}'.format(line)
            Utility.lc_print('{0}\n# Stack Trace:\n{1}'.format("Failed to send", out), mode='error')


class SystemInfo(object):

    def __init__(self):
        ''' '''
        self.ip = self.ip_address()
        self.user = self.user_name()
        self.host = self.host_name()
        self.platform = self.platform_name()
        self.version = self.get_version()
        self.maya = self.maya_version()
        self.geo = self.geo_data()

    def get_text(self):
        ''' '''
        return '{} : {}\nMaya: {}\nUser: {}\nOS: {}\nIP: {}\nGeo: {}, {}, {}'.format(self.version[0],
                                                                                     self.version[1],
                                                                                     self.maya,
                                                                                     self.user,
                                                                                     self.platform,
                                                                                     self.ip,
                                                                                     self.geo['country'],
                                                                                     self.geo['region'],
                                                                                     self.geo['city'])

    def ip_address(self):
        ''' '''
        try:
            ip = urllib2.urlopen("http://api.ipify.org").read()
        except:
            ip = None

        return ip

    def geo_data(self):
        ''' '''
        geo_data_json = urllib2.urlopen("http://ipinfo.io/json").read()
        data = json.loads(geo_data_json)
        return data

    def user_name(self):
        ''' '''
        return getpass.getuser()

    def platform_name(self):
        ''' '''
        return "{} {}".format(platform.system(), platform.release())

    def maya_version(self):
        ''' '''
        return pm.about(version=True)

    def host_name(self):
        ''' '''
        name = None

        if socket.gethostname().find('.') >= 0:
            name = socket.gethostname()
        else:
            name = socket.gethostbyaddr(socket.gethostname())[0]

        return name

    def lct_path(self):
        try:
            currentLocation = os.path.dirname(__file__)
            scriptPath = os.path.normpath(os.path.join(currentLocation, os.pardir, os.pardir, os.pardir))

            lct_path = os.path.normpath(os.path.join(scriptPath, 'lct'))

            if os.path.exists(lct_path):
                return lct_path
            else:
                raise Exception("Path does not exist: {}".format(lct_path))
        except:
            Utility.lc_print_exception()

    def get_version(self):
        '''
            get the current toolset version and release value
        '''

        conf_file = os.path.normpath(os.path.join(self.lct_path(), 'settings', 'lct.conf'))

        release = None
        version = None

        # find the version string for the current installed lct toolset if it exists
        if os.path.exists(conf_file):
            conf = {}
            execfile(conf_file, conf)
            # get the version and release values
            version = conf['version']
            release = conf['release']

        return (release, version)
