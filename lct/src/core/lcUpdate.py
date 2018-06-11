import datetime
import os
import shutil
import urllib
import urllib2
import webbrowser
import zipfile
from HTMLParser import HTMLParser

import pymel.core as pm

import lct.src.core.lcConfiguration as lcConfiguration
import lct.src.core.lcUtility as lcUtility


class UpdateHTMLParser(HTMLParser):

    # def __init__(self):
    #   self.packages = []

    def fetch_url(self, url):
        self.packages = []

        request = urllib2.Request(url)
        response = urllib2.urlopen(request)
        link = response.geturl()
        html = response.read()
        response.close()
        self.feed(html)  # feed() starts the HTMLParser parsing

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            # Check the list of defined attributes.
            for name, value in attrs:
                # If href is defined, print it.
                if name == "href":
                    if 'lct' in value and not 'latest' in value:
                        self.packages.append(value)


class Update:

    def __init__(self):
        ''' '''

    @classmethod
    def lct_auto_update(cls, confirmDiag=False, releaseSwitch=None, *args, **kwargs):
        ''' '''
        currentLocation = os.path.dirname(__file__)
        scriptPath = os.path.normpath(os.path.join(currentLocation, os.pardir, os.pardir, os.pardir))

        # check if working on leo's machine
        if cls.update_check_working_locally():
            scriptPath = os.path.normpath(os.path.join(os.environ['MAYA_APP_DIR'], 'scripts'))

        # get the current toolset version and release codes
        release, version = cls.update_get_current_version()

        # switch between pub and dev
        if releaseSwitch:
            release = releaseSwitch

        if release:
            # check if there is a new version on the server and get it
            updatePath = cls.update_get_new_version(version=version, release=release)
            if updatePath:
                if confirmDiag:
                    cls.update_confirm_window(release, version, scriptPath, updatePath)
                else:
                    cls.update_unpack_files(scriptPath, updatePath)

    @classmethod
    def update_confirm_window(cls, release, version, scriptPath, updatePath, *args, **kwargs):
        '''
            show a window with update info and user confirm button
        '''
        # settings
        global_cfg = lcConfiguration.GlobalSettingsDictionary(verbose=False)

        # format scriptPath to fit
        scriptPathNice = scriptPath
        if len(scriptPath) > 36:
            scriptPathNice = '....' + scriptPath[-32:]
        # updateURLNice = updatePath.replace('http://', '')
        updateURLNice = updatePath[-24:]

        windowName = 'lct_update'
        if pm.control(windowName, exists=True):
            pm.deleteUI(windowName)

        w = 300
        wB = (w - 200) / 3
        wC = (w - 100) / 2
        h = 280
        updateWindow = pm.window(windowName, t="LCToolbox - Update", widthHeight=[w, h], rtf=False, mnb=False,
                                 mxb=False, s=False, toolbox=True)

        pm.columnLayout()
        pm.text(l='', al='center', w=w)
        pm.text('update_heading', l='*****', al='center', w=w)
        pm.text(l='', al='center', w=w)
        pm.text(l='Release: {}'.format(release), al='center', w=w)
        pm.text(l='', al='center', w=w)
        pm.text(l='Current Version: {}'.format(version), al='center', w=w)

        if updatePath:
            pm.text('update_heading', edit=True, l='UPDATE AVAILABLE', font='boldLabelFont')
            pm.text(l='Update Version: {}'.format(updatePath.split('lct_')[1].split('.zip')[0]), al='center', w=w)
            pm.text(l='', al='center', w=w)
            pm.text(l='Install Path:\n{}'.format(os.path.join(scriptPathNice, 'lct')), al='center', w=w)
            pm.text(l='', al='center', w=w)
            pm.text(l='Update File:\n{}'.format(updateURLNice), al='center', w=w)
            pm.text(l='', al='center', w=w)
            pm.rowColumnLayout(nc=3, cw=([1, 100], [2, 100], [3, 100]))
            pm.text(l='', al='center', w=w)
            pm.button(l='Release Notes', w=100, h=25,
                      command=lambda *args: webbrowser.open('http://lct.leocov.com/release_notes', new=2))
            # pm.text(l='http://lct.leocov.com/release_notes', al='center', hyperlink=True)
            pm.text(l='', al='center', w=w)
            pm.setParent('..')

            pm.text(l='', al='center', w=w)
            pm.rowColumnLayout(nc=5, cw=([1, wB], [2, 100], [3, wB], [4, 100], [5, wB]))
            pm.text(l='', al='center', w=wB)
            pm.button(l='Update', w=100, h=25, command=lambda *args: cls.update_unpack_files(scriptPath, updatePath))
            pm.text(l='', al='center', w=wB)
            pm.button(l='Cancel', w=100, h=25, command=lambda *args: pm.deleteUI(updateWindow))
            pm.text(l='', al='center', w=wB)
        else:
            h = 135
            pm.text('update_heading', edit=True, l='NO UPDATE AVAILABLE', font='boldLabelFont')

            pm.text(l='', al='center', w=w)
            pm.rowColumnLayout(nc=3, cw=([1, wC], [2, 100], [3, wC]))
            pm.text(l='', al='center', w=wC)
            pm.button(l='Close', w=100, h=25, command=lambda *args: pm.deleteUI(updateWindow))
            pm.text(l='', al='center', w=wC)

        pm.setParent('..')
        pm.rowColumnLayout(nc=3, cw=([1, 40], [2, 200]))
        pm.text(l='', w=40)
        pm.checkBox('checkBox_periodic', l='Periodically check for updates?', w=w, h=25, al='center',
                    v=global_cfg.get('g_update_check'),
                    annotation="Periodic update will check for a new version about every 7 days and prompt you to install it.",
                    changeCommand=lambda *args: global_cfg.set('g_update_check',
                                                               pm.checkBox('checkBox_periodic', query=True, v=True)))

        updateWindow.show()
        pm.window(updateWindow, edit=True, h=h, w=(w + 2))

    @classmethod
    def update_unpack_files(cls, scriptPath, updatePath, updateWindow='lct_update', *args, **kwargs):
        '''
            unpack zip files and copy to script path
        '''
        # settings
        global_cfg = lcConfiguration.GlobalSettingsDictionary(verbose=False)

        if pm.control(updateWindow, exists=True):
            pm.deleteUI(updateWindow)

        try:
            folderName = 'lct'
            fileDownload = urllib.urlretrieve(updatePath, os.path.join(scriptPath, 'lct_update.zip'))[0]

            # upgrade lct files
            if os.path.exists(os.path.join(scriptPath, folderName)):  # if the original exists
                if os.path.exists(os.path.join(scriptPath, folderName + '_backup')):  # if the backup exists
                    shutil.rmtree(os.path.join(scriptPath, folderName + '_backup'))  # remove the backup
                # make a new backup
                os.renames(os.path.join(scriptPath, folderName), os.path.join(scriptPath, folderName + '_backup'))

            # unzip new files
            with zipfile.ZipFile(fileDownload) as zf:
                zf.extractall(scriptPath)

            os.remove(fileDownload)

            global_cfg.set('g_first_launch', True)

            lcUtility.Utility.relaunch_all_open_tools()

            msg = 'Update Succeeded'
            log = "{}\n\n{}".format(lcUtility.SystemInfo().get_text(), msg)
            logger = lcUtility.LogManager('lct updated', log)
            logger.SendLog()

        except:
            lcUtility.Utility.lc_print_exception(message='Update Failed')

    @classmethod
    def update_check_working_locally(cls, *args, **kwargs):
        '''
            check if working on my own machine
        '''
        currentLocation = os.path.dirname(__file__)
        scriptPath = os.path.normpath(os.path.join(currentLocation, os.pardir, os.pardir, os.pardir))
        devPath = os.path.normpath("D:/repo")
        if os.path.exists(devPath):
            if devPath == scriptPath:
                return True
        return False

    @classmethod
    def update_get_current_version(cls, *args, **kwargs):
        '''
            get the current toolset version and release value
        '''
        currentLocation = os.path.dirname(__file__)
        scriptPath = os.path.normpath(os.path.join(currentLocation, os.pardir, os.pardir, os.pardir))

        conf_file = os.path.normpath(os.path.join(scriptPath, 'lct', 'settings', 'lct.conf'))

        release = None
        version = None

        # find the version string for the current installed lct toolset if it exists
        if os.path.exists(conf_file):
            conf = lcConfiguration.Conf.load_conf_file(conf_file)
            # get the version and release values
            version = conf['version']
            release = conf['release']

        return (release, version)

    @classmethod
    def update_get_new_version(cls, version, release='pub', updateHttp="", *args,
                               **kwargs):
        '''
            check if there is a new version of the toolkit
        '''
        updateFile = None

        if release == 'dev':
            updateHttp = updateHttp + "dev/"
        if release == 'pub':
            updateHttp = updateHttp + "pub/"

        try:
            parser = UpdateHTMLParser()
            parser.fetch_url(updateHttp)
            for package in parser.packages:
                if package.split('lct_')[1].split('.zip')[0].translate(None, '.') > version.translate(None, '.'):
                    updateFile = package
            if updateFile:
                updateFile = updateHttp + updateFile
        except:
            lcUtility.Utility.lc_print('Web Update Check Failed')

        return updateFile

    @classmethod
    def update_periodic_check(cls, timeDifference=604800, *args, **kwargs):
        '''
        if enough time has elapsed since last check show the update window
        '''

        # settings
        global_cfg = lcConfiguration.GlobalSettingsDictionary(verbose=False)
        update_check = global_cfg.get('g_update_check')

        if update_check:
            currentLocation = os.path.dirname(__file__)
            scriptPath = os.path.normpath(os.path.join(currentLocation, os.pardir, os.pardir, os.pardir))

            conf_file = os.path.normpath(os.path.join(scriptPath, 'lct', 'settings', 'lct.conf'))

            # find the version string for the current installed lct toolset if it exists
            if os.path.exists(conf_file):
                conf = lcConfiguration.Conf.load_conf_file(conf_file)
                # get the conf values
                release = conf['release']
                version = conf['version']
                timestamp = conf['timestamp']

                # gather the times
                now = datetime.datetime.now()  # 2015-04-12 15:35:34.183000
                then = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
                tdelta = now - then
                seconds = tdelta.total_seconds()

                # if enough time has passed
                if seconds > timeDifference:
                    # write new timestamp
                    f = open(conf_file, 'w')
                    f.write("release = '{0}'".format(release))
                    f.write('\n')
                    f.write("version = '{0}'".format(version))
                    f.write('\n')
                    f.write("timestamp = '{0}'".format(now))
                    f.close()
                    # open the update window
                    cls.lct_auto_update(confirmDiag=True)
