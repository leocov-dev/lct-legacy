import os

import pymel.core as pm

import lct.src.core.lcColor as lcColor
import lct.src.core.lcConfiguration as lcConfiguration
import lct.src.core.lcPath as lcPath
import lct.src.core.lcUI as lcUI

# interface colors
kw = {'hue': 0.70, 'saturation': 0.5, 'value': 0.5}
colorWheel = lcColor.ColorWheel(15, **kw)

# set conf values
conf = lcConfiguration.Conf.load_conf_file(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                                        "{}.conf".format(os.path.basename(__file__).split('.')[0])))
publish = conf['publish']
annotation = conf['annotation']
prefix = conf['prefix']
height = conf['height']

# set paths
srcPath = lcPath.Path.getSrcPath()
basePath = os.path.abspath(os.path.dirname(__file__))
iconPath = os.path.normpath(os.path.join(basePath, 'icons'))
fileName = os.path.splitext(os.path.basename(__file__))[0]

# setup configuration node and add necessary attributes
global_cfg = lcConfiguration.GlobalSettingsDictionary()
lct_cfg = lcConfiguration.ConfigurationNode(lcPath.Path.get_tools_settings_file(), global_cfg)
lct_cfg.add('lcPolyBakePop', False)


def lcPolyBakeUI(dockable=False, asChildLayout=False, *args, **kwargs):
    """ """

    ci = 0  # color index iterator
    windowName = fileName
    shelfCommand = 'import lct.src.{0}.{0} as {1}\nreload({1})\n{1}.{0}UI()'.format(windowName, prefix)
    commandString = 'import lct.src.{0}.{0} as {1}\nreload({1})\n{1}.{0}UI(asChildLayout=True)'.format(windowName,
                                                                                                       prefix)
    icon = os.path.join(basePath, '{}.png'.format(fileName))
    winWidth = 205
    winHeight = height

    if pm.window(windowName, ex=True):
        pm.deleteUI(windowName)

    if not asChildLayout:
        lcUI.UI.lcToolbox_child_popout(prefix + '_columnLayout_main', windowName, height, commandString, iconPath,
                                       lct_cfg)
        mainWindow = lcUI.lcWindow(prefix=prefix, windowName=windowName, width=winWidth, height=winHeight, icon=icon,
                                   shelfCommand=shelfCommand, annotation=annotation, dockable=dockable, menuBar=True)
        mainWindow.create()

    #
    pm.columnLayout(prefix + '_columnLayout_main')
    w = 200
    pm.text(l='', h=25)
    pm.text(l=windowName, w=w, h=25, align='center', font='boldLabelFont')
    pm.text(l='In Development', w=w, h=25, align='center', font='boldLabelFont')
    pm.text(l='', h=75)

    # Show Window
    if not asChildLayout:
        mainWindow.show()
        # force height and width
        pm.window(mainWindow.mainWindow, edit=True, h=winHeight, w=winWidth)
    else:
        pm.separator(style='none', h=5)
        pm.setParent('..')
        pm.setParent('..')

    # edit menus
    optionsMenu, helpMenu = lcUI.UI.lcToolbox_child_menu_edit(asChildLayout, windowName)

    # restore interface from lct_cfg
