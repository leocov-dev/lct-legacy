import functools
import os

import pymel.core as pm

import lct.src.core.lcColor as lcColor
import lct.src.core.lcConfiguration as lcConfiguration
import lct.src.core.lcPath as lcPath
import lct.src.core.lcString as lcString
import lct.src.core.lcUI as lcUI
import lct.src.core.lcUtility as lcUtility

# interface colors
hue = 0.5
colorWheel = lcColor.ColorWheel(divisions=9, hueRange=[hue, hue], satRange=[0.2, 0.5], valRange=[0.5, 0.5])

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
lct_cfg.add('lcRenamePop', False)
lct_cfg.add('lcRenameSearch', '')
lct_cfg.add('lcRenameReplace', '')
lct_cfg.add('lcRenameRemUnderscore', False)
lct_cfg.add('lcRenamePrefix', '')
lct_cfg.add('lcRenameSuffix', '')
lct_cfg.add('lcRenameRename', '')
lct_cfg.add('lcRenameStart', 1)
lct_cfg.add('lcRenamePadding', 2)
lct_cfg.add('lcRenameToken', '')


def lcRenameUI(dockable=False, asChildLayout=False, *args, **kwargs):
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

    pm.text(l='--- Rename ---', align='center', w=w, h=20, font='boldLabelFont', bgc=colorWheel.darkgrey)
    pm.separator(style='none', h=3)

    # Search and Replace
    a = 50
    b = w - a
    pm.rowColumnLayout(nc=2, cw=([1, a], [2, b]))
    pm.text(l='Search: ', align='right', w=a)
    pm.textField(prefix + '_textField_search', w=b, cc=lambda *args: lct_cfg.set('lcRenameSearch', pm.textField(
        prefix + '_textField_search', q=True, tx=True)))
    pm.text(l='Replace: ', align='right', w=a)
    pm.textField(prefix + '_textField_replace', w=b, cc=lambda *args: lct_cfg.set('lcRenameReplace', pm.textField(
        prefix + '_textField_replace', q=True, tx=True)))
    pm.setParent(prefix + '_columnLayout_main')

    a = 185
    b = w - a
    pm.rowColumnLayout(nc=2, cw=([1, a], [2, b]))
    pm.text(l='Remove leading and trailing _  ', w=a, align='right')
    pm.checkBox(prefix + '_checkBox_rem_underscore', l='', cc=lambda *args: lct_cfg.set('lcRenameRemUnderscore',
                                                                                        pm.checkBox(
                                                                                            prefix + '_checkBox_rem_underscore',
                                                                                            q=True, v=True)))
    pm.setParent(prefix + '_columnLayout_main')

    a = (w / 2)
    b = w - a
    pm.rowColumnLayout(nc=2, cw=([1, a], [2, b]))
    pm.button(l='Rename All', command=functools.partial(lcReNm_search_and_replace, 'all'), bgc=colorWheel.getPrev())
    pm.button(l='Rename Selected', command=functools.partial(lcReNm_search_and_replace, 'selected'),
              bgc=colorWheel.getPrev())

    pm.setParent(prefix + '_columnLayout_main')
    pm.separator(style='none', h=10)

    # Suffix and Prefix
    a = 50
    b = (w / 2) - a
    pm.rowColumnLayout(nc=4, cw=([1, a], [2, b], [3, a], [4, b]))
    pm.text(l='Prefix_: ', align='right', w=a)
    pm.textField(prefix + '_textField_prefix', w=b, cc=lambda *args: lct_cfg.set('lcRenamePrefix', pm.textField(
        prefix + '_textField_prefix', q=True, tx=True)))
    pm.text(l='_Suffix: ', align='right', w=a)
    pm.textField(prefix + '_textField_suffix', w=b, cc=lambda *args: lct_cfg.set('lcRenameSuffix', pm.textField(
        prefix + '_textField_suffix', q=True, tx=True)))
    pm.setParent(prefix + '_columnLayout_main')

    a = (w / 2)
    b = w - a
    pm.rowColumnLayout(nc=2, cw=([1, a], [2, b]))
    pm.button(l='Add Prefix', c=functools.partial(lcReNm_add_prefix), bgc=colorWheel.getPrev())
    pm.button(l='Add Suffix', c=functools.partial(lcReNm_add_suffix), bgc=colorWheel.getPrev())

    pm.setParent(prefix + '_columnLayout_main')
    pm.separator(style='none', h=10)

    # Rename and Number
    a = 50
    b = w - a
    pm.rowColumnLayout(nc=2, cw=([1, a], [2, b]))
    pm.text(l='Rename: ', align='right', w=a)
    pm.textField(prefix + '_textField_rename', w=b, cc=lambda *args: lct_cfg.set('lcRenameRename', pm.textField(
        prefix + '_textField_rename', q=True, tx=True)))
    pm.setParent(prefix + '_columnLayout_main')

    a = 70
    b = (w / 2) - a
    pm.rowColumnLayout(nc=4, cw=([1, a], [2, b], [3, a], [4, b]))
    pm.text(l='Start From #: ', align='right', w=a)
    pm.intField(prefix + '_intField_start', w=b,
                cc=lambda *args: lct_cfg.set('lcRenameStart', pm.intField(prefix + '_intField_start', q=True, v=True)))
    pm.text(l='Padding: ', align='right', w=a)
    pm.intField(prefix + '_intField_pad', w=b,
                cc=lambda *args: lct_cfg.set('lcRenamePadding', pm.intField(prefix + '_intField_pad', q=True, v=True)))
    pm.setParent(prefix + '_columnLayout_main')
    pm.button(l='Rename and Number', w=w, c=functools.partial(lcReNm_rename_and_number), bgc=colorWheel.getPrev())
    pm.separator(style='in', h=10, w=w)

    # Hump and Underscore
    pm.text(l='--- Swap Style ---', align='center', w=w, h=20, font='boldLabelFont', bgc=colorWheel.darkgrey)
    pm.separator(style='none', h=3)
    a = (w / 2)
    b = w - a
    pm.rowColumnLayout(nc=2, cw=([1, a], [2, b]))
    pm.button(l='> CamelCase', annotation='Swap undersocres with camelCase', c=functools.partial(lcReNm_to_camel_case),
              bgc=colorWheel.getPrev())
    pm.button(l='> Underscore', annotation='Swap camelCase with undersocres', c=functools.partial(lcReNm_to_underscore),
              bgc=colorWheel.getPrev())
    pm.setParent(prefix + '_columnLayout_main')
    pm.separator(style='in', h=10, w=w)

    # Hide by Token
    pm.text(l='--- Hide by Token ---', align='center', w=w, h=20, font='boldLabelFont', bgc=colorWheel.darkgrey)
    pm.separator(style='none', h=3)
    a = (w - 70)
    b = (w - a) / 2
    c = b
    pm.rowColumnLayout(nc=3, cw=([1, a], [2, b], [2, b]))
    pm.textField(prefix + '_textField_token', w=a, placeholderText='Search Token, e.g. hi_',
                 cc=lambda *args: lct_cfg.set('lcRenameToken',
                                              pm.textField(prefix + '_textField_token', q=True, tx=True)))
    pm.button(l='Hide', w=b, c=functools.partial(lcReNm_token_show_hide, 'hide'), bgc=colorWheel.getPrev())
    pm.button(l='Show', w=c, c=functools.partial(lcReNm_token_show_hide, 'show'), bgc=colorWheel.getPrev())
    pm.setParent(prefix + '_columnLayout_main')

    #
    if not asChildLayout:
        mainWindow.show()
        pm.window(mainWindow.mainWindow, edit=True, h=winHeight, w=winWidth)
    else:
        pm.separator(style='none', h=5)
        pm.setParent('..')
        pm.setParent('..')

    # edit menus
    optionsMenu, helpMenu = lcUI.UI.lcToolbox_child_menu_edit(asChildLayout, windowName)

    # restore interface from lct_cfg
    pm.textField(prefix + '_textField_search', edit=True, text=lct_cfg.get('lcRenameSearch'))
    pm.textField(prefix + '_textField_replace', edit=True, text=lct_cfg.get('lcRenameReplace'))
    pm.checkBox(prefix + '_checkBox_rem_underscore', edit=True, v=lct_cfg.get('lcRenameRemUnderscore'))
    pm.textField(prefix + '_textField_prefix', edit=True, text=lct_cfg.get('lcRenamePrefix'))
    pm.textField(prefix + '_textField_suffix', edit=True, text=lct_cfg.get('lcRenameSuffix'))
    pm.textField(prefix + '_textField_rename', edit=True, text=lct_cfg.get('lcRenameRename'))
    pm.intField(prefix + '_intField_start', edit=True, v=lct_cfg.get('lcRenameStart'))
    pm.intField(prefix + '_intField_pad', edit=True, v=lct_cfg.get('lcRenamePadding'))
    pm.textField(prefix + '_textField_token', edit=True, text=lct_cfg.get('lcRenameToken'))


def lcReNm_search_and_replace(mode, *args, **kwargs):
    ''' '''
    searchTerm = pm.textField(prefix + '_textField_search', query=True, text=True)
    replaceTerm = pm.textField(prefix + '_textField_replace', query=True, text=True)
    underscore = pm.checkBox(prefix + '_checkBox_rem_underscore', query=True, value=True)
    itemList = None

    pm.undoInfo(chunkName='lcUndo_search_and_replace', openChunk=True)

    if mode == 'selected':
        itemList = pm.ls(sl=True)
    if mode == 'all':
        itemList = pm.ls(transforms=True, textures=True, materials=True)

    if itemList:
        for item in itemList:
            try:
                oldName = str(item)
                newName = lcString.String.search_and_replace(item, searchTerm, replaceTerm, underscore)
                if newName != oldName:
                    newName = pm.rename(item, newName)
                    lcUtility.Utility.lc_print('Renamed: {0} > {1}'.format(oldName, newName))
            except:
                lcUtility.Utility.lc_print_exception('Could not rename {}'.format(item))
                pm.undoInfo(chunkName='lcUndo_search_and_replace', closeChunk=True)

    pm.undoInfo(chunkName='lcUndo_search_and_replace', closeChunk=True)


def lcReNm_add_prefix(*args, **kwargs):
    ''' '''
    addPrefix = pm.textField(prefix + '_textField_prefix', query=True, text=True)
    itemList = pm.ls(sl=True)

    pm.undoInfo(chunkName='lcUndo_prefix', openChunk=True)

    if itemList:
        for item in itemList:
            try:
                oldName = str(item)
                newName = lcString.String.add_prefix(oldName, addPrefix)
                if newName != oldName:
                    newName = pm.rename(item, newName)
                    lcUtility.Utility.lc_print('Renamed: {0} > {1}'.format(oldName, newName))
            except:
                lcUtility.Utility.lc_print_exception('Could not add prefix {}'.format(item))
                pm.undoInfo(chunkName='lcUndo_prefix', closeChunk=True)

    pm.undoInfo(chunkName='lcUndo_prefix', closeChunk=True)


def lcReNm_add_suffix(*args, **kwargs):
    ''' '''
    addSuffix = pm.textField(prefix + '_textField_suffix', query=True, text=True)
    itemList = pm.ls(sl=True)

    pm.undoInfo(chunkName='lcUndo_prefix', openChunk=True)

    if itemList:
        for item in itemList:
            try:
                oldName = str(item)
                newName = lcString.String.add_suffix(oldName, addSuffix)
                if newName != oldName:
                    newName = pm.rename(item, newName)
                    lcUtility.Utility.lc_print('Renamed: {0} > {1}'.format(oldName, newName))
            except:
                lcUtility.Utility.lc_print_exception('Could not add suffix {}'.format(item))
                pm.undoInfo(chunkName='lcUndo_prefix', closeChunk=True)

    pm.undoInfo(chunkName='lcUndo_prefix', closeChunk=True)


def lcReNm_rename_and_number(*args, **kwargs):
    ''' '''
    itemList = pm.ls(sl=True)
    nameBase = pm.textField(prefix + '_textField_rename', q=True, tx=True)
    counter = pm.intField(prefix + '_intField_start', q=True, v=True)
    padding = pm.intField(prefix + '_intField_pad', q=True, v=True)

    pm.undoInfo(chunkName='lcUndo_number', openChunk=True)

    if itemList:
        for item in itemList:
            try:
                oldName = str(item)
                newName = nameBase
                if not nameBase:
                    newName = oldName + "_"
                newName = lcString.String.rename_and_number(newName, counter, padding)
                counter = counter + 1
                if newName != oldName:
                    newName = pm.rename(item, newName)
                    lcUtility.Utility.lc_print('Renamed: {0} > {1}'.format(oldName, newName))
            except:
                lcUtility.Utility.lc_print_exception('Could not rename {}'.format(item))
                pm.undoInfo(chunkName='lcUndo_number', closeChunk=True)

    pm.undoInfo(chunkName='lcUndo_number', closeChunk=True)


def lcReNm_to_camel_case(*args, **kwargs):
    ''' '''
    itemList = pm.ls(sl=True)

    pm.undoInfo(chunkName='lcUndo_number', openChunk=True)

    if itemList:
        for item in itemList:
            try:
                oldName = str(item)
                parts = oldName.split('_')
                if len(parts) > 1:
                    newName = ''.join([p.capitalize() for p in parts])
                else:
                    newName = oldName
                print newName
                if newName != oldName:
                    newName = pm.rename(item, newName)
                    lcUtility.Utility.lc_print('Renamed: {0} > {1}'.format(oldName, newName))
            except:
                lcUtility.Utility.lc_print_exception('Could not rename {}'.format(item))
                pm.undoInfo(chunkName='lcUndo_number', closeChunk=True)

    pm.undoInfo(chunkName='lcUndo_number', closeChunk=True)


def lcReNm_to_underscore(*args, **kwargs):
    ''' '''
    itemList = pm.ls(sl=True)

    pm.undoInfo(chunkName='lcUndo_number', openChunk=True)

    if itemList:
        for item in itemList:
            try:
                oldName = str(item)
                digits = lcString.String.split_at_digits(oldName)
                caps = []
                for d in digits:
                    caseList = lcString.String.split_at_uppercase(d)
                    for c in caseList:
                        caps.append(c)
                print caps
                newName = '_'.join(caps)
                print newName
                if newName != oldName:
                    newName = pm.rename(item, newName)
                    lcUtility.Utility.lc_print('Renamed: {0} > {1}'.format(oldName, newName))
            except:
                lcUtility.Utility.lc_print_exception('Could not rename {}'.format(item))
                pm.undoInfo(chunkName='lcUndo_number', closeChunk=True)

    pm.undoInfo(chunkName='lcUndo_number', closeChunk=True)


def lcReNm_token_show_hide(mode, *args, **kwargs):
    ''' '''
    token = pm.textField(prefix + '_textField_token', q=True, tx=True)

    if mode == 'show':
        itemList = pm.ls(invisible=True, transforms=True)
        for item in itemList:
            if token and token in str(item):
                item.visibility.set(True)

    if mode == 'hide':
        itemList = pm.ls(visible=True, transforms=True)
        for item in itemList:
            if token and token in str(item):
                item.visibility.set(False)
