import os
import math
import re
import functools
import pymel.core as pm

import lct.src.core.lcUtility as lcUtility
import lct.src.core.lcGeometry as lcGeometry
import lct.src.core.lcConfiguration as lcConfiguration
import lct.src.core.lcColor as lcColor
import lct.src.core.lcShader as lcShader
import lct.src.core.lcPath as lcPath
import lct.src.core.lcUI as lcUI

import lct.src.lcToolbox.lcToolbox as lcToolbox

# interface colors
hue = 0.0
colorWheel = lcColor.ColorWheel(divisions=3, hueRange=[hue, hue], satRange=[0.5, 0.3], valRange=[0.45, 0.45])

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

defaultString = 'Nothing Live . . .'

# setup configuraion
global_cfg = lcConfiguration.GlobalSettingsDictionary()
lct_cfg = lcConfiguration.ConfigurationNode(lcPath.Path.get_tools_settings_file(), global_cfg)
lct_cfg.add('lcRetopoBasicPop', False)
lct_cfg.add('lcRetopoBasicListItem', 1)
lct_cfg.add('lcRetopoBasicLayering', 0.0)
lct_cfg.add('lcRetopoBasicShader', 0.5)
lct_cfg.add('lcRetopoBasicScriptJob', 0)


def lcRetopoBasicUI(dockable=False, asChildLayout=False, *args, **kwargs):
    """ """
    global lct_cfg
    global prefix

    ci = 0  # color index iterator
    windowName = 'lcRetopoBasic'
    shelfCommand = 'import lct.src.{0}.{0} as {1}\nreload({1})\n{1}.{0}UI()'.format(windowName, prefix)
    commandString = 'import lct.src.{0}.{0} as {1}\nreload({1})\n{1}.{0}UI(asChildLayout=True)'.format(windowName,
                                                                                                       prefix)
    icon = os.path.join(basePath, 'lcRetopoBasic.png')
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

    pm.columnLayout(prefix + '_columnLayout_main')

    # SETUP
    pm.button(l='Setup for Retopo', bgc=colorWheel.getColorRGB(ci), w=200, h=25,
              annotation='Setup a high res mesh for retopology',
              command=lambda *args: rtb_setup_live_mesh(highresListDropdown))
    ci += 1

    # List
    pm.rowColumnLayout(nc=3, cw=([1, 25], [2, 150], [3, 25]))
    pm.symbolButton(h=25, image=os.path.join(iconPath, 'reloadMeshList.png'),
                    annotation='Reload the list of high res meshes',
                    command=lambda *args: rtb_highres_list_populate(highresListDropdown))
    highresListDropdown = pm.optionMenu(prefix + '_optionMenu_highres_list', w=150, h=23, bgc=[0.5, 0.5, 0.5],
                                        annotation='List of high res meshes in the scene')
    highresListDropdown.changeCommand(lambda *args: rtb_choose_active(highresListDropdown))
    remove_mesh_button = pm.symbolButton(h=25, image=os.path.join(iconPath, 'removeMeshFromList.png'),
                                         annotation='Remove current high res mesh from the list and return it to a normal state',
                                         command=lambda *args: rtb_remove(highresListDropdown))
    popup_remove_mesh = pm.popupMenu(parent=remove_mesh_button)
    pm.menuItem(l='Remove all live meshes', parent=popup_remove_mesh,
                command=lambda *args: rtb_remove_all(highresListDropdown))
    pm.setParent(prefix + '_columnLayout_main')

    # Scale
    pm.rowColumnLayout(nc=4, cw=([1, 50], [2, 100], [3, 25], [4, 25]))
    pm.picture(prefix + '_picture_layer_mesh', image=os.path.join(iconPath, 'meshLayering.png'),
               annotation='Drag slider to change mesh layering')
    pm.floatSlider(prefix + '_floatSlider_layer_mesh', h=25, step=0.01, min=0, max=1,
                   v=lct_cfg.get('lcRetopoBasicLayering'),
                   dragCommand=lambda *args: rtb_scale_layer_mesh(highresListDropdown))
    button_xray = pm.symbolButton(prefix + '_symbolButton_xray', h=25, image=os.path.join(iconPath, 'toggleXray.png'),
                                  bgc=[0.27, 0.27, 0.27], annotation='Toggle Mesh X-Ray',
                                  command=lambda *args: rtb_toggle_xray(highresListDropdown, 'active'))
    popup_xray = pm.popupMenu(parent=button_xray)
    pm.menuItem(l='xRay on/off all', parent=popup_xray, command=lambda *args: rtb_toggle_xray(highresListDropdown))

    button_hide = pm.symbolButton(prefix + '_symbolButton_hide', h=25, image=os.path.join(iconPath, 'hideMesh.png'),
                                  bgc=[0.27, 0.27, 0.27], annotation='Hide/Show Current High-Res',
                                  command=lambda *args: rtb_toggle_hide(highresListDropdown, 'active'))
    popup_hide = pm.popupMenu(parent=button_hide)
    pm.menuItem(l='Hide/Show all', parent=popup_hide, command=lambda *args: rtb_toggle_hide(highresListDropdown, 'all'))
    pm.menuItem(l='Hide/Show others', parent=popup_hide,
                command=lambda *args: rtb_toggle_hide(highresListDropdown, 'others'))
    pm.setParent(prefix + '_columnLayout_main')

    # Shader
    pm.rowColumnLayout(nc=3, cw=([1, 50], [2, 100], [3, 50]))
    pm.picture(image=os.path.join(iconPath, 'shaderOpacity.png'), enable=False,
               annotation='Drag slider to change shader transparency')
    pm.floatSlider(prefix + '_floatSlider_topo_trans', h=25, step=0.1, min=0, max=1,
                   v=lct_cfg.get('lcRetopoBasicShader'), dragCommand=lambda *args: rtb_update_topo_transparency())
    pm.symbolButton(h=25, image=os.path.join(iconPath, 'assignShader.png'), bgc=[0.27, 0.27, 0.27],
                    annotation='Create and/or assign a semi-transparent shader to selected low res mesh',
                    command=lambda *args: rtb_create_retopo_shader())
    pm.setParent(prefix + '_columnLayout_main')
    pm.separator(style='in', h=5)

    # Relax and Shrinkwrap
    pm.rowColumnLayout(nc=2)
    pm.button(l='Relax', bgc=colorWheel.getColorRGB(ci), w=100, h=25,
              annotation='Relax selected verts and shrink-wrap them to the live mesh',
              command=lambda *args: rtb_vert_ops(highresListDropdown, operation='relax'))
    ci += 1
    pm.button(l='Shrink-Wrap', bgc=colorWheel.getColorRGB(ci), w=100, h=25,
              annotation='Shrink-wrap selected verts to the live mesh',
              command=lambda *args: rtb_vert_ops(highresListDropdown, operation='shrink'))
    ci += 1
    pm.setParent(prefix + '_columnLayout_main')

    # PROG Bar
    pm.progressBar(prefix + '_progress_control', en=False, w=202, isInterruptable=True)
    pm.separator(style='in', h=5)

    # Tool List
    pm.gridLayout(nrc=[1, 5], cwh=[40, 40])
    ##1
    pm.symbolButton(prefix + '_symbolButton_select_mode', image='selectByComponent.png',
                    c=lambda *args: rtb_toggle_select_mode(), annotation='Toggle Object/Component Modes')
    ##2
    create_mesh = pm.symbolButton(image='polyCylinder.png',
                                  c=lambda *args: pm.polyCylinder(r=1, h=2, sx=8, sy=1, sz=1, ax=(0, 1, 0), rcp=0,
                                                                  cuv=3, ch=1), annotation='Create Poly Cylinder')
    popup_create_mesh = pm.popupMenu(parent=create_mesh)
    pm.menuItem(l='polyPlane', parent=popup_create_mesh,
                command=lambda *args: pm.polyPlane(w=2, h=2, sx=1, sy=1, ax=(0, 1, 0), cuv=2, ch=1))
    pm.menuItem(l='polyCube', parent=popup_create_mesh,
                command=lambda *args: pm.polyCube(w=2, h=2, d=2, sx=1, sy=1, ax=(0, 1, 0), cuv=2, ch=1))
    ##3
    pm.symbolButton(image='polyUnite.png', command=lambda *args: lcGeometry.Geometry.merge_and_weld(),
                    annotation='Combine and Weld')
    ##4
    button_zeroX = pm.symbolButton(image=os.path.join(iconPath, 'zeroX.png'), command=lambda *args: rtb_zero('x'),
                                   annotation='Zero to world axis')
    popup_zeroX = pm.popupMenu(parent=button_zeroX)
    pm.menuItem(l='Zero X', parent=popup_zeroX, command=lambda *args: rtb_zero('x'))
    pm.menuItem(l='Zero Y', parent=popup_zeroX, command=lambda *args: rtb_zero('y'))
    pm.menuItem(l='Zero Z', parent=popup_zeroX, command=lambda *args: rtb_zero('z'))
    ##5
    pm.symbolButton(image='modelToolkit.png', c=lambda *args: pm.mel.eval('ToggleModelingToolkit'),
                    annotation='Modeling Toolkit')

    #
    if not asChildLayout:
        mainWindow.show()
        pm.window(mainWindow.mainWindow, edit=True, h=winHeight, w=winWidth)
    else:
        pm.setParent('..')
        pm.setParent('..')

    # edit menus
    optionsMenu, helpMenu = lcUI.UI.lcToolbox_child_menu_edit(asChildLayout, windowName)

    pm.menuItem(parent=optionsMenu, divider=True, dividerLabel=windowName)
    pm.menuItem(parent=optionsMenu, l='Remove all live meshes',
                command=lambda *args: rtb_remove_all(highresListDropdown))

    # populate drowpdowns
    rtb_highres_list_populate(highresListDropdown)

    # restore interface selections
    highresListDropdown.setSelect(lct_cfg.get('lcRetopoBasicListItem'))
    rtb_choose_active(highresListDropdown)

    # vertex animation cache in viewport 2.0 must be disabled or the mesh will not update properly
    if pm.objExists('hardwareRenderingGlobals'):
        pm.PyNode('hardwareRenderingGlobals').vertexAnimationCache.set(0)
    rtb_init_select_mode()
    if not pm.scriptJob(ex=lct_cfg.get('lcRetopoBasicScriptJob')) or lct_cfg.get('lcRetopoBasicScriptJob') == 0:
        jobNum = pm.scriptJob(e=["SelectModeChanged", lambda *args: rtb_init_select_mode()], protected=True)
        lct_cfg.set('lcRetopoBasicScriptJob', jobNum)


def rtb_init_select_mode(*args, **kwargs):
    ''' '''
    if pm.control(prefix + '_symbolButton_select_mode', exists=True):
        componentMode = pm.selectMode(query=True, component=True)
        objectMode = pm.selectMode(query=True, object=True)
        if componentMode:
            pm.symbolButton(prefix + '_symbolButton_select_mode', edit=True, image='selectByComponent.png')
        else:
            pm.symbolButton(prefix + '_symbolButton_select_mode', edit=True, image='selectByObject.png')


def rtb_toggle_select_mode(*args, **kwargs):
    if pm.control(prefix + '_symbolButton_select_mode', exists=True):
        componentMode = pm.selectMode(query=True, component=True)
        if not componentMode:
            pm.selectMode(component=True)
            pm.symbolButton(prefix + '_symbolButton_select_mode', edit=True, image='selectByComponent.png')
        else:
            pm.selectMode(object=True)
            pm.symbolButton(prefix + '_symbolButton_select_mode', edit=True, image='selectByObject.png')


def rtb_setup_live_mesh(highresListDropdown, *args, **kwargs):
    ''' '''
    global lct_cfg

    sel = pm.ls(sl=True)
    lcGeometry.Geometry.fixNamespaceNames()
    if sel:
        for item in sel:
            pm.undoInfo(chunkName='lc_undo_makelive', openChunk=True)
            try:
                pm.parent(item, world=True)
                lcGeometry.Geometry.unlock_translate_rotate_scale(item)
                root = pm.group(empty=True, name=item + '_RETOPO')
                live = pm.duplicate(item, name=item + '_live')[0]
                high = item.rename(item + '_high')

                pm.makeIdentity([high, live], apply=True, t=1, r=1, s=1, n=0)
                lcUtility.Utility.centerPvt([high, live])

                highShape = high.getShape()
                liveShape = live.getShape()

                highShape.overrideEnabled.set(1)  # enable display overrides
                highShape.overrideDisplayType.set(2)  # set to referenced

                liveShape.overrideEnabled.set(1)  # enable display overrides
                liveShape.overrideDisplayType.set(1)  # set to template
                liveShape.overrideVisibility.set(0)  # set visibility to 0

                pm.makeLive(live)

                highresListDropdown.addItems([high])
                numItems = highresListDropdown.getNumberOfItems()
                highresListDropdown.setSelect(numItems)

                pm.parent(high, root)
                pm.parent(live, root)

                pm.connectAttr('persp.translate', high.scalePivot)

                rtb_scale_layer_mesh(highresListDropdown)

                rtb_glow(highresListDropdown)

                lct_cfg.set('lcRetopoBasicListItem', highresListDropdown.getSelect())

                pm.picture(prefix + '_picture_layer_mesh', edit=True, enable=True)
                pm.floatSlider(prefix + '_floatSlider_layer_mesh', edit=True, enable=True)
                pm.undoInfo(chunkName='lc_undo_makelive', closeChunk=True)
                pm.select(clear=True)
            except:
                pm.undoInfo(chunkName='lc_undo_makelive', closeChunk=True)
                pm.undo()
                lcUtility.Utility.lc_print('Could not make {0} live'.format(item))


def rtb_remove(highresListDropdown, *args, **kwargs):
    ''' remove item from the list and delete live-mesh and groups '''
    global defaultString
    global lct_cfg

    high = highresListDropdown.getValue()

    # restore interface selections
    highresListDropdown.setSelect(1)
    rtb_choose_active(highresListDropdown)

    if not high == defaultString:
        high = pm.PyNode(high.split("'")[0])  # get rid of unicode crap
        high.rename(re.sub(r'\_high$', '', str(high)))
        pm.parent(high, world=True)

        high.setScale([1, 1, 1])
        pm.disconnectAttr('persp.translate', high.scalePivot)

        if pm.displaySurface(high, query=True, xRay=True)[0] == True:
            pm.displaySurface(high, xRay=False)
        if not high.visibility.get():
            high.visibility.set(True)

        highShape = high.getShape()
        highShape.overrideDisplayType.set(0)  # sets to normal mode
        highShape.overrideEnabled.set(0)  # disable display overrides

        pm.delete(str(high) + '_RETOPO')

    rtb_highres_list_populate(highresListDropdown)

    lct_cfg.set('lcRetopoBasicListItem', highresListDropdown.getSelect())
    pm.select(clear=True)


def rtb_remove_all(highresListDropdown, *args, **kwargs):
    '''
    remove all meshes from the dropdown list
    '''
    global defaultString

    numItems = highresListDropdown.getNumberOfItems()

    while numItems > 1:
        highresListDropdown.setSelect(2)
        rtb_remove(highresListDropdown)
        numItems = highresListDropdown.getNumberOfItems()


def rtb_create_retopo_shader():
    ''' '''
    global lct_cfg

    try:
        sel = [obj for obj in pm.ls(sl=True) if obj.getShape() and obj.getShape().nodeType() == 'mesh']
        pm.select(sel, replace=True)
    except:
        pm.warning('Please select some geometry')
        return

    retopoShader = lcShader.ShaderNode('lcRetopo', 'lambert')
    retopoShader.create()
    retopoShader.shader.color.set(0, 0, 1)

    retopoShader.shader.color.set(1, 0, 0)
    slider = lct_cfg.get('lcRetopoBasicShader')
    retopoShader.shader.transparency.set(slider, slider, slider)

    if sel:
        pm.select(sel, replace=True)  # grab the stored selection
        pm.hyperShade(assign=retopoShader.shaderName)  # assign shader to selection


def rtb_update_high_res_shader(highresListDropdown, *args, **kwargs):
    '''
    '''
    global defaultString

    sel = pm.ls(sl=True)
    high = highresListDropdown.getValue()

    inactiveShader = lcShader.ShaderNode('lcRetopo_Inactive', 'blinn')
    inactiveShader.create()
    inactiveShader.shader.color.set(0.45, 0.45, 0.45)
    inactiveShader.shader.specularColor.set(0.13, 0.3, 0.47)
    inactiveShader.shader.eccentricity.set(0.5)
    inactiveShader.shader.specularRollOff.set(0.7)

    activeShader = lcShader.ShaderNode('lcRetopo_Active', 'blinn')
    activeShader.create()
    activeShader.shader.color.set(0.65, 0.65, 0.65)
    activeShader.shader.specularColor.set(0.25, 0.55, 0.88)
    inactiveShader.shader.eccentricity.set(0.4)
    inactiveShader.shader.specularRollOff.set(0.55)

    for item in highresListDropdown.getItemListLong():
        meshItem = pm.menuItem(item, query=True, label=True)
        if meshItem != defaultString:
            pm.select(meshItem, replace=True)
            if meshItem == high:
                pm.hyperShade(assign=activeShader.shader)  # assign shader to selection
            else:
                pm.hyperShade(assign=inactiveShader.shader)  # assign shader to selection

    pm.select(sel, replace=True)


def rtb_scale_layer_mesh(highresListDropdown, *args, **kwargs):
    ''' '''
    global defaultString
    global lct_cfg

    scale = pm.floatSlider(prefix + '_floatSlider_layer_mesh', query=True, value=True)
    lct_cfg.set('lcRetopoBasicLayering', scale)
    scale = math.pow(scale, 4)  # makes the slider a bit progressive, gives a better feel to the scale in the low range
    scale = 1 + scale * 2  # remaps 0-1 to 1-2 to be useful as a scale value

    # iterate over the entire list and adjust scales
    listItems = highresListDropdown.getItemListLong()

    for item in listItems:
        high = pm.menuItem(item, query=True, l=True)
        if high != defaultString:
            high = pm.PyNode(high)
            high.setScale([scale, scale, scale])


def rtb_toggle_xray(highresListDropdown, mode='all', *args, **kwargs):
    ''' '''
    global defaultString
    global lct_cfg

    if mode == 'all':
        xRay = None

        listItems = highresListDropdown.getItemListLong()

        for item in listItems:
            high = pm.menuItem(item, query=True, l=True)
            if high != defaultString:
                if xRay == None:
                    xRay = pm.displaySurface(high, query=True, xRay=True)[0]
                pm.displaySurface(high, xRay=not xRay)
    else:
        high = highresListDropdown.getValue()
        if high != defaultString:
            high = pm.PyNode(high)
            xRay = pm.displaySurface(high, query=True, xRay=True)[0]
            pm.displaySurface(high, xRay=not xRay)

    rtb_glow(highresListDropdown)


def rtb_toggle_hide(highresListDropdown, mode='all', *args, **kwargs):
    ''' '''
    global defaultString
    global lct_cfg

    if mode == 'all':
        vis = None
        listItems = highresListDropdown.getItemListLong()
        for item in listItems:
            high = pm.menuItem(item, query=True, l=True)
            if high != defaultString:
                high = pm.PyNode(high)
                if vis == None:
                    vis = high.visibility.get()
                high.visibility.set(not vis)

    if mode == 'active':
        high = highresListDropdown.getValue()
        if high != defaultString:
            high = pm.PyNode(high)
            vis = high.visibility.get()
            high.visibility.set(not vis)

    if mode == 'others':
        vis = None
        listItems = highresListDropdown.getItemListLong()
        highActive = highresListDropdown.getValue()
        for item in listItems:
            high = pm.menuItem(item, query=True, l=True)
            if high != defaultString and high != highActive:
                high = pm.PyNode(high)
                if vis == None:
                    vis = high.visibility.get()
                high.visibility.set(not vis)

    rtb_glow(highresListDropdown)


def rtb_update_topo_transparency():
    ''' '''
    global prefix
    global lct_cfg

    if pm.objExists('lcRetopo'):
        trans = pm.floatSlider(prefix + '_floatSlider_topo_trans', query=True, value=True)
        trans = math.pow(trans, 0.25)  # user feedback slider 'feeling'
        lct_cfg.set('lcRetopoBasicShader', trans)
        pm.setAttr('lcRetopo.transparency', [trans, trans, trans])


def rtb_choose_active(highresListDropdown, *args, **kwargs):
    ''' '''
    global prefix
    global defaultString
    global lct_cfg

    lct_cfg.set('lcRetopoBasicListItem', highresListDropdown.getSelect())
    high = highresListDropdown.getValue()
    if high != defaultString:
        rtb_scale_layer_mesh(highresListDropdown)
        pm.picture(prefix + '_picture_layer_mesh', edit=True, enable=True)
        pm.floatSlider(prefix + '_floatSlider_layer_mesh', edit=True, enable=True)

        live = pm.PyNode(high.replace('_high', '_live'))
        liveShape = live.getShape()
        pm.makeLive(live)
    else:
        pm.makeLive(none=True)
        rtb_scale_layer_mesh(highresListDropdown)
        pm.picture(prefix + '_picture_layer_mesh', edit=True, enable=False)
        pm.floatSlider(prefix + '_floatSlider_layer_mesh', edit=True, enable=False)

    rtb_glow(highresListDropdown)


def rtb_highres_list_populate(highresListDropdown, *args, **kwargs):
    ''' '''
    global defaultString
    global lct_cfg

    highresListDropdown.clear()
    highresListDropdown.addItems([defaultString])

    sel = [obj for obj in pm.ls(dag=True, transforms=True) if obj.getShape() and obj.getShape().nodeType() == 'mesh']
    highres = lcUtility.Utility.filterByToken(sel, 'high')

    for mesh in highres:
        highresListDropdown.addItems([mesh])

    rtb_glow(highresListDropdown)

    pm.picture(prefix + '_picture_layer_mesh', edit=True, enable=False)
    pm.floatSlider(prefix + '_floatSlider_layer_mesh', edit=True, enable=False)

    if highresListDropdown.getNumberOfItems() < lct_cfg.get('lcRetopoBasicListItem'):
        lct_cfg.set('lcRetopoBasicListItem', highresListDropdown.getNumberOfItems())


def rtb_zero(axis='x', *args, **kwargs):
    '''
    zero selected components on an axis
    '''
    axis = axis.lower()
    sel = pm.ls(sl=True)
    verts = lcGeometry.Geometry.getVertsFromSelection(sel)
    if verts:
        for v in verts:
            if axis == 'x':
                pm.move(0, v, absolute=True, worldSpace=True, x=True)
            if axis == 'y':
                pm.move(0, v, absolute=True, worldSpace=True, y=True)
            if axis == 'z':
                pm.move(0, v, absolute=True, worldSpace=True, z=True)
    else:
        lcUtility.Utility.lc_print('Select some components', mode='warning')


def rtb_vert_ops(highresListDropdown, operation, *args, **kwargs):
    ''' '''
    global defaultString
    global lct_cfg
    mainProgBar = pm.mel.eval('$tmp = $gMainProgressBar')
    progBarList = [mainProgBar, prefix + '_progress_control']

    high = highresListDropdown.getValue()

    if not high == defaultString or operation == 'relax':

        pm.undoInfo(openChunk=True)

        sel = pm.ls(sl=True)

        if sel:
            if operation == 'relax' and high == defaultString:
                shape = sel[0]
                liveShape = pm.PyNode(shape.split('.')[0])
            else:
                live = pm.PyNode(high.replace('_high', '_live'))
                liveShape = live.getShape()

            verts = lcGeometry.Geometry.getVertsFromSelection(sel)
            if verts:  # and verts[0].nodeType() == 'mesh':
                try:
                    if operation == 'relax':
                        lcGeometry.Geometry.relaxVerts(verts, liveShape, progBarList)
                    if operation == 'shrink':
                        lcGeometry.Geometry.shrinkWrap(verts, liveShape, progBarList)
                except:
                    for bar in progBarList:
                        pm.progressBar(bar, edit=True, en=False)
                        pm.progressBar(bar, edit=True, endProgress=True)
                    lcUtility.Utility.lc_print_exception('Shrink-wrap did not complete')
            else:
                lcUtility.Utility.lc_print('No verts to shrink wrap!', mode='warning')
            pm.select(sel, r=True)
            # pm.hilite(pm.PyNode(sel[0].split('.')[0]).getParent(), r=True)
            # type = lcGeometry.Geometry.getMeshSelectionType(sel[0])
            # lcGeometry.Geometry.switchSelectType(type)

            pm.undoInfo(closeChunk=True)

    else:
        lcUtility.Utility.lc_print('Select a mesh from the dropdown list', mode='warning')


def rtb_glow(highresListDropdown, *args, **kwargs):
    ''' highlight dropdown list red if nothing is selected '''
    global defaultString
    global lct_cfg

    rtb_update_high_res_shader(highresListDropdown)

    high = highresListDropdown.getValue()

    if high == defaultString:
        highresListDropdown.setBackgroundColor(colorWheel.darkgrey)
        pm.symbolButton(prefix + '_symbolButton_xray', edit=True, enableBackground=False, bgc=colorWheel.maya)
        pm.symbolButton(prefix + '_symbolButton_hide', edit=True, enableBackground=False, bgc=colorWheel.maya)
    else:
        highresListDropdown.setBackgroundColor(colorWheel.mayalight)

        high = pm.PyNode(high)
        vis = high.visibility.get()
        if not vis:
            pm.symbolButton(prefix + '_symbolButton_hide', edit=True, bgc=colorWheel.darkgrey)
        else:
            pm.symbolButton(prefix + '_symbolButton_hide', edit=True, enableBackground=False, bgc=colorWheel.maya)
        xRay = pm.displaySurface(high, query=True, xRay=True)[0]
        if xRay:
            pm.symbolButton(prefix + '_symbolButton_xray', edit=True, bgc=colorWheel.darkgrey)
        else:
            pm.symbolButton(prefix + '_symbolButton_xray', edit=True, enableBackground=False, bgc=colorWheel.maya)
