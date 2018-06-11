import datetime
import functools
import os
import webbrowser

import pymel.core as pm

import lct.src.core.lcConfiguration as lcConfiguration
import lct.src.core.lcPath as lcPath
import lct.src.core.lcUpdate as lcUpdate
import lct.src.core.lcUtility as lcUtility


class UI(object):
    @classmethod
    def lc_browse_field_button(cls, width, textFieldName, lct_cfg, configAttr, placeholderText,
                               annotation='Browse a path', fileMask='', *args, **kwargs):
        '''
        make a text field and browse button
        return a string path
        '''
        cw2 = 25
        cw1 = width - cw2
        pm.rowColumnLayout(nc=2, cw=([1, cw1], [2, cw2]))
        pm.textField(textFieldName, w=cw2, placeholderText=placeholderText,
                     changeCommand=lambda *args: lct_cfg.set(configAttr,
                                                             pm.textField(textFieldName, query=True, tx=True)))
        pm.symbolButton(image='navButtonBrowse.png', annotation=annotation, w=cw2,
                        command=lambda *args: cls.lc_browse_field_set(textFieldName, lct_cfg, configAttr, fileMask,
                                                                      annotation))

    @classmethod
    def lc_browse_field_set(cls, textFieldName, lct_cfg, configAttr, fileMask='', hint='', *args, **kwargs):
        '''
        '''
        objPath = lcPath.Path.browsePathTextField(textFieldName, fileMask, hint)
        if objPath:
            lct_cfg.set(configAttr, objPath)

    @classmethod
    def lcToolbox_child_popout(cls, mainColumn, windowName, height, commandString, iconPath, lct_cfg, *args, **kwargs):
        '''
        pop out the tool from the lcToolbox
        '''
        import lct.src.lcToolbox.lcToolbox as lcToolbox

        lcToolboxPath = os.path.join(os.path.abspath(os.path.dirname(__file__)), os.pardir, 'lcToolbox',
                                     "lcToolbox.conf")
        conf = lcConfiguration.Conf.load_conf_file(lcToolboxPath)

        srcPath = lcPath.Path.getSrcPath()
        if pm.columnLayout(mainColumn, ex=True) and pm.window(windowName, ex=False) and pm.window('lcToolbox', ex=True):
            pm.deleteUI(mainColumn)
            toolboxHeight = pm.window('lcToolbox', query=True, h=True) - height + conf['height']
            pm.picture(image=os.path.join(srcPath, 'lcToolbox', 'icons', 'none.png'), parent='fl_form_tool')
            pm.symbolButton('lcTb_{}'.format(windowName), edit=True, enable=True,
                            image=os.path.join(iconPath, '{}_Return.png'.format(windowName)),
                            command=functools.partial(lcToolbox.lcTb_open_tool, 'lcToolbox', height, commandString))
            lct_cfg.set(windowName + 'Pop', True)
            lct_cfg.set('lcToolboxHeight', conf['height'])
            lct_cfg.set('lcToolboxCurrentTool', '')
            pm.window('lcToolbox', edit=True, h=toolboxHeight)

    @classmethod
    def lcToolbox_child_menu_edit(cls, asChildLayout, windowName, *args, **kwargs):
        '''
        setup the menus for editing
        '''
        if not asChildLayout:
            # this triggers if the tool has been poped out
            if pm.window('lcToolbox', ex=True):
                # find the menus in lcToolbox window
                principalMenus = pm.window('lcToolbox', query=True, menuArray=True)
                optionsMenu = principalMenus[0]
                optionsMenuList = pm.menu(optionsMenu, query=True, itemArray=True)
                # remove the custom menus
                for item in optionsMenuList[2:]:
                    pm.deleteUI(item)
            # switch to tool's own window menus
            principalMenus = pm.window(windowName, query=True, menuArray=True)
        else:
            # tool is child of lcToolbox, use it's menus
            principalMenus = pm.window('lcToolbox', query=True, menuArray=True)

        optionsMenu = principalMenus[0]
        optionsMenuList = pm.menu(optionsMenu, query=True, itemArray=True)
        # not handling help menu at this time
        helpMenu = None
        # remove custom menus to avoid duplication
        for item in optionsMenuList[2:]:
            pm.deleteUI(item)

        return (optionsMenu, helpMenu)

    @classmethod
    def lcToolbox_first_launch_window(cls, force_show=False, *args, **kwargs):
        '''
            show a window with first lauch settings
        '''
        # settings
        global_cfg = lcConfiguration.GlobalSettingsDictionary(verbose=False)

        windowName = 'lct_first_launch'
        if pm.control(windowName, exists=True):
            pm.deleteUI(windowName)

        show_window = global_cfg.get('g_first_launch')

        if force_show:
            show_window = True

        if show_window:
            w = 300
            h = 262
            margins = 8
            middle = w - (margins * 2)

            updateWindow = pm.window(windowName, t="LCToolbox - Welcome", widthHeight=[w, h], rtf=False, mnb=False,
                                     mxb=False, s=False, toolbox=True)

            pm.rowColumnLayout(nc=3, cw=([1, margins], [2, middle], [3, margins + 2]))
            # first column
            pm.text(l='', w=margins)

            # middle column
            pm.columnLayout()

            pm.text(l='Welcome to LCToolbox', al='center', w=middle, h=50, font='boldLabelFont')

            pm.text(l='Please read the License and Privacy Policy', al='center', w=middle, h=25)

            pm.button(l='License', al='center', w=middle,
                      command=lambda *args: webbrowser.open('http://lct.leocov.com/license', new=2))
            pm.text(l='', w=middle, h=8)
            pm.button(l='Privacy Policy', al='center', w=middle,
                      command=lambda *args: webbrowser.open('http://lct.leocov.com/privacy', new=2))
            pm.text(l='', w=middle, h=8)
            pm.button(l='Release Notes', w=middle, bgc=(0.5, 0.3, 0.3),
                      command=lambda *args: webbrowser.open('http://lct.leocov.com/release_notes', new=2))
            pm.text(l='', w=middle, h=8)

            pm.checkBox('checkBox_errors', l='Do you consent to automatically send error logs?', w=middle, h=25,
                        al='center', v=global_cfg.get('g_send_errors'),
                        annotation="Send error logs for critical excepton to the developer, some personal information is logged. See Privacy Policy for details.",
                        bgc=(0.5, 0.3, 0.3), changeCommand=lambda *args: global_cfg.set('g_send_errors',
                                                                                        pm.checkBox('checkBox_errors',
                                                                                                    query=True,
                                                                                                    v=True)))

            # pm.checkBox('checkBox_scene_settings', l='Save tool settings in Maya scene node?', w=middle, h=25, al='center', v=global_cfg.get('g_scene_settings'), annotation="Settings can be saved globally or as unique to each scene file in a script node.", changeCommand=lambda *args: global_cfg.set('g_scene_settings', pm.checkBox('checkBox_scene_settings', query=True, v=True)))

            pm.text(l='', w=middle, h=15)

            pm.checkBox('checkBox_first_launch', l='Show this window at launch?', w=middle, h=25, al='center',
                        v=global_cfg.get('g_first_launch'), annotation="Hide this window until after an update.",
                        bgc=(0.3, 0.5, 0.3), changeCommand=lambda *args: global_cfg.set('g_first_launch', pm.checkBox(
                    'checkBox_first_launch', query=True, v=True)))

            pm.setParent('..')

            # last column
            pm.text(l='', w=margins)

            updateWindow.show()
            pm.window(updateWindow, edit=True, h=h, w=(w + 2))


class lcDialog(object):

    def __init__(self, kind, *args, **kwargs):
        '''
        '''
        self.kwargs = kwargs
        self.kind = kind
        self.progress = None


class lcWindow(object):

    def __init__(self, prefix, windowName, width, height, icon, shelfCommand, annotation=' ', dockable=False,
                 menuBar=False, mnb=False, mxb=False, s=False, rtf=False, startArea='right', allowedAreas='all',
                 floating=False, *args, **kwargs):
        """ Initialize class and variables """
        self.kwargs = kwargs
        self.windowName = windowName
        self.dockName = windowName + 'Dock'
        self.width = width
        self.height = height
        self.icon = icon
        self.prefix = prefix
        self.shelfCommand = shelfCommand
        self.annotation = annotation
        self.dockable = dockable
        self.menuBar = menuBar
        self.mnb = mnb
        self.mxb = mxb
        self.sizeable = s
        self.rtf = rtf
        self.startArea = startArea
        self.allowedAreas = allowedAreas
        self.floating = floating

        # store for use outside
        self.toolName = windowName
        self.mainWindow = ''
        self.menuBarLayout = ''
        self.prinipalMenus = None

        self.global_cfg = lcConfiguration.GlobalSettingsDictionary()
        self.lct_cfg = lcConfiguration.ConfigurationNode(lcPath.Path.get_tools_settings_file(), self.global_cfg)

        self.srcPath = lcPath.Path.getSrcPath()

    def create(self, *args, **kwargs):
        ''' '''
        if pm.control(self.windowName, exists=True):
            pm.deleteUI(self.windowName)
        if pm.control(self.dockName, exists=True):
            pm.deleteUI(self.dockName)

        if self.dockable:
            self.mainWindow = pm.window(self.windowName, t=self.windowName)
        else:
            self.mainWindow = pm.window(self.windowName, t=self.windowName, widthHeight=[self.width, self.height],
                                        rtf=self.rtf, mnb=self.mnb, mxb=self.mxb, s=self.sizeable, **self.kwargs)

        if self.menuBar:
            self.menuBarLayout = pm.menuBarLayout(self.prefix + '_menuBarLayout')
            #### Help menu
            pm.menu(self.prefix + '_help', l='Help', helpMenu=True)
            pm.menuItem(parent=self.prefix + '_help', l='Online Help', image='help.png',
                        command=lambda *args: webbrowser.open('http://lct.leocov.com/help', new=2))
            pm.menuItem(parent=self.prefix + '_help', l='Contact / Bug Report',
                        image=os.path.join(self.srcPath, 'icons', 'lc_bug.png'),
                        command=lambda *args: self.bug_report_window())
            errorLogMenuItem = pm.menuItem(parent=self.prefix + '_help', l='Send Error Logs',
                                           checkBox=self.global_cfg.get('g_send_errors'),
                                           annotation="Automatically send error logs to the developer",
                                           command=lambda *args: self.global_cfg.set('g_send_errors',
                                                                                     pm.menuItem(errorLogMenuItem,
                                                                                                 q=True,
                                                                                                 checkBox=True)))
            updateMenuItem = pm.menuItem(parent=self.prefix + '_help', l='Update', enable=False, image='',
                                         command=lambda *args: lcUpdate.Update.lct_auto_update(confirmDiag=True))
            pm.menuItem(parent=self.prefix + '_help', l='About', image='channelBox.png',
                        command=lambda *args: self.about())
            #### Options menu
            pm.menu(self.prefix + '_options', l='Options')
            sceneSettingsMenuItem = pm.menuItem(parent=self.prefix + '_options', l="Use scene settings node",
                                                checkBox=self.global_cfg.get('g_scene_settings'),
                                                annotation="Store tool settings in a scene node. This applies to all scenes.",
                                                command=lambda *args: self.global_cfg.set('g_scene_settings',
                                                                                          pm.menuItem(
                                                                                              sceneSettingsMenuItem,
                                                                                              q=True, checkBox=True)))
            pm.menuItem(parent=self.prefix + '_options', l='Reset {0}'.format(self.windowName), image='airField.svg',
                        command=lambda *args: self.lct_cfg.reset_tool_config(self.windowName))
            # pm.menuItem(parent = self.prefix+'_options', l='Make Shelf Icon', command=lambda *args: lcShelf.Shelf.makeShelfButton(self.windowName, self.shelfCommand, self.icon, self.annotation) )

            # get the current toolset version and release codes
            release, version = lcUpdate.Update.update_get_current_version()
            if release:
                # check if there is a new version on the server and get it
                updatePath = lcUpdate.Update.update_get_new_version(version=version, release=release)
                if updatePath:
                    pm.menuItem(updateMenuItem, edit=True, l='Update Available', enable=True,
                                image='activeSelectedAnimLayer.png')

    def show(self, *args, **kwargs):
        ''' '''
        if self.dockable:
            mainDock = pm.dockControl(self.dockName, label=self.windowName, area=self.startArea,
                                      content=self.mainWindow, allowedArea=self.allowedAreas, floating=self.floating,
                                      w=self.width, h=self.height)
        else:
            self.mainWindow.show()

    def about(self, *args, **kwargs):
        ''' '''
        now = datetime.datetime.now()
        year = now.year
        release, version = lcUpdate.Update.update_get_current_version()
        aboutName = 'lct_about'

        w = 220
        h = 243

        if pm.control(aboutName, exists=True):
            pm.deleteUI(aboutName)

        aboutWindow = pm.window(aboutName, t="LEOCOV Toolbox - About", widthHeight=[w, h], rtf=False, mnb=False,
                                mxb=False, s=False, toolbox=True)

        pm.columnLayout(w=w, cw=w, cal='center')
        pm.text(l='', al='center', w=w)
        pm.text(l='LEOCOV Toolbox', al='center', w=w)
        pm.text(l='', al='center', w=w)
        pm.text(l='Release: {}'.format(release), al='center', w=w)
        pm.text(l='Version: {}'.format(version), al='center', w=w)
        pm.text(l='', al='center', w=w)
        pm.button(l='License', al='center', w=w,
                  command=lambda *args: webbrowser.open('http://lct.leocov.com/license', new=2))
        pm.button(l='Privacy Policy', al='center', w=w,
                  command=lambda *args: webbrowser.open('http://lct.leocov.com/privacy', new=2))
        pm.button(l='Release Notes', w=w,
                  command=lambda *args: webbrowser.open('http://lct.leocov.com/release_notes', new=2))
        pm.button(l='First Launch Window', al='center', w=w,
                  command=lambda *args: UI.lcToolbox_first_launch_window(force_show=True))

        pm.text(l='', al='center', w=w)
        pm.text(l='Leonardo Covarrubias - {} {}'.format("Copyright", year), al='center', w=w)
        pm.text(l='', al='center', w=w)

        pm.rowColumnLayout(nc=3, cw=([1, 60], [2, 100], [3, 60]))
        pm.text(l='', al='center', w=50)
        pm.button('about_close', l='Close', w=100, h=25, command=lambda *args: pm.deleteUI(aboutWindow))
        pm.text(l='', al='center', w=50)

        aboutWindow.show()
        pm.window(aboutWindow, edit=True, h=h, w=(w + 2))

    def bug_report_window(self):
        ''' '''
        windowName = 'bugWindow'

        w = 400
        h = 330

        if pm.control(windowName, exists=True):
            pm.deleteUI(windowName)

        bug_window = pm.window(windowName, t="Bug Report / Contact", widthHeight=[w, h], rtf=False, mnb=False,
                               mxb=False, s=False, toolbox=True)

        pm.columnLayout(w=w, cw=w, cal='center')
        wM = (w - 30)
        pm.rowColumnLayout(nc=3, cw=([1, 15], [2, wM], [3, 15]))
        pm.text(l='', w=15)

        pm.columnLayout(w=wM, cw=wM, cal='center')

        pm.text(l='Message or Bug:', w=wM, h=30, al='left', font='boldLabelFont')
        message_text = pm.scrollField(w=wM, wordWrap=True)

        pm.text(l='Email Address (Optional, if you want a reply):', w=wM, h=30, al='left', font='boldLabelFont')
        email_address = pm.textField(w=wM)

        pm.setParent('..')

        pm.text(l='', w=15)

        pm.setParent('..')

        pm.separator(style='none', h=12, w=wM)

        cwA = 10
        cwB = (w / 2) - (1.5 * cwA)
        pm.rowColumnLayout(nc=5, cw=([1, cwA], [2, cwB], [3, cwA], [4, cwB], [5, cwA]))
        pm.text(l='', w=cwA)
        pm.button('bug_send', l='Send', w=cwB, h=25, command=lambda *args: self.bug_report_send(windowName,
                                                                                                pm.textField(
                                                                                                    email_address,
                                                                                                    query=True,
                                                                                                    text=True),
                                                                                                pm.scrollField(
                                                                                                    message_text,
                                                                                                    query=True,
                                                                                                    text=True)))
        pm.text(l='', w=cwA)
        pm.button('bug_cancel', l='Cancel', w=cwB, h=25, command=lambda *args: pm.deleteUI(windowName))
        pm.text(l='', w=cwA)

        bug_window.show()
        pm.window(bug_window, edit=True, h=h, w=(w + 2))

    def bug_report_send(self, window, email_address, message_text):
        ''' '''
        if message_text:

            if not email_address:
                email_address = 'None Supplied'

            log = "{}\n{}\n\n{}".format(lcUtility.SystemInfo().get_text(), "Email: {}".format(email_address),
                                        message_text)
            logger = lcUtility.LogManager('lct bug report', log)
            logger.SendLog()

            pm.deleteUI(window)
        else:
            lcUtility.Utility.lc_print("The message box can not be blank", mode='warning')
