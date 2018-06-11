import os

import pymel.core as pm

import lct.src.core.lcColor as lcColor
import lct.src.core.lcConfiguration as lcConfiguration
import lct.src.core.lcPath as lcPath
import lct.src.core.lcPrefs as lcPrefs
import lct.src.core.lcShader as lcShader
import lct.src.core.lcTexture as lcTexture
import lct.src.core.lcUI as lcUI

# interface colors
hue = 0.3
colorWheel = lcColor.ColorWheel(divisions=9, hueRange=[hue, hue], satRange=[0.2, 0.5], valRange=[0.4, 0.6])

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

defaultPath = 'Re-Path Dir . . .'
defaultPrefix = 'tx'

# setup configuration node and add necessary attributes
global_cfg = lcConfiguration.GlobalSettingsDictionary()
lct_cfg = lcConfiguration.ConfigurationNode(lcPath.Path.get_tools_settings_file(), global_cfg)
lct_cfg.add('lcTextureToolsPop', False)
lct_cfg.add('lcTextureToolsRepath', '')
lct_cfg.add('lcTextureToolsPrefix', '')
lct_cfg.add('lcTextureToolsShaderRepath', '')


def lcTextureToolsUI(dockable=False, asChildLayout=False, *args, **kwargs):
    ''' '''
    global lct_cfg
    global prefix
    global height
    global defaultPath
    global defaultPrefix

    ci = 0  # color index iterator
    windowName = 'lcTextureTools'
    shelfCommand = 'import lct.src.{0}.{0} as {1}\nreload({1})\n{1}.{0}UI()'.format(windowName, prefix)
    commandString = 'import lct.src.{0}.{0} as {1}\nreload({1})\n{1}.{0}UI(asChildLayout=True)'.format(windowName,
                                                                                                       prefix)
    icon = os.path.join(basePath, 'lcTextureTools.png')
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

    # RENAME TEXTURE NODES
    pm.text(l='- Rename File Texture Nodes -', font='boldLabelFont', al='center', w=200, h=20, bgc=colorWheel.darkgrey)
    pm.separator(style='none', h=3, w=200)

    pm.rowColumnLayout(nc=3, cw=([1, 40], [2, 110], [3, 50]))
    pm.textField(prefix + '_textField_prefix', placeholderText=defaultPrefix,
                 changeCommand=lambda *args: lct_cfg.set('lcTextureToolsPrefix',
                                                         pm.textField(prefix + '_textField_prefix', query=True,
                                                                      tx=True)),
                 receiveFocusCommand=lambda *args: lcTxT_rename_focus())
    pm.text(l="_'texture_file_name'")
    pm.button(prefix + '_button_rename', l='Rename', bgc=colorWheel.getColorRGB(ci),
              annotation='rename all file texture nodes', w=50,
              command=lambda *args: lcTxT_rename_textures(pm.textField(prefix + '_textField_prefix', q=True, tx=True)))
    ci += 1
    pm.setParent(prefix + '_columnLayout_main')
    pm.separator(style='in', h=8, w=200)

    # REPATH TEXTURE NODES
    pm.text(l='- Set new path for File Textures -', font='boldLabelFont', al='center', w=200, h=25,
            bgc=colorWheel.darkgrey)
    pm.separator(style='none', h=3, w=200)

    lcUI.UI.lc_browse_field_button(width=200, textFieldName=prefix + '_textField_new_path', lct_cfg=lct_cfg,
                                   configAttr='lcTextureToolsRepath', placeholderText=defaultPath,
                                   annotation='Choose a new texture directory')
    pm.setParent(prefix + '_columnLayout_main')

    #
    pm.rowColumnLayout(nc=2, cw=([1, 100], [2, 100]))
    pm.iconTextButton(w=100, h=25, style='iconAndTextHorizontal', label='Repath All', flat=False,
                      image=os.path.join(iconPath, 'repath.png'), bgc=colorWheel.getColorRGB(ci),
                      annotation='Repath all file texture nodes to exact path given',
                      command=lambda *args: lcTxT_repath_all())
    ci += 1
    pm.iconTextButton(w=100, h=25, style='iconAndTextHorizontal', label='Selected', flat=False,
                      image=os.path.join(iconPath, 'repath.png'), bgc=colorWheel.getColorRGB(ci),
                      annotation='Repath selected file texture nodes to exact path given',
                      command=lambda *args: lcTxT_repath_selected())
    ci += 1
    pm.setParent(prefix + '_columnLayout_main')
    #
    pm.rowColumnLayout(nc=2, cw=([1, 100], [2, 100]))
    pm.button(w=100, h=25, label='Intelli-All', bgc=colorWheel.getColorRGB(ci),
              annotation='Recursive search given path to repath all file texture nodes',
              command=lambda *args: lcTxT_intelligent_repath_all())
    ci += 1
    pm.button(w=100, h=25, label='Intelli-Selected', bgc=colorWheel.getColorRGB(ci),
              annotation='Recursive search given path to repath selected file texture nodes',
              command=lambda *args: lcTxT_intelligent_repath_selected())
    ci += 1
    pm.setParent(prefix + '_columnLayout_main')
    pm.separator(style='in', h=8, w=200)

    # REPATH SHADERS (dx11 only)
    pm.text(l='- Set new path for DX11 Shaders -', font='boldLabelFont', al='center', w=200, h=25,
            bgc=colorWheel.darkgrey)
    pm.separator(style='none', h=3, w=200)

    lcUI.UI.lc_browse_field_button(width=200, textFieldName=prefix + '_textField_new_shader_path', lct_cfg=lct_cfg,
                                   configAttr='lcTextureToolsShaderRepath', placeholderText=defaultPath,
                                   annotation='Choose a new shader directory')
    pm.setParent(prefix + '_columnLayout_main')

    #
    pm.rowColumnLayout(nc=2, cw=([1, 100], [2, 100]))
    pm.iconTextButton(w=100, h=25, style='iconAndTextHorizontal', label='Repath All', flat=False,
                      image=os.path.join(iconPath, 'shader_repath.png'), bgc=colorWheel.getColorRGB(ci),
                      annotation='Repath all dx11Shader nodes to exact path given',
                      command=lambda *args: lcTxT_shader_repath_all())
    ci += 1
    pm.iconTextButton(w=100, h=25, style='iconAndTextHorizontal', label='Selected', flat=False,
                      image=os.path.join(iconPath, 'shader_repath.png'), bgc=colorWheel.getColorRGB(ci),
                      annotation='Repath selected dx11Shader nodes to exact path given',
                      command=lambda *args: lcTxT_shader_repath_selected())
    ci += 1
    pm.setParent(prefix + '_columnLayout_main')
    pm.separator(style='in', h=8, w=200)

    # OPEN TEXTURES
    # a=170
    # b=200-a
    # pm.rowColumnLayout(nc=2, cw=([1,a], [2,b]))
    pm.text(l='- Open File Texture Nodes -', font='boldLabelFont', al='center', w=200, h=25, bgc=colorWheel.darkgrey)
    pm.separator(style='none', h=3, w=200)

    # pm.symbolButton(prefix+'_button_check_editors', visible=False, image=os.path.join(srcPath,'icons','hint.png'), annotation='Setup Image File Editors', command=lambda *args: lcTxT_update_maya_prefs(prefix+'_button_check_editors') )
    pm.setParent(prefix + '_columnLayout_main')
    pm.rowColumnLayout(nc=2, cw=([1, 100], [2, 100]))
    pm.iconTextButton(w=100, h=25, style='iconAndTextHorizontal', label='Open All', flat=False,
                      image=os.path.join(iconPath, 'open.png'), bgc=colorWheel.getColorRGB(ci),
                      annotation='Open all file texture nodes in default associated program',
                      command=lambda *args: lcTxT_open_textures('all'))
    ci += 1
    pm.iconTextButton(w=100, h=25, style='iconAndTextHorizontal', label='Selected', flat=False,
                      image=os.path.join(iconPath, 'open.png'), bgc=colorWheel.getColorRGB(ci),
                      annotation='Open selected file texture nodes in default associated program',
                      command=lambda *args: lcTxT_open_textures('selected'))
    ci += 1
    pm.separator(style='none', h=8, w=200)

    #
    if not asChildLayout:
        mainWindow.show()
        pm.window(mainWindow.mainWindow, edit=True, height=winHeight, width=winWidth)
    else:
        pm.setParent('..')
        pm.setParent('..')

    # edit menus
    optionsMenu, helpMenu = lcUI.UI.lcToolbox_child_menu_edit(asChildLayout, windowName)

    # restore interface selections
    pm.textField(prefix + '_textField_new_path', edit=True, text=lct_cfg.get('lcTextureToolsRepath'))
    pm.textField(prefix + '_textField_prefix', edit=True, text=lct_cfg.get('lcTextureToolsPrefix'))
    pm.textField(prefix + '_textField_new_shader_path', edit=True, text=lct_cfg.get('lcTextureToolsShaderRepath'))

    # run extra stuff
    pm.setFocus(prefix + '_button_rename')

    # validate export directory
    lcPath.Path.validatePathTextField(prefix + '_textField_new_path', lct_cfg, 'lcTextureToolsRepath', defaultPath)
    lcPath.Path.validatePathTextField(prefix + '_textField_new_shader_path', lct_cfg, 'lcTextureToolsShaderRepath',
                                      defaultPath)


def lcTxT_repath_all(*args, **kwargs):
    ''' '''
    textures = pm.ls(type='file')
    if textures:
        newPath = pm.textField(prefix + '_textField_new_path', query=True, text=True)
        if newPath:
            lcTexture.Texture.repathTextures(textures, newPath)


def lcTxT_repath_selected(*args, **kwargs):
    ''' '''
    textures = pm.ls(sl=True)
    textures = lcTexture.Texture.filterForTextures(textures)
    if textures:
        newPath = pm.textField(prefix + '_textField_new_path', query=True, text=True)
        if newPath:
            lcTexture.Texture.repathTextures(textures, newPath)


def lcTxT_open_textures(operation, *args, **kwargs):
    ''' '''
    if not pm.optionVar(query='EditImageDir') or not pm.optionVar(query='PhotoshopDir'):
        prefsWindow = lcPrefs.MiniPrefsWindow()
        prefsWindow.show()
    else:
        if operation == 'selected':
            textures = lcTexture.Texture.filterForTextures(pm.ls(sl=True))
        if operation == 'all':
            textures = pm.ls(type='file')

        if textures:
            lcTexture.Texture.openTextureList(textures)


def lcTxT_rename_textures(renamePrefix, *args, **kwargs):
    ''' '''
    if not renamePrefix:
        renamePrefix = defaultPrefix
    lcTexture.Texture.renameAllTextureNodes(renamePrefix)


def lcTxT_rename_focus(*args, **kwargs):
    renamePrefix = pm.textField(prefix + '_textField_prefix', query=True, tx=True)
    if not renamePrefix:
        pm.textField(prefix + '_textField_prefix', edit=True, tx=defaultPrefix)


def lcTxT_intelligent_repath_all():
    '''  '''
    newPath = pm.textField(prefix + '_textField_new_path', query=True, text=True)
    if newPath:
        lcTexture.Texture.intelligentRepathAll(newPath)


def lcTxT_intelligent_repath_selected():
    '''  '''
    textures = pm.ls(sl=True)
    textures = lcTexture.Texture.filterForTextures(textures)
    if textures:
        newPath = pm.textField(prefix + '_textField_new_path', query=True, text=True)
        if newPath:
            lcTexture.Texture.intelligentRepath(textures, newPath)


def lcTxT_shader_repath_all():
    '''  '''
    newPath = pm.textField(prefix + '_textField_new_shader_path', query=True, text=True)
    if newPath:
        lcShader.Shader.intelligentRepathAll(newPath)


def lcTxT_shader_repath_selected():
    '''  '''
    shaders = pm.ls(sl=True)
    shaders = lcShader.Shader.filterForShaders(shaders, ['dx11Shader'])
    if shaders:
        newPath = pm.textField(prefix + '_textField_new_shader_path', query=True, text=True)
        if newPath:
            lcShader.Shader.intelligentRepath(shaders, newPath)
