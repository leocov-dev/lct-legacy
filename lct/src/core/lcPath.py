import os
import subprocess
import platform
import datetime
import pymel.core as pm

import lct.src.core.lcUtility as lcUtility


class Path:
    ''' '''

    def __init__(self, *args, **kwargs):
        ''' '''
        # self.platform = sys.platform.system()

    @classmethod
    def renameWithTimestamp(cls, filePath, fileName, *args, **kwargs):
        '''
        rename the file with a new name and renameWithTimestamp
        '''
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        extension = os.path.splitext(os.path.basename(filePath))[1]
        newPath = os.path.join(os.path.dirname(filePath), '{}_{}{}'.format(fileName, timestamp, extension))
        os.rename(filePath, newPath)

        return newPath

    @classmethod
    def getSceneName(cls, *args, **kwargs):
        ''' '''
        scenePath = pm.sceneName()
        if scenePath:
            sceneName = os.path.basename(scenePath).split('.')[0]
            return sceneName
        return None

    @classmethod
    def repath(cls, filePath='', newPath='', *args, **kwargs):
        """ replace the entire path to a file """
        if newPath != '':
            fileName = os.path.basename(filePath)
            returnPath = os.path.normpath(os.path.join(newPath, fileName))
            return returnPath
        else:
            return filePath

    @classmethod
    def get_lct_settings_path(cls, *args, **kwargs):
        """
        this is the folder lct_settings next to the lct install folder
        lct/../lct_settings
        """
        currentLocation = os.path.dirname(__file__)
        return os.path.normpath(os.path.join(currentLocation, os.pardir, os.pardir, os.pardir, 'lct_settings'))

    @classmethod
    def get_global_settings_file(cls):
        '''
        get the global tool settings
        '''
        lct_settings_path = cls.get_lct_settings_path()
        return os.path.join(lct_settings_path, 'global.json')

    @classmethod
    def get_tools_settings_file(cls):
        '''
        get the combined tools settings
        '''
        lct_settings_path = cls.get_lct_settings_path()
        return os.path.join(lct_settings_path, 'tools.json')

    @classmethod
    def get_local_settings_file(cls, tool_name):
        '''
        get the local settings for the named tool
        '''
        src = cls.getSrcPath()
        return os.path.join(src, tool_name, '{}.json'.format(tool_name))

    @classmethod
    def getSettingsPath(cls, *args, **kwargs):
        """
        this is the folder lct/settings
        """
        currentLocation = os.path.dirname(__file__)
        settingsPath = os.path.normpath(os.path.join(currentLocation, os.pardir, os.pardir, 'settings'))

        return settingsPath

    @classmethod
    def getMelPath(cls, *args, **kwargs):
        """
        lct/src/mel
        """
        currentLocation = os.path.dirname(__file__)
        melPath = os.path.normpath(os.path.join(currentLocation, os.pardir, 'mel'))

        return melPath

    @classmethod
    def getSrcPath(cls, *args, **kwargs):
        """
        lct/src
        """
        currentLocation = os.path.dirname(__file__)
        srcPath = os.path.normpath(os.path.join(currentLocation, os.pardir))

        return srcPath

    @classmethod
    def browsePathTextField(cls, textField, filter='', caption='', mode=3, *args, **kwargs):
        ''' '''
        path = pm.textField(textField, query=True, text=True)
        if not os.path.exists(path):
            path = os.path.dirname(pm.sceneName())

        path = pm.fileDialog2(ds=1, caption=caption, dir=path, fileFilter=filter, fileMode=mode)

        if path:
            path = path[0]
            pm.textField(textField, edit=True, text=path)
            return path
        return None

    @classmethod
    def validatePathTextField(cls, textField, lct_cfg, configAttr, defaultText):
        '''
        validate the location in the textField, if it does not exist
        update with default text
        '''
        if not os.path.exists(pm.textField(textField, query=True, text=True)):
            pm.textField(textField, edit=True, text=defaultText)
            lct_cfg.set(configAttr, defaultText)

    @classmethod
    def openFilePath(cls, path=None, program=None, *args, **kwargs):
        ''' open a file or path '''
        myPlatform = platform.system()
        if path:
            path = os.path.normpath(path)
            if os.path.exists(path):
                try:
                    if myPlatform.startswith('Win'):
                        if program:
                            try:
                                os.system('start "" "{0}" "{1}"'.format(program, path))
                            except:
                                os.startfile(path)
                        else:
                            os.startfile(path)
                    elif myPlatform.startswith('Darwin'):
                        subprocess.call(('open', path))
                    elif myPlatform.startswith('Linux'):
                        subprocess.call(('xdg-open', path))
                except:
                    pm.warning('some problem opening the file or path: {}'.format(path))
            else:
                pm.warning('path not found: {}'.format(path))
        else:
            pm.warning('no path specified')

    @classmethod
    def openImage(cls, path=None, *args, **kwargs):
        ''' open a file or path '''
        try:
            pm.launchImageEditor(editImageFile=path)
        except:
            lcUtility.Utility.lc_print_exception(
                '>> Check Application Prefs <<\nPSD Editor: {0}\nImage Editor: {1}'.format(
                    pm.optionVar(query='PhotoshopDir'), pm.optionVar(query='EditImageDir')))
