import functools
import math
import os

import pymel.core as pm
from pymel import versions

import lct.src.core.lcConfiguration as lcConfiguration
import lct.src.core.lcPath as lcPath
import lct.src.core.lcPrefs as lcPrefs
import lct.src.core.lcShelf as lcShelf
import lct.src.core.lcUI as lcUI
import lct.src.core.lcUpdate as lcUpdate
import lct.src.core.lcUtility as lcUtility

# init global paths
srcPath = lcPath.Path.getSrcPath()
basePath = os.path.abspath(os.path.dirname(__file__))
iconPath = os.path.normpath(os.path.join(basePath, 'icons'))

# set conf values
conf = lcConfiguration.Conf.load_conf_file(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                                        "{}.conf".format(os.path.basename(__file__).split('.')[0])))

# lct conf values
lct_conf = lcConfiguration.Conf.load_conf_file()

# shelf button command
shelfCommand = 'import lct.src.lcToolbox.lcToolbox as lcTb\nreload(lcTb)\nlcTb.lcToolboxUI()'

# set up configuration
global_cfg = lcConfiguration.GlobalSettingsDictionary()
lct_cfg = lcConfiguration.ConfigurationNode(lcPath.Path.get_tools_settings_file(), global_cfg)
lct_cfg.add('lcToolboxRelease', lct_conf['release'])
lct_cfg.add('lcToolboxCurrentTool', '')
lct_cfg.add('lcToolboxHeight', conf['height'])


def lcToolboxUI(dockable=False, *args, **kwargs):
    """ """
    prefix = conf['prefix']

    ci = 0  # color index iterator
    toolName = 'lcToolbox'
    icon = os.path.join(basePath, 'lcToolbox.png')
    winWidth = 231
    winHeight = conf['height']

    mainWindow = lcUI.lcWindow(prefix=prefix, windowName=toolName, width=winWidth, height=winHeight, icon=icon,
                               shelfCommand=shelfCommand, annotation=conf['annotation'], dockable=dockable,
                               menuBar=True, rtf=True)
    mainWindow.create()

    principalMenus = mainWindow.menuBarLayout.getMenuArray()
    optionsMenu = principalMenus[0]
    helpMenu = principalMenus[-1]

    # add to help menu
    pm.menuItem(parent=helpMenu, divider=True, dividerLabel='Misc')
    pm.menuItem(parent=helpMenu, l='Reset All Tools', image='smallTrash.png',
                command=lambda *args: lct_cfg.reset_all_config())
    pm.menuItem(parent=helpMenu, l='Mini Maya Prefs', command=lambda *args: lcPrefs.MiniPrefsWindow().show())
    if lct_conf['release'] == 'dev':
        pm.menuItem(parent=helpMenu, l='Switch to Pub', image='blendColors.svg',
                    command=lambda *args: lcUpdate.Update.lct_auto_update(confirmDiag=True, releaseSwitch='pub'))

    pm.columnLayout(prefix + '_columnLayout_main')
    mainWindow.show()

    lcTb_open_tool(mainWindow.windowName, lct_cfg.get('lcToolboxHeight'), lct_cfg.get('lcToolboxCurrentTool'))

    # first launch window
    lcUI.UI.lcToolbox_first_launch_window()

    # check for an update
    lcUpdate.Update.update_periodic_check()


def lcTb_open_tool(windowName, heightAdjust, commandString='', *args, **kwargs):
    ''' '''
    prefix = conf['prefix']

    if lcUtility.Utility.maya_version_check():

        if pm.columnLayout(prefix + '_columLayout_holder', exists=True):
            pm.deleteUI(prefix + '_columLayout_holder')
        if pm.formLayout('fl_form', exists=True):
            pm.deleteUI('fl_form')
        if pm.columnLayout('fl_form_shelf', exists=True):
            pm.deleteUI('fl_form_shelf')
        if pm.columnLayout('fl_form_tool', exists=True):
            pm.deleteUI('fl_form_tool')

        pm.setParent(prefix + '_columnLayout_main')

        pm.columnLayout(prefix + '_columLayout_holder', rowSpacing=0)

        pm.formLayout('fl_form', numberOfDivisions=100)
        pm.picture('fl_form_header', image=os.path.join(iconPath, 'header_{}.png'.format(lct_conf['release'])))
        if lct_conf['release'] == 'dev':
            pm.symbolButton('fl_form_reload', image=os.path.join(iconPath, 'reload.png'),
                            command=functools.partial(lcTb_open_tool_new_window, shelfCommand))

        pm.columnLayout('fl_form_shelf')
        shelfHeight = 32
        fl_flow_layout = pm.flowLayout(width=204, height=shelfHeight + 4, wrap=True, columnSpacing=0)

        # list published tools except lcToolbox
        toolList = lcUtility.Utility.buildPublishList(inline=False)
        toolCount = 0
        for item in toolList:
            if item[0] != 'lcToolbox':
                toolCount = toolCount + 1
                toolName = item[0]
                toolPrefix = item[1]
                toolAnnotation = item[2]
                toolHeight = int(item[5])
                toolIcon = os.path.normpath(os.path.join(srcPath, toolName, toolName + '.png'))
                shelfIcon = os.path.normpath(os.path.join(srcPath, toolName, 'icons', toolName + '_shelf.png'))
                toolShelfCommand = "import lct.src.{0}.{0} as {1}\nreload({1})\n{1}.{0}UI()".format(toolName,
                                                                                                    toolPrefix)

                toolExecString = unicode(
                    "import lct.src.{0}.{0} as {1}\nreload({1})\n{1}.{0}UI(asChildLayout=True)".format(toolName,
                                                                                                       toolPrefix))

                toolButton = pm.symbolButton(prefix + '_' + toolName, image=toolIcon, annotation=toolAnnotation,
                                             command=functools.partial(lcTb_open_tool, windowName, toolHeight,
                                                                       toolExecString))
                popup = pm.popupMenu(prefix + '_' + toolName + 'popup', parent=toolButton)
                pm.menuItem(l='Open in new window', parent=popup,
                            command=functools.partial(lcTb_open_tool_new_window, toolShelfCommand))
                pm.menuItem(l='Add to shelf', parent=popup,
                            command=functools.partial(lcShelf.Shelf.makeShelfButton, toolName, toolShelfCommand,
                                                      shelfIcon, toolAnnotation))

                if pm.window(toolName, ex=True):  # if i have the tool window open seperately use the return arrow icon
                    pm.symbolButton(prefix + '_' + toolName, edit=True, image=os.path.normpath(
                        os.path.join(srcPath, toolName, 'icons', toolName + '_Return.png')),
                                    command=functools.partial(lcTb_open_tool, windowName, toolHeight, toolExecString))

                # if i am loading a specific tool back into the window update its icon to standard
                if commandString and toolName in commandString:
                    pm.symbolButton(toolButton, edit=True, image=os.path.normpath(
                        os.path.join(srcPath, toolName, 'icons', toolName + '_Release.png')),
                                    command=functools.partial(lcTb_open_tool_new_window, toolShelfCommand))

        rowCount = max(1, math.ceil(toolCount / 5.0))
        shelfHeight = shelfHeight * rowCount + 4
        pm.flowLayout(fl_flow_layout, edit=True, height=shelfHeight)

        pm.setParent('fl_form')
        fl_form_tool = pm.columnLayout('fl_form_tool', width=224, columnOffset=('left', 10))

        pm.separator(style='double', h=5, w=205)

        if not commandString:
            pm.picture(image=os.path.join(iconPath, 'none.png'))
        else:
            exec commandString in locals()
            lct_cfg.set('lcToolboxCurrentTool', commandString)
            lct_cfg.set('lcToolboxHeight', heightAdjust)

        if lct_conf['release'] == 'dev':
            pm.formLayout('fl_form', edit=True, attachForm=[('fl_form_header', 'top', 0), ('fl_form_shelf', 'top', 54),
                                                            ('fl_form_shelf', 'left', 25), ('fl_form_reload', 'top', 0),
                                                            ('fl_form_reload', 'left', 103)],
                          attachControl=[(fl_form_tool, 'top', 0, 'fl_form_shelf')])
        else:
            pm.formLayout('fl_form', edit=True, attachForm=[('fl_form_header', 'top', 0), ('fl_form_shelf', 'top', 54),
                                                            ('fl_form_shelf', 'left', 25)],
                          attachControl=[(fl_form_tool, 'top', 0, 'fl_form_shelf')])

        pm.setParent(prefix + '_columLayout_holder')
        pm.picture('fl_form_footer', image=os.path.join(iconPath, 'footer_{}.png'.format(lct_conf['release'])))

        pm.window(windowName, edit=True,
                  height=heightAdjust + shelfHeight + 122)  # +conf['height'])#, width=mainWindow.width)
    else:
        pm.separator(style='none', h=30)
        pm.text(l='Your Maya Version:', al='center', w=231, h=25, font='boldLabelFont')
        pm.text(l='{}'.format(versions.shortName()), al='center', w=231, h=10, font='boldLabelFont')
        pm.separator(style='none', h=10)
        pm.text(l='You must have\nMaya 2014 or greater\nto run the\nLEOCOV Toolbox', al='center', w=231, h=60,
                font='boldLabelFont')
        pm.window(windowName, edit=True, height=231)


def lcTb_open_tool_new_window(commandString='', *args, **kwargs):
    ''' '''
    if commandString:
        exec commandString in locals()
