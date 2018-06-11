import math
import os

import pymel.core as pm

import lct.src.core.lcColor as lcColor
import lct.src.core.lcConfiguration as lcConfiguration
import lct.src.core.lcGeometry as lcGeometry
import lct.src.core.lcPath as lcPath
import lct.src.core.lcPlugin as lcPlugin
import lct.src.core.lcTexture as lcTexture
import lct.src.core.lcUI as lcUI
import lct.src.core.lcUtility as lcUtility

# interface colors
colorWheel = lcColor.ColorWheel(divisions=8, hueRange=[0.0, 0.9], satRange=[0.4, 0.4], valRange=[0.5, 0.5])

# set conf values
conf = lcConfiguration.Conf.load_conf_file(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                                        "{}.conf".format(os.path.basename(__file__).split('.')[0])))
publish = conf['publish']
annotation = conf['annotation']
prefix = conf['prefix']
height = conf['height']
width = 205

# set paths
srcPath = lcPath.Path.getSrcPath()
basePath = os.path.abspath(os.path.dirname(__file__))
iconPath = os.path.normpath(os.path.join(basePath, 'icons'))
# setup undo
undoChunk = False  # used to open/close an undo chunck for drag command rotation slider

# setup configuration node and add necessary attributes
global_cfg = lcConfiguration.GlobalSettingsDictionary()
lct_cfg = lcConfiguration.ConfigurationNode(lcPath.Path.get_tools_settings_file(), global_cfg)
lct_cfg.add('lcUVToolsPop', False)
lct_cfg.add('lcUVToolsShell', True)
lct_cfg.add('lcUVToolsAntialias', False)
lct_cfg.add('lcUVToolsOpenPS', True)
lct_cfg.add('lcUVToolsMove', 1.0)
lct_cfg.add('lcUVToolsScale', 2.0)
lct_cfg.add('lcUVToolsRotate', 45.0)
lct_cfg.add('lcUVToolsSnapshotCustom', False)
lct_cfg.add('lcUVToolsSnapshotSelHeight', 2)
lct_cfg.add('lcUVToolsSnapshotSelWidth', 2)
lct_cfg.add('lcUVToolsSnapshotCustomHeight', 2048)
lct_cfg.add('lcUVToolsSnapshotCustomWidth', 2048)


def lcUVToolsUI(dockable=False, asChildLayout=False, *args, **kwargs):
    ''' '''
    global lct_cfg
    global prefix
    global height

    windowName = 'lcUVTools'
    shelfCommand = 'import lct.src.{0}.{0} as {1}\nreload({1})\n{1}.{0}UI()'.format(windowName, prefix)
    commandString = 'import lct.src.{0}.{0} as {1}\nreload({1})\n{1}.{0}UI(asChildLayout=True)'.format(windowName,
                                                                                                       prefix)
    icon = os.path.join(basePath, 'lcUVTools.png')

    if pm.window(windowName, ex=True):
        pm.deleteUI(windowName)

    if not asChildLayout:
        lcUI.UI.lcToolbox_child_popout(prefix + '_columnLayout_main', windowName, height, commandString, iconPath,
                                       lct_cfg)
        mainWindow = lcUI.lcWindow(prefix=prefix, windowName=windowName, width=width, height=height, icon=icon,
                                   shelfCommand=shelfCommand, annotation=annotation, dockable=dockable, menuBar=True)
        mainWindow.create()

    # column for the uv tool bar
    pm.columnLayout(prefix + '_columnLayout_main')

    # build ui in parts

    # Row 1 - basic
    pm.rowColumnLayout(nc=4, cw=[(1, 95), (2, 35), (3, 35), (4, 35)])
    pm.columnLayout()
    pm.checkBox(prefix + '_checkBox_shell', l='  Shell Mode', v=False,
                changeCommand=lambda *args: lct_cfg.set('lcUVToolsShell',
                                                        pm.checkBox(prefix + '_checkBox_shell', query=True, v=True)))
    pm.button(l='Grab Shell', bgc=colorWheel.getNext(), h=20, w=93, command=lambda *args: lcGeometry.UV().grabShell())
    pm.setParent('..')
    pm.symbolButton(image=os.path.join(srcPath, 'icons', 'temp.png'), enable=False, visible=False)

    button_snapshot = pm.symbolButton(image='polyUVSnapshot.png', annotation='Take UV Snapshot',
                                      command=lambda *args: uvmp_uv_snapshot())
    popup_snapshot = pm.popupMenu(parent=button_snapshot)
    pm.menuItem(prefix + '_checkBox_antiAlias', l='Antialias', checkBox=False, parent=popup_snapshot,
                command=lambda *args: lct_cfg.set('lcUVToolsAntialias',
                                                  pm.menuItem(prefix + '_checkBox_antiAlias', query=True,
                                                              checkBox=True)))
    pm.menuItem(prefix + '_checkBox_openPS', l='Auto Open PS', checkBox=True, parent=popup_snapshot,
                command=lambda *args: lct_cfg.set('lcUVToolsOpenPS',
                                                  pm.menuItem(prefix + '_checkBox_openPS', query=True, checkBox=True)))

    pm.symbolButton(image='textureEditor.png', annotation='Open the UV Editor',
                    command=lambda *args: pm.mel.eval('TextureViewWindow'))
    # pm.text(l='')
    pm.setParent(prefix + '_columnLayout_main')

    # Row 2
    pm.separator(style='in', h=10, w=200)
    row2 = pm.rowColumnLayout(nc=3, cw=[(1, 66), (2, 66), (3, 66)])

    ##MOVE
    pm.columnLayout()
    pm.text(l='Move', w=66, align='center')
    pm.separator(style='none', h=9)
    bgc = colorWheel.getNext()
    pm.rowColumnLayout(nc=3, cw=[(1, 15), (2, 34), (3, 15)])
    pm.text(l='')
    pm.button(l='^', h=15, bgc=bgc,
              command=lambda *args: uvmp_move([0, 1 * pm.floatField(prefix + '_move_value', q=True, v=True)]))
    pm.text(l='')
    pm.button(l='<', bgc=bgc,
              command=lambda *args: uvmp_move([-1 * pm.floatField(prefix + '_move_value', q=True, v=True), 0]))
    pm.floatField(prefix + '_move_value', h=34, v=1.00, pre=2)
    pm.button(l='>', bgc=bgc,
              command=lambda *args: uvmp_move([1 * pm.floatField(prefix + '_move_value', q=True, v=True), 0]))
    pm.text(l='')
    pm.button(l='v', h=15, bgc=bgc,
              command=lambda *args: uvmp_move([0, -1 * pm.floatField(prefix + '_move_value', q=True, v=True)]))
    pm.text(l='')
    pm.setParent(row2)

    ##SCALE
    pm.columnLayout()
    pm.text(l='Scale', w=66, align='center')
    pm.separator(style='none', h=4)
    bgc = colorWheel.getNext()
    pm.rowColumnLayout(nc=3, cw=[(1, 25), (2, 14), (3, 25)])
    pm.button('U+', bgc=bgc, c=lambda *args: uvmp_scale([pm.floatField(prefix + '_scale_value', q=True, v=True), 1]))
    pm.button('+', bgc=bgc, c=lambda *args: uvmp_scale([pm.floatField(prefix + '_scale_value', q=True, v=True),
                                                        pm.floatField(prefix + '_scale_value', q=True, v=True)]))
    pm.button('V+', bgc=bgc, c=lambda *args: uvmp_scale([1, pm.floatField(prefix + '_scale_value', q=True, v=True)]))
    pm.setParent('..')
    pm.rowColumnLayout(nc=3, cw=[(1, 13), (2, 38), (3, 13)])
    pm.text(l='')
    pm.floatField(prefix + '_scale_value', v=2.00, min=1.0, pre=2, h=25)
    pm.text(l='')
    pm.setParent('..')
    pm.rowColumnLayout(nc=3, cw=[(1, 25), (2, 14), (3, 25)])
    pm.button('U-', bgc=bgc, c=lambda *args: uvmp_scale([pm.floatField(prefix + '_scale_value', q=True, v=True) / pow(
        pm.floatField(prefix + '_scale_value', q=True, v=True), 2), 1]))  # x/(x^2)
    pm.button('-', bgc=bgc, c=lambda *args: uvmp_scale([pm.floatField(prefix + '_scale_value', q=True, v=True) / pow(
        pm.floatField(prefix + '_scale_value', q=True, v=True), 2),
                                                        pm.floatField(prefix + '_scale_value', q=True, v=True) / pow(
                                                            pm.floatField(prefix + '_scale_value', q=True, v=True),
                                                            2)]))  # x/(x^2)
    pm.button('V-', bgc=bgc, c=lambda *args: uvmp_scale([1,
                                                         pm.floatField(prefix + '_scale_value', q=True, v=True) / pow(
                                                             pm.floatField(prefix + '_scale_value', q=True, v=True),
                                                             2)]))  # x/(x^2)
    pm.setParent(row2)

    ##ROTATE
    pm.columnLayout()
    pm.text(l='Rotate', w=66, align='center')
    pm.separator(h=2)
    bgc = colorWheel.getNext()
    pm.rowColumnLayout(nc=2, cw=[(1, 16), (2, 48)])
    pm.columnLayout()
    pm.button(prefix + '_clockwise', l='>', bgc=bgc, w=15, h=20,
              c=lambda *args: uvmp_rotate(-pm.floatField(prefix + '_rotate_value', q=True, v=True)))
    pm.button(prefix + '_counter_clockwise', l='<', bgc=bgc, w=15, h=20,
              c=lambda *args: uvmp_rotate(pm.floatField(prefix + '_rotate_value', q=True, v=True)))
    pm.setParent('..')
    pm.floatField(prefix + '_rotate_value', v=45.00, pre=2, h=40)
    pm.setParent('..')
    pm.floatSlider(prefix + '_rotate_free', min=-1, max=1, v=0, w=64, dc=uvmp_rotate_interactive, cc=uvmp_reset_slider)
    pm.button(l='align', bgc=bgc, w=65, h=20, command=lambda *args: uvmp_align_cardinal())
    pm.setParent(prefix + '_columnLayout_main')

    # Row 3
    pm.separator(style='in', h=10, w=200)
    row3 = pm.rowColumnLayout(nc=2, cw=[(1, 100), (2, 100)])
    uvmp_texture_range_UI()
    pm.setParent(row3)
    ##TOOLS
    pm.gridLayout(nrc=[2, 2], cwh=[48, 48])
    pm.symbolButton(image='expandContainer.png', bgc=(0.25, 0.5, 0.25),
                    command=lambda *args: uvmp_split_edges_at_UVs(), annotation='Enter UV Unfold')

    pm.symbolButton(image='collapseContainer.png', bgc=(0.5, 0.25, 0.25),
                    command=lambda *args: uvmp_merge_special(), annotation='Exit UV Unfold')

    pm.symbolButton(image='polyMapCut.png', command=lambda *args: uvmp_cut_edge(), annotation='Cut UV Edge')

    pm.symbolButton(image='textureEditorUnfoldUVsLarge.png', command=lambda *args: uvmp_auto_layout(),
                    annotation='Auto UV Layout')

    pm.setParent(prefix + '_columnLayout_main')

    # #Row 4
    # pm.separator(style='in', h=10, w=200)
    # pm.rowColumnLayout(nc=2, cw=[(1,100), (2,100)])

    # pm.setParent(prefix+'_columnLayout_main')

    #
    if not asChildLayout:
        mainWindow.show()
        pm.window(mainWindow.mainWindow, edit=True, h=height, w=width)
    else:
        pm.setParent('..')
        pm.setParent('..')

    # edit menus
    optionsMenu, helpMenu = lcUI.UI.lcToolbox_child_menu_edit(asChildLayout, windowName)

    # restore interface selections
    pm.checkBox(prefix + '_checkBox_shell', edit=True, value=lct_cfg.get('lcUVToolsShell'))

    # extra stuff
    pm.setFocus(
        prefix + '_move_value')  # set cursor focus on move value, otherwise it sets to first available ui element
    lcPlugin.Plugin.reload_plugin(plugin='Unfold3D', autoload=True)


def uvmp_texture_range_UI(*args, **kwargs):
    """ ui elements for modifing the texture range in the uv editor """
    h = 15
    ofs = 25
    pm.columnLayout(cw=100)
    pm.text(l='Texture Range', al='center', w=100, h=25)
    pm.columnLayout(cw=100, cal='right', co=['left', ofs])

    pm.rowColumnLayout(nc=3, cw=[(1, h), (2, h), (3, h)])

    bgc = colorWheel.getNext()
    pm.button(l='+', bgc=bgc, h=h, c=lambda *args: lcTexture.TextureEditor().setTextureTiling([0.0, 0.0, 0.0, 1.0]))
    pm.text(l='^', h=h)
    pm.button(l='-', bgc=bgc, h=h, c=lambda *args: lcTexture.TextureEditor().setTextureTiling([0.0, 0.0, 0.0, -1.0]))
    pm.setParent('..')
    pm.setParent('..')
    bgc = colorWheel.getNext()

    pm.rowColumnLayout(nc=2, cw=[(1, 49), (2, 49)])
    pm.rowColumnLayout(nc=3, cw=[(1, h), (2, h), (3, h)])
    pm.button(l='+', bgc=bgc, h=h, c=lambda *args: lcTexture.TextureEditor().setTextureTiling([-1.0, 0.0, 0.0, 0.0]))
    pm.text(l='<', h=h)
    pm.button(l='-', bgc=bgc, h=h, c=lambda *args: lcTexture.TextureEditor().setTextureTiling([1.0, 0.0, 0.0, 0.0]))
    pm.setParent('..')
    bgc = colorWheel.getNext()

    pm.rowColumnLayout(nc=3, cw=[(1, h), (2, h), (3, h)])
    pm.button(l='+', bgc=bgc, h=h, c=lambda *args: lcTexture.TextureEditor().setTextureTiling([0.0, 0.0, 1.0, 0.0]))
    pm.text(l='>', h=h)
    pm.button(l='-', bgc=bgc, h=h, c=lambda *args: lcTexture.TextureEditor().setTextureTiling([0.0, 0.0, -1.0, 0.0]))
    pm.setParent('..')
    pm.setParent('..')
    bgc = colorWheel.getNext()

    pm.columnLayout(cw=98, cal='right', co=['left', ofs])
    pm.rowColumnLayout(nc=3, cw=[(1, h), (2, h), (3, h)])
    pm.button(l='+', bgc=bgc, h=h, c=lambda *args: lcTexture.TextureEditor().setTextureTiling([0.0, -1.0, 0.0, 0.0]))
    pm.text(l='v', h=h)
    pm.button(l='-', bgc=bgc, h=h, c=lambda *args: lcTexture.TextureEditor().setTextureTiling([0.0, 1.0, 0.0, 0.0]))
    pm.setParent('..')


# Methods
def uvmp_move(uvw=[0, 0], *args, **kwargs):
    ''' commands for moving uvs or uv shells '''

    shell = pm.checkBox(prefix + '_checkBox_shell', q=True, v=True)

    sel = pm.ls(sl=True)
    if sel:
        uvs = pm.polyListComponentConversion(sel, toUV=True)
        pm.select(uvs, replace=True)
        try:
            if pm.checkBox(prefix + '_checkBox_shell', q=True, v=True):
                lcGeometry.UV().moveShell(uvw)
                lcGeometry.UV().grabShell()  # not necessary to grab the shell, but makes for better visual feedback
            else:
                lcGeometry.UV().move(uvw)
        except:
            lcUtility.Utility.lc_print_exception('something went wrong')
        finally:
            pm.select(sel, replace=True)


def uvmp_scale(uvw=[1, 1], *args, **kwargs):
    ''' commands for scaling uvs or uv shells '''
    shell = pm.checkBox(prefix + '_checkBox_shell', q=True, v=True)

    sel = pm.ls(sl=True)
    if sel:
        uvs = pm.polyListComponentConversion(sel, toUV=True)
        pm.select(uvs, replace=True)
        try:
            if shell:
                uvCenter = lcGeometry.UV().getBoundingBoxCenter(shell=True)
                lcGeometry.UV().scaleShell(uvw, uvCenter)
                lcGeometry.UV().grabShell()  # not necessary to grab the shell, but makes for better visual feedback
            else:
                uvCenter = lcGeometry.UV().getBoundingBoxCenter()
                lcGeometry.UV().scale(uvw, uvCenter)
        except:
            lcUtility.Utility.lc_print_exception('something went wrong')
        finally:
            pm.select(sel, replace=True)


def uvmp_rotate(angle=0, *args, **kwargs):
    ''' rotate uv's based on an angle with aspect ratio correction '''
    shell = pm.checkBox(prefix + '_checkBox_shell', q=True, v=True)

    sel = pm.ls(sl=True)
    if sel:
        uvs = pm.polyListComponentConversion(sel, toUV=True)
        pm.select(uvs, replace=True)
        try:
            texDim = lcTexture.TextureEditor().getTextureDimensions()
            if shell:
                uvCenter = lcGeometry.UV().getBoundingBoxCenter(shell=True)
                lcGeometry.UV().rotateShell(angle, uvCenter, texDim)
            else:
                uvCenter = lcGeometry.UV().getBoundingBoxCenter()
                lcGeometry.UV().rotate(angle, uvCenter, texDim)
        except:
            lcUtility.Utility.lc_print_exception('something went wrong')
        finally:
            pm.select(sel, replace=True)


def uvmp_rotate_interactive(*args, **kwargs):
    '''
    Enables an interactive rotation slider with aspect ratio correction

    Because uv's dont have inherent transforms, it doesn't function like a slider would on an object,
    instead its current slider value is added additionaly to rotate the uv's

    Feels like an 'inertial' slider
    Its progressivly modified to give finer control closer to the slider center
    '''

    try:
        global undoChunk  # if we dont use an undo chunk here each tick of the slider creates a new undo state and we run out of undo's very quickly
        if undoChunk == False:  # if we dont use a state check var each drag command tick try's to open a new chunk and breaks the undo queue
            pm.undoInfo(openChunk=True, chunkName='undo_rotate_interactive')
            undoChunk = True
        angle = pm.floatSlider(prefix + '_rotate_free', q=True, v=True)
        if angle > 0:
            uvmp_rotate(pow(angle * 2, 2) * -1)
        else:
            uvmp_rotate(pow(angle * 2, 2))
    except:
        pass


def uvmp_reset_slider(*args, **kwargs):
    '''
    resets the rotation slider to 0 position after its let go
    '''

    global undoChunk
    if undoChunk == True:  # close the undo chunck on slider release
        pm.undoInfo(closeChunk=True, chunkName='undo_rotate_interactive')
        undoChunk = False
    pm.floatSlider(prefix + '_rotate_free', e=True, v=0)


def uvmp_auto_layout(*args, **kwargs):
    '''
    automaticaly unfold 3d
    '''

    # if int(pm.about(version=True))<=2014:
    #   lcUtility.Utility.lc_print('This command requires Maya 2015 or higher', mode='error')
    if not pm.pluginInfo('Unfold3D', query=True, loaded=True):
        lcUtility.Utility.lc_print('This command requires the Unfold3D plugin', mode='error')
    else:
        sel = pm.ls(sl=True)
        if sel:
            try:
                sel = sel[0]
                if pm.nodeType(sel) != 'transform':
                    sel = pm.listTransforms(sel)[0]
                allFaces = pm.polyListComponentConversion(sel, tf=True)
                pm.polyProjection(allFaces, type='Planar', md='y')

                pm.delete(sel, ch=True)
                uvs = pm.polyListComponentConversion(sel, toUV=True)

                pm.Unfold3D(uvs, u=True, ite=6, p=1, bi=1, tf=1, ms=512, rs=8)
                pm.delete(sel, ch=True)

            except:
                lcUtility.Utility.lc_print_exception('something went wrong unfolding: {}'.format(sel))
            finally:
                pm.select(sel, replace=True)


def uvmp_cut_edge(*args, **kwargs):
    '''
    prepare cuts for unfolding
    '''

    try:
        pm.mel.eval('DetachEdgeComponent;')
    except:
        lcUtility.Utility.lc_print_exception('Could not cut edge')


def uvmp_align_cardinal(*args, **kwargs):
    '''
    automaticaly rotate uv shell to align selected edge vertically or horizontally
    '''

    edges = pm.filterExpand(sm=32, ex=True)
    if edges:
        uvs = pm.polyListComponentConversion(edges[0], toUV=True)
        uvs = pm.filterExpand(uvs, sm=35, ex=True)
        uvA = pm.polyEditUV(uvs[0], q=True)
        uvB = pm.polyEditUV(uvs[1], q=True)
        pm.select(uvs, replace=True)

        xDiff = uvA[0] - uvB[0]
        yDiff = uvA[1] - uvB[1]
        angle = math.degrees(math.atan2(yDiff, xDiff))

        # find the quadrant of the vector and flip the rotation if needed
        sign = 1
        if angle <= 45 and angle > -180:
            sign = -1

        # find the minimum angle
        while abs(angle) > 45:
            if angle > 0:
                angle = 90 - angle
            else:
                angle = 90 + angle

        angle = sign * angle  # invert or not

        try:
            texDim = lcTexture.TextureEditor().getTextureDimensions()
            uvCenter = lcGeometry.UV().getBoundingBoxCenter()
            lcGeometry.UV().grabShell()
            lcGeometry.UV().rotate(angle, uvCenter, texDim)
        except:
            lcUtility.Utility.lc_print_exception('something went wrong')
        finally:
            pm.select(edges, replace=True)
    else:
        lcUtility.Utility.lc_print('Please select an edge to straighten along', mode='warning')


def uvmp_split_edges_at_UVs(*args, **kwargs):
    '''
    automaticaly split edges wherever there is a uv border
    '''

    sel = pm.ls(sl=True)
    if sel and pm.nodeType(sel[0]) == 'transform':
        polyObject = sel[0]
        pm.polyOptions(displayBorder=True, ao=True, sb=3)

        # get the open border uvs
        pm.select(polyObject.map, replace=True)
        pm.polySelectConstraint(t=0x0010, sh=0, bo=1, m=2)
        pm.polySelectConstraint(sh=0, bo=0, m=0)

        borderUVs = pm.ls(sl=True)
        borderEdges = pm.polyListComponentConversion(borderUVs, toEdge=True, internal=True)
        borderEdges = pm.filterExpand(borderEdges, sm=32, ex=True)
        for edge in borderEdges:
            if len(pm.PyNode(edge).connectedFaces()) < 2:
                print edge
                borderEdges.remove(edge)
            else:
                edgeUVs = pm.polyListComponentConversion(edge, toUV=True)
                edgeUVs = pm.filterExpand(edgeUVs, sm=35, ex=True)
                if not len(edgeUVs) > 2:
                    borderEdges.remove(edge)

        print borderEdges
        pm.select(borderEdges, replace=True)
        pm.mel.eval('DetachEdgeComponent;')

        pm.delete(sel, constructionHistory=True)
        pm.select(sel, replace=True)
    else:
        lcUtility.Utility.lc_print('Please select an object', mode='warning')


def uvmp_merge_special(*args, **kwargs):
    '''
    merge with a very close distance
    '''

    sel = pm.ls(sl=True)
    if sel:
        pm.polyMergeVertex(sel, distance=0.001)
        pm.delete(sel, constructionHistory=True)
        pm.polySoftEdge(sel, a=180)
        pm.select(sel, replace=True)
    else:
        lcUtility.Utility.lc_print('Please select one or more objects', mode='warning')


def uvmp_uv_snapshot(*args):
    '''
    Connects the uv snapshot button
    Opens prompt window if no texture is available in the uv editor to source a size from
    '''

    sel = pm.ls(sl=True)
    if sel:
        uvmp_snapshot_window_UI()
    else:
        pm.warning("Select some UV's or Objects")


def uvmp_snapshot_window_UI(*args, **kwargs):
    '''
    this is not called in the main UI section
    its a popup window that lets you set the UV snapshot dimensions
    if there is no texture currently assigned to the model
    '''

    if pm.control(prefix + '_Snapshot', exists=True):
        pm.deleteUI(prefix + '_Snapshot')

    w = 150
    h = 171
    pm.window(prefix + '_Snapshot', t=' ', mxb=False, mnb=False, s=False, widthHeight=[h, h])
    pm.columnLayout(cal='center')
    pm.separator(style='none', h=10, w=w)
    pm.text(l='UV Snapshot Size', font='boldLabelFont', al='center', w=w - 2)
    pm.separator(style='none', h=10, w=w)
    pm.rowColumnLayout(nc=2, cw=[(1, 74), (2, 74)])
    pm.text(l='Width')
    pm.text(l='Height')
    pm.separator(style='none', h=5, w=w)
    pm.separator(style='none', h=5, w=w)
    optionMenuWidth = pm.optionMenu(prefix + '_optionMenu_width', h=25,
                                    enable=(not lct_cfg.get('lcUVToolsSnapshotCustom')),
                                    changeCommand=lambda *args: uvmp_snapshot_window_update())
    optionMenuWidth.addItems(['512', '1024', '2048', '4096'])
    optionMenuWidth.setSelect(lct_cfg.get('lcUVToolsSnapshotSelWidth'))
    optionMenuHeight = pm.optionMenu(prefix + '_optionMenu_height', h=25,
                                     enable=(not lct_cfg.get('lcUVToolsSnapshotCustom')),
                                     changeCommand=lambda *args: uvmp_snapshot_window_update())
    optionMenuHeight.addItems(['512', '1024', '2048', '4096'])
    optionMenuHeight.setSelect(lct_cfg.get('lcUVToolsSnapshotSelHeight'))
    pm.setParent('..')

    pm.rowColumnLayout(nc=2, cw=[(1, 32), (2, 100)])
    pm.text(l='')
    pm.checkBox(prefix + '_custom_snapshot_size', l='Custom Size?', value=lct_cfg.get('lcUVToolsSnapshotCustom'),
                changeCommand=lambda *args: uvmp_snapshot_window_update())
    pm.setParent('..')

    pm.rowColumnLayout(nc=2, cw=[(1, 74), (2, 74)])
    pm.intField(prefix + '_snapshot_width', v=lct_cfg.get('lcUVToolsSnapshotCustomWidth'),
                enable=lct_cfg.get('lcUVToolsSnapshotCustom'),
                changeCommand=lambda *args: uvmp_snapshot_window_update())
    pm.intField(prefix + '_snapshot_height', v=lct_cfg.get('lcUVToolsSnapshotCustomHeight'),
                enable=lct_cfg.get('lcUVToolsSnapshotCustom'),
                changeCommand=lambda *args: uvmp_snapshot_window_update())
    pm.setParent('..')

    pm.separator(style='none', h=15, w=w)
    pm.button(l='Take Snapshot', w=w - 2, h=35, c=lambda *args: uvmp_snapshot_execute())

    pm.showWindow(prefix + '_Snapshot')

    pm.window(prefix + '_Snapshot', edit=True, w=w, h=h)


def uvmp_snapshot_window_update(*args, **kwargs):
    '''
    update the snapshot window on user interaction
    '''

    checkBoxState = pm.checkBox(prefix + '_custom_snapshot_size', query=True, value=True)

    # toggle input based on checkbox
    pm.intField(prefix + '_snapshot_width', edit=True, enable=checkBoxState)
    pm.intField(prefix + '_snapshot_height', edit=True, enable=checkBoxState)
    pm.optionMenu(prefix + '_optionMenu_width', edit=True, enable=(not checkBoxState))
    pm.optionMenu(prefix + '_optionMenu_height', edit=True, enable=(not checkBoxState))

    if not checkBoxState:
        # update custom fields with dropdown values
        width = int(pm.optionMenu(prefix + '_optionMenu_width', query=True, value=True))
        height = int(pm.optionMenu(prefix + '_optionMenu_height', query=True, value=True))
        pm.intField(prefix + '_snapshot_width', edit=True, value=width)
        pm.intField(prefix + '_snapshot_height', edit=True, value=height)

    selWidth = pm.optionMenu(prefix + '_optionMenu_width', query=True, select=True)
    selHeight = pm.optionMenu(prefix + '_optionMenu_height', query=True, select=True)
    snapWidth = pm.intField(prefix + '_snapshot_width', query=True, value=True)
    snapHeight = pm.intField(prefix + '_snapshot_height', query=True, value=True)

    lct_cfg.set('lcUVToolsSnapshotCustom', checkBoxState)
    lct_cfg.set('lcUVToolsSnapshotSelHeight', selHeight)
    lct_cfg.set('lcUVToolsSnapshotSelWidth', selWidth)
    lct_cfg.set('lcUVToolsSnapshotCustomHeight', snapHeight)
    lct_cfg.set('lcUVToolsSnapshotCustomWidth', snapWidth)


def uvmp_snapshot_execute(*args, **kwargs):
    '''
    takes the snapshot and opens it in photoshop, deletes the popup window if necessary
    '''

    texDim = [pm.intField(prefix + '_snapshot_width', q=True, v=True),
              pm.intField(prefix + '_snapshot_height', q=True, v=True)]
    path = pm.workspace(q=True, rd=True)
    fileName = prefix + '_temp_uvsnapshot.tga'
    snapShotFile = os.path.join(path, fileName)
    lcTexture.TextureEditor().uvSnapshot(snapShotFile, texDim[0], texDim[1],
                                         bool(pm.menuItem(prefix + '_checkBox_antiAlias', q=True, cb=True)))

    if pm.menuItem(prefix + '_checkBox_openPS', q=True, cb=True):
        lcPath.Path.openImage(snapShotFile)
    else:
        lcUtility.Utility.lc_print('Created UV Snapshot: {}'.format(snapShotFile))

    if pm.control(prefix + '_Snapshot', exists=True):
        pm.deleteUI(prefix + '_Snapshot')
