import os
import sys

import pymel.core as pm

import lct.src.core.lcBake as lcBake
import lct.src.core.lcColor as lcColor
import lct.src.core.lcConfiguration as lcConfiguration
import lct.src.core.lcGeometry as lcGeometry
import lct.src.core.lcPath as lcPath
import lct.src.core.lcPlugin as lcPlugin
import lct.src.core.lcUI as lcUI

# interface colors
hue = 0.95
colorWheel = lcColor.ColorWheel(divisions=9, hueRange=[hue,hue], satRange=[0.2,0.3], valRange=[0.5,0.3])

#set conf values
conf = lcConfiguration.Conf.load_conf_file(os.path.join(os.path.abspath(os.path.dirname(__file__)), "{}.conf".format(os.path.basename(__file__).split('.')[0]) ) )
publish = conf['publish']
annotation = conf['annotation']
prefix = conf['prefix']
height = conf['height']

#set paths
srcPath = lcPath.Path.getSrcPath()
basePath = os.path.abspath(os.path.dirname(__file__))
iconPath = os.path.normpath(os.path.join(basePath, 'icons'))

defaultString = 'Select / Make A Set . . .'
defaultPath = 'Export Path . . .'

# setup configuration info
global_cfg = lcConfiguration.GlobalSettingsDictionary()
lct_cfg = lcConfiguration.ConfigurationNode(lcPath.Path.get_tools_settings_file(), global_cfg)
lct_cfg.add('lcBatchBakePop', False)
lct_cfg.add('lcBatchBakePath', defaultPath)
lct_cfg.add('lcBatchBakeSetList', 1)
lct_cfg.add('lcBatchBakeCamList', 2)
lct_cfg.add('lcBatchBakeShadows', 1)

def lcBatchBakeUI(dockable=False, asChildLayout=False, *args, **kwargs):
    ''' '''
    global lct_cfg
    global prefix
    global defaultPath

    windowName = 'lcBatchBake'
    shelfCommand = 'import lct.src.{0}.{0} as {1}\nreload({1})\n{1}.{0}UI()'.format(windowName, prefix)
    commandString = 'import lct.src.{0}.{0} as {1}\nreload({1})\n{1}.{0}UI(asChildLayout=True)'.format(windowName, prefix)
    icon = basePath+'lcBatchBake.png'
    winWidth  = 205
    winHeight = 243

    if pm.window(windowName, ex=True):
        pm.deleteUI(windowName)

    if not asChildLayout:
        lcUI.UI.lcToolbox_child_popout(prefix+'_columnLayout_main', windowName, height, commandString, iconPath, lct_cfg)
        mainWindow = lcUI.lcWindow(prefix=prefix, windowName=windowName, width=winWidth, height=winHeight, icon=icon, shelfCommand=shelfCommand, annotation=annotation, dockable=dockable, menuBar=True)
        mainWindow.create()

    #
    pm.columnLayout(prefix+'_columnLayout_main')


    # check for mental ray plugin
    mental_ray_available = lcPlugin.Plugin.reload_plugin(plugin='Mayatomr', autoload=True)

    if mental_ray_available:
        #
        pm.rowColumnLayout(nc=2, cw=([1,100], [2,100]) )
        pm.button(l='Make Texture Set', bgc=colorWheel.getPrev(), w=100, h=35, annotation='Create a Texture bake set', command=lambda *args: lcBake_make_new_bake_set(bakeSetListDropdown, 'texture') )
        pm.button(l='Make Vertex Set', bgc=colorWheel.getPrev(), w=100, h=35, annotation='Create a Texture bake set', command=lambda *args: lcBake_make_new_bake_set(bakeSetListDropdown, 'vertex') )
        pm.setParent(prefix+'_columnLayout_main')

        #
        pm.rowColumnLayout(nc=3, cw=([1,25], [2,150], [3,25]) )
        pm.symbolButton(h=25, image=os.path.join(iconPath,'reloadList.png'), annotation='Reload the bake set list', command=lambda *args: lcBake_populate_bake_set_list(bakeSetListDropdown) )
        bakeSetListDropdown = pm.optionMenu(prefix+'_optionMenu_bake_set_list', w=150, h=25, annotation='List of bake sets' )
        bakeSetListDropdown.changeCommand(lambda *args: lcBake_choose_active(bakeSetListDropdown) )
        button_delete_sets = pm.symbolButton(h=25, image=os.path.join(iconPath,'deleteItem.png'), annotation='Delete this bake set', command=lambda *args: lcBake_delete_current_bake_set(bakeSetListDropdown) )
        popup_delete_sets = pm.popupMenu(parent=button_delete_sets)
        pm.menuItem(l='Delete all bake sets', parent=popup_delete_sets, command=lambda *args: lcBake_delete_all_bake_sets(bakeSetListDropdown) )
        pm.setParent(prefix+'_columnLayout_main')

        #
        pm.rowColumnLayout(nc=2, cw=([1,100], [2,100] ) )  #nc=3, cw=([1,50], [2,50], [3,100] ) )
        pm.button(l='+ Add', bgc=colorWheel.getPrev(), w=100, h=25, annotation='Add geometry to bake set', command=lambda *args: lcBake_add_to_current_bake_set(bakeSetListDropdown) )
        # pm.button(l='- Rem', bgc=colorWheel.getPrev(), w=50, h=25, annotation='Remove geometry from bake set', command=lambda *args: lcBake_fake_command() )
        # ci+=1
        pm.button(l='Edit Options', bgc=colorWheel.getPrev(), w=100, h=25, annotation='Edit the bake set options', command=lambda *args: lcBake_show_bake_set_attrs(bakeSetListDropdown) )
        pm.setParent(prefix+'_columnLayout_main')

        #
        pm.rowColumnLayout(nc=2, cw=([1,75], [2,125] ) )
        pm.text(l='Bake Camera: ', al='right')
        cameraListDropdown = pm.optionMenu(prefix+'_optionMenu_camera_list', w=125, h=25, annotation='List of cameras' )
        cameraListDropdown.changeCommand (lambda *args:   lct_cfg.set('lcBatchBakeCamList', cameraListDropdown.getSelect()))
        pm.text(l='')
        pm.checkBox(prefix+'_checkBox_shadows', w=125, h=25, value=True, label='Shadows and AO?', annotation='Turn on to bake shadows and ambient occlusion', changeCommand=lambda *args: lct_cfg.set('lcBatchBakeShadows', pm.checkBox(prefix+'_checkBox_shadows', query=True, v=True)))
        pm.setParent(prefix+'_columnLayout_main')

        #
        pm.separator(style='none', h=10)
        lcUI.UI.lc_browse_field_button(width=200, textFieldName=prefix+'_textField_texture_path', lct_cfg=lct_cfg, configAttr='lcBatchBakePath', placeholderText=defaultPath, annotation='Choose an export directory')

        # pm.rowColumnLayout(nc=2, cw=([1,150], [2,50]) )
        # pm.textField(prefix+'_textField_texture_path', tx=defaultPath, annotation='Output directory path', w=150, changeCommand=lambda *args: lct_cfg.set('lcBatchBakePath', pm.textField(prefix+'_textField_texture_path', query=True, tx=True)))
        # pm.button(prefix+'_button_browse_path', l='Browse', bgc=colorWheel.getPrev(), annotation='Choose a directory', w=50, command=lambda *args: lcBake_setExportPath() )
        # ci+=1
        pm.setParent(prefix+'_columnLayout_main')

        #
        pm.rowColumnLayout(nc=2, cw=([1,150], [2,50]) )
        pm.button(l='Bake It !!', bgc=colorWheel.getPrev(), w=150, h=40, annotation='Bake to texture or vertex', command=lambda *args: lcBake_convert_lightmap(bakeSetListDropdown, cameraListDropdown) )
        pm.symbolButton(prefix+'_button_open_folder', bgc=(0.18,0.18,0.18), image=os.path.join(srcPath, 'icons', 'folder_med.png'), annotation='Open the export folder', command=lambda *args: lcBake_openExportPath() )

    # mental ray was not found!
    else:
        pm.text(l="Mental Ray plug-in not found", al='center', w=200, h=215, font='boldLabelFont')

    #
    if not asChildLayout:
        mainWindow.show()
        pm.window(mainWindow.mainWindow, edit=True, h=winHeight, w=winWidth)
    else:
        pm.setParent('..')
        pm.setParent('..')

    #
    if mental_ray_available:
        #edit menus
        optionsMenu, helpMenu = lcUI.UI.lcToolbox_child_menu_edit(asChildLayout, windowName)

        pm.menuItem(parent=optionsMenu, divider=True, dividerLabel=windowName)
        pm.menuItem(parent=optionsMenu, l='Delete All Bake Sets', command=lambda *args: lcBake_delete_all_bake_sets(bakeSetListDropdown) )

        #populate lists
        lcBake_populate_bake_set_list(bakeSetListDropdown)
        lcBake_populate_camera_list(cameraListDropdown)

        #Restore Interface Selections
        bakeSetListDropdown.setSelect(lct_cfg.get('lcBatchBakeSetList'))
        cameraListDropdown.setSelect(lct_cfg.get('lcBatchBakeCamList'))
        pm.checkBox(prefix+'_checkBox_shadows', edit=True, value=lct_cfg.get('lcBatchBakeShadows'))
        pm.textField(prefix+'_textField_texture_path', edit=True, text=lct_cfg.get('lcBatchBakePath'))

        #update interface highlighting
        if lct_cfg.get('lcBatchBakeSetList') > 1:
            lcBake_glow(bakeSetListDropdown)

        # validate export directory
        lcPath.Path.validatePathTextField(prefix+'_textField_texture_path', lct_cfg, 'lcBatchBakePath', defaultPath)

def lcBake_openExportPath(*args, **kwargs):
    ''' open lightmap dir if its already been created, otherwise open base path '''
    global prefix
    global lct_cfg

    outputDirectoryBase = pm.textField(prefix+'_textField_texture_path', query=True, text=True)
    outputDirectory = os.path.normpath(os.path.join(outputDirectoryBase, 'lightMap'))
    if os.path.exists(outputDirectory):
        lcPath.Path.openFilePath(outputDirectory)
    else:
        lcPath.Path.openFilePath(outputDirectoryBase)

def lcBake_populate_camera_list(cameraListDropdown, *args, **kwargs):
    ''' '''
    global lct_cfg

    cameraListDropdown.clear()

    cameras = pm.ls(type='camera')
    for cam in cameras:
        #cameraListDropdown.addItems([cam])
        cameraListDropdown.addItems(lcGeometry.Geometry.getTransformsFromShapes([cam]))

def lcBake_populate_bake_set_list(bakeSetListDropdown, *args, **kwargs):
    ''' '''
    global defaultString
    global lct_cfg

    bakeSetListDropdown.clear()
    bakeSetListDropdown.addItems([defaultString])

    textureBakeSets = pm.ls(type='textureBakeSet')
    vertexBakeSets = pm.ls(type='vertexBakeSet')
    bakeSets = textureBakeSets+vertexBakeSets
    for set in bakeSets:
        bakeSetListDropdown.addItems([set])

    lcBake_glow(bakeSetListDropdown)

def lcBake_make_new_bake_set(bakeSetListDropdown, type, *args, **kwargs):
    ''' '''
    global lct_cfg

    selectedObjs = pm.ls(selection=True)

    newBakeSet = lcBake.Bake.createBakeSet(type=type)
    bakeSetListDropdown.addItems([newBakeSet])
    numItems = bakeSetListDropdown.getNumberOfItems()
    bakeSetListDropdown.setSelect(numItems)

    lcBake.Bake.assignBakeSet(selectedObjs, newBakeSet)

    lcBake_glow(bakeSetListDropdown)

def lcBake_add_to_current_bake_set(bakeSetListDropdown, *args, **kwargs):
    ''' '''
    global lct_cfg
    global defaultString

    selectedObjs = pm.ls(selection=True)

    numItems = bakeSetListDropdown.getNumberOfItems()
    if numItems > 0:
        currentBakeSet = bakeSetListDropdown.getValue()
        if currentBakeSet != defaultString:
            lcBake.Bake.assignBakeSet(selectedObjs, currentBakeSet)

def lcBake_delete_current_bake_set(bakeSetListDropdown, *args, **kwargs):
    ''' '''
    global lct_cfg
    global defaultString

    numItems = bakeSetListDropdown.getNumberOfItems()
    if numItems > 0:
        currentBakeSet = bakeSetListDropdown.getValue()
        if currentBakeSet != defaultString:
            pm.delete(currentBakeSet)

    lcBake_populate_bake_set_list(bakeSetListDropdown)

def lcBake_show_bake_set_attrs(bakeSetListDropdown, *args, **kwargs):
    ''' '''
    global lct_cfg
    global defaultString

    numItems = bakeSetListDropdown.getNumberOfItems()
    if numItems > 0:
        currentBakeSet = bakeSetListDropdown.getValue()
        if currentBakeSet != defaultString:
            pm.mel.showEditor(currentBakeSet)

def lcBake_delete_all_bake_sets(bakeSetListDropdown, *args, **kwargs):
    ''' '''
    textureBakeSets = pm.ls(type='textureBakeSet')
    vertexBakeSets = pm.ls(type='vertexBakeSet')
    bakeSets = textureBakeSets+vertexBakeSets

    for item in bakeSets:
        pm.delete(item)

    lcBake_populate_bake_set_list(bakeSetListDropdown)

def lcBake_convert_lightmap(bakeSetListDropdown, cameraListDropdown, *args, **kwargs):
    ''' '''
    global lct_cfg
    global prefix
    global defaultString
    global defaultPath

    sel = pm.ls(sl=True)

    numItems = bakeSetListDropdown.getNumberOfItems()
    if numItems > 0:
        currentBakeSet = bakeSetListDropdown.getValue()
        if currentBakeSet != defaultString:
            currentCamera = cameraListDropdown.getValue()
            outputDirectory = pm.textField(prefix+'_textField_texture_path', query=True, text=True)
            if os.path.exists(outputDirectory) or pm.PyNode(currentBakeSet).nodeType() == 'vertexBakeSet':
                shadows = pm.checkBox(prefix+'_checkBox_shadows', query=True, value=True)

                if pm.control('bakeWindow', exists = True):
                    pm.deleteUI('bakeWindow')
                bakeWindow = pm.window('bakeWindow', t='Batch Bake', widthHeight=[100, 100], rtf=True, mnb=False, mxb=False, s=False)
                pm.columnLayout()
                pm.text(l='')
                pm.text(l='')
                pm.text(l='          Bake In Progress          ')
                pm.text(l='                  ......        ')
                pm.text(l='')
                pm.text(l='')
                bakeWindow.show()
                pm.refresh()

                if pm.PyNode(currentBakeSet).nodeType() == 'vertexBakeSet':
                    outputDirectory = 'None'

                convertString = lcBake.Bake.convertLightmap(currentBakeSet, currentCamera, outputDirectory, shadows)

                sys.stdout.write('Convert Command: {0}'.format(convertString) )

                pm.deleteUI('bakeWindow')

                pm.select(sel, replace=True)
            else:
                pm.warning('Path not found: {0}'.format(outputDirectory) )
                pm.setFocus(prefix+'_textField_texture_path')

def lcBake_open_lightmap_folder(*args, **kwargs):
    ''' '''
    global lct_cfg

    dir = pm.textField(prefix+'_textField_texture_path', query=True, text=True)
    lightmapDir = os.path.normpath(os.path.join(dir, 'lightMap'))
    if os.path.exists(lightmapDir):
        lcPath.Path.openFilePath(lightmapDir)
    elif os.path.exists(dir):
        lcPath.Path.openFilePath(dir)
    else:
        pm.warning('Path not found: {0}'.format(dir) )

def lcBake_choose_active(listDropdown, *args, **kwargs):
    ''' '''
    global lct_cfg
    global defaultString

    lct_cfg.set('lcBatchBakeSetList', listDropdown.getSelect())

    lcBake_glow(listDropdown)

def lcBake_glow(listDropdown, *args, **kwargs):
    ''' highlight dropdown list red if nothing is selected '''
    global lct_cfg
    global defaultString

    selected = listDropdown.getValue()

    if selected==defaultString:
        listDropdown.setBackgroundColor(colorWheel.darkgrey )
    else:
        listDropdown.setBackgroundColor(colorWheel.mayalight )