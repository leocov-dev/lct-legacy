import os

import pymel.core as pm

import lct.src.core.lcColor as lcColor
import lct.src.core.lcConfiguration as lcConfiguration
import lct.src.core.lcGeometry as lcGeometry
import lct.src.core.lcPath as lcPath
import lct.src.core.lcPlugin as lcPlugin
import lct.src.core.lcRender as lcRender
import lct.src.core.lcShader as lcShader
import lct.src.core.lcUI as lcUI
import lct.src.core.lcUtility as lcUtility

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
lct_cfg.add('lcTexGenPop', False)

# tool specific vars
s_texgen_name = 'lcTexGen'
s_aogen_name = 'lcAOGen'


def lcTexGenUI(dockable=False, asChildLayout=False, *args, **kwargs):
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

    # check for dx11Shader plugin
    dx11_available = lcPlugin.Plugin.reload_plugin(plugin='dx11Shader', autoload=True)

    if dx11_available:
        # annotations
        anno_reset = 'Reset Shader'
        anno_attrs = 'Open Shader Attributes'
        anno_clear = 'Clear Shader Assignment'
        anno_assign = 'Assign Shader to Selection'

        ##########
        # Shader1
        a = w / 2
        b = w - a
        pm.rowColumnLayout(prefix + '_rowColumnLayout_shaders', nc=2, cw=([1, a], [2, b]))
        pm.frameLayout(label='Texture', mh=8, mw=8)
        pm.columnLayout()
        pm.rowColumnLayout(nc=2, cw=([1, 6], [2, 64]))
        pm.text(l='')
        pm.swatchDisplayPort(prefix + '_swatch_tex',
                             wh=(64, 64), renderSize=64,
                             pc=lambda *args: lcTxGn_open_shader_attrs(shaderName=s_texgen_name))
        pm.setParent('..')
        pm.separator(style='none', h=8)
        fw = w / 2 - 21
        a = fw * 0.3
        b = fw - a
        pm.rowColumnLayout(nc=2, cw=([1, a], [2, b]))
        pm.button(l='R', w=a, command=lambda *args: lcTxGn_reset_shader(shaderName=s_texgen_name),
                  annotation=anno_reset)
        pm.button(l='Assign', w=b, bgc=(0.75, 0.4, 0.4), command=lambda *args: lcTxGn_assign(shaderName=s_texgen_name),
                  annotation=anno_assign)
        pm.button(l='C', w=a, command=lambda *args: lcTxGn_assign(shaderName=s_texgen_name, mode='clear'),
                  annotation=anno_clear)
        pm.button(l='Attrs', w=b, command=lambda *args: lcTxGn_open_shader_attrs(shaderName=s_texgen_name),
                  annotation=anno_attrs)

        ##########
        # Shader2
        pm.setParent(prefix + '_rowColumnLayout_shaders')
        pm.frameLayout(label='AO', mh=8, mw=8)
        pm.columnLayout()
        pm.rowColumnLayout(nc=2, cw=([1, 6], [2, 64]))
        pm.text(l='')
        pm.swatchDisplayPort(prefix + '_swatch_ao',
                             wh=(64, 64), renderSize=64,
                             pc=lambda *args: lcTxGn_open_shader_attrs(shaderName=s_aogen_name))
        pm.setParent('..')
        pm.separator(style='none', h=8)
        fw = w / 2 - 21
        a = fw * 0.3
        b = fw - a
        pm.rowColumnLayout(nc=2, cw=([1, a], [2, b]))
        pm.button(l='R', w=a, command=lambda *args: lcTxGn_reset_shader(shaderName=s_aogen_name), annotation=anno_reset)
        pm.button(l='Assign', w=b, bgc=(0.75, 0.4, 0.4), command=lambda *args: lcTxGn_assign(shaderName=s_aogen_name),
                  annotation=anno_assign)
        pm.button(l='C', w=a, command=lambda *args: lcTxGn_assign(shaderName=s_aogen_name, mode='clear'),
                  annotation=anno_clear)
        pm.button(l='Attrs', w=b, command=lambda *args: lcTxGn_open_shader_attrs(shaderName=s_aogen_name),
                  annotation=anno_attrs)

        ##########
        # Tools
        pm.setParent(prefix + '_columnLayout_main')
        c = 6
        a = (w / 2) - (c / 2)
        pm.rowColumnLayout(nc=3, cw=([1, a], [2, c], [3, a]))
        pm.columnLayout(w=a)
        pm.button(l='Preview', w=a - 2, command=lambda *args: lcTxGn_preview_shader(),
                  annotation='Preview UV flattened mesh')
        pm.separator(style='none', h=4)
        pm.text(l='VP2 Mode:', w=a)
        pm.text(prefix + '_text_vp2mode', l='OpenGL', w=a)
        pm.setParent('..')
        pm.separator(style='in', w=c, horizontal=False)
        pm.columnLayout(w=a)
        pm.button(l='Render', w=a - 2, command=lambda *args: lcTxGn_render_shader(),
                  annotation='Render UV flattened mesh')
        pm.checkBox(prefix + '_checkBox_overwrite', l='Overwrite Img', v=True)
        pm.checkBox(prefix + '_checkBox_open', l='Auto open PS', v=True)

    # dx11Shader was not found!
    else:
        pm.text(l="dx11Shader plug-in not found", al='center', w=200, h=215, font='boldLabelFont')

    # Show Window
    if not asChildLayout:
        mainWindow.show()
        # force height and width
        pm.window(mainWindow.mainWindow, edit=True, h=winHeight, w=winWidth)
    else:
        pm.separator(style='none', h=5)
        pm.setParent('..')
        pm.setParent('..')

    if dx11_available:
        # edit menus
        optionsMenu, helpMenu = lcUI.UI.lcToolbox_child_menu_edit(asChildLayout, windowName)

        # restore interface from lct_cfg

        # plugins
        lcPlugin.Plugin.reload_plugin(plugin='dx11Shader', autoload=True)
        lcPlugin.Plugin.reload_plugin(plugin='glslShader', autoload=True)

        # activate texture mode
        lcUtility.Editor.update_model_editors(displayAppearance='smoothShaded', displayTextures=True)

        # extra stuff
        vp2RenderingEngine = pm.optionVar(query='vp2RenderingEngine')
        if vp2RenderingEngine in (1, 'DirectX11'):
            pm.text(prefix + '_text_vp2mode', edit=True, l='DX11')
            lcTxGn_init_shaders()
        if vp2RenderingEngine in (2, 'OpenGL'):
            pm.text(prefix + '_text_vp2mode', edit=True, l='OpenGL')
            lcUtility.Utility.lc_print('Switch to DX11, OpenGL not yet implemented', mode='warning')
            pm.columnLayout(prefix + '_columnLayout_main', edit=True, enable=False)


def lcTxGn_init_shaders(*args, **kwargs):
    ''' make the shader if it does not exist
    update connections if it does
    '''
    renderMode = pm.text(prefix + '_text_vp2mode', query=True, l=True)

    shaderType = 'dx11Shader'
    shaderFileExtension = '.fx'

    if renderMode == 'OpenGL':
        shaderType = 'GLSLShader'
        shaderFileExtension = '.glsl'

    texGenShader = lcShader.ShaderNode(s_texgen_name, shaderType)
    texGenShader.create()
    texGenShader.setShaderFile(os.path.join(srcPath, 'shaders', 'lcTexGen{}'.format(shaderFileExtension)))
    texGenShader.setFileTexture('NormalTexture', os.path.join(srcPath, 'shaders', 'texture', 'default_normal.tga'))
    texGenShader.setFileTexture('LitSphereTexture', os.path.join(srcPath, 'shaders', 'texture', 'default_sphere.tga'))
    texGenShader.setFileTexture('TilingSphereTexture',
                                os.path.join(srcPath, 'shaders', 'texture', 'default_tiling.tga'))
    texGenShader.setFileTexture('MaskCube', os.path.join(srcPath, 'shaders', 'texture', 'maskCube.dds'))
    pm.swatchDisplayPort(prefix + '_swatch_tex', edit=True, shadingNode=texGenShader.shaderName)

    aoGenShader = lcShader.ShaderNode(s_aogen_name, shaderType)
    aoGenShader.create()
    aoGenShader.setShaderFile(os.path.join(srcPath, 'shaders', 'lcAOGen{}'.format(shaderFileExtension)))
    aoGenShader.setFileTexture('NormalTexture', os.path.join(srcPath, 'shaders', 'texture', 'default_normal.tga'))
    pm.swatchDisplayPort(prefix + '_swatch_ao', edit=True, shadingNode=aoGenShader.shaderName)

    # make the gradient ramp proxy locators for ramp positions
    if not pm.objExists('LcTxGn'):
        lcTxGnGrp = pm.group(n='LcTxGn', empty=True)
    if not pm.objExists('GradientTop'):
        gradTop = pm.spaceLocator(n='GradientTop')
        gradTop.setPosition((0, 5, 0))
        gradTop.tx.lock()
        gradTop.tz.lock()
        gradTop.rotate.lock()
        gradTop.scale.lock()
        gradTop.getShape().localScale.set(2, 2, 2)
        gradTopAno = lcGeometry.Geometry.getTransformsFromShapes(pm.annotate(gradTop, tx='Gradient Top', p=(1, 7, 0)))[
            0]
        gradTopAno.template.set(1)
        pm.parent(gradTopAno, gradTop)
        pm.parent('GradientTop', 'LcTxGn')
        pm.connectAttr(gradTop.ty, aoGenShader.shader.rampTop)
    if not pm.objExists('GradientBottom'):
        gradBot = pm.spaceLocator(n='GradientBottom')
        gradBot.setPosition((0, 0, 0))
        gradBot.tx.lock()
        gradBot.tz.lock()
        gradBot.rotate.lock()
        gradBot.scale.lock()
        gradBot.getShape().localScale.set(2, 2, 2)
        gradBotAno = \
        lcGeometry.Geometry.getTransformsFromShapes(pm.annotate(gradBot, tx='Gradient Bottom', p=(1, 1, 0)))[0]
        gradBotAno.template.set(1)
        pm.parent(gradBotAno, gradBot)
        pm.parent('GradientBottom', 'LcTxGn')
        pm.connectAttr(gradBot.ty, aoGenShader.shader.rampBottom)


def lcTxGn_open_shader_attrs(shaderName=None, *args, **kwargs):
    ''' open the attribute editor for the shader '''

    shader_node = pm.PyNode(shaderName)
    shader_instance = lcShader.ShaderNode(shader_node.name(), shader_node.type())
    shader_instance.update()

    shader_instance.openAttributeEditor()


def lcTxGn_reset_shader(shaderName=None, *args, **kwargs):
    ''' remake the shader new '''
    renderMode = pm.text(prefix + '_text_vp2mode', query=True, l=True)

    shaderType = 'dx11Shader'
    shaderFileExtension = '.fx'

    if renderMode == 'OpenGL':
        shaderType = 'GLSLShader'
        shaderFileExtension = '.glsl'

    shader_node = pm.PyNode(shaderName)
    shader_instance = lcShader.ShaderNode(shader_node.name(), shader_node.type())
    shader_instance.update()

    # delete and make shader node
    pm.delete(shaderName)

    if shaderName == 'lcTexGen':
        texGenShader = lcShader.ShaderNode(s_texgen_name, shaderType)
        texGenShader.create()
        texGenShader.setShaderFile(os.path.join(srcPath, 'shaders', 'lcTexGen{}'.format(shaderFileExtension)))
        texGenShader.setFileTexture('NormalTexture', os.path.join(srcPath, 'shaders', 'texture', 'default_normal.tga'))
        texGenShader.setFileTexture('LitSphereTexture',
                                    os.path.join(srcPath, 'shaders', 'texture', 'default_sphere.tga'))
        texGenShader.setFileTexture('TilingSphereTexture',
                                    os.path.join(srcPath, 'shaders', 'texture', 'default_tiling.tga'))
        texGenShader.setFileTexture('MaskCube', os.path.join(srcPath, 'shaders', 'texture', 'maskCube.dds'))
        pm.swatchDisplayPort(prefix + '_swatch_tex', edit=True, shadingNode=texGenShader.shaderName)

    if shaderName == 'lcAOGen':
        aoGenShader = lcShader.ShaderNode(s_aogen_name, shaderType)
        aoGenShader.create()
        aoGenShader.setShaderFile(os.path.join(srcPath, 'shaders', 'lcAOGen{}'.format(shaderFileExtension)))
        aoGenShader.setFileTexture('NormalTexture', os.path.join(srcPath, 'shaders', 'texture', 'default_normal.tga'))
        pm.swatchDisplayPort(prefix + '_swatch_ao', edit=True, shadingNode=aoGenShader.shaderName)

    ####
    lcUtility.Utility.lc_print('reset: {}'.format(shaderName))


def lcTxGn_assign(shaderName=None, mode='assign', *args, **kwargs):
    ''' remake the shader new '''

    sel = pm.ls(sl=True)

    if mode == 'clear':
        # get assinged geo
        pm.hyperShade(objects=shaderName)
        # set to lambert1
        pm.sets('initialShadingGroup', edit=True, forceElement=True)
        pm.select(clear=True)

    else:
        if sel:
            shader_node = pm.PyNode(shaderName)
            shader_instance = lcShader.ShaderNode(shader_node.name(), shader_node.type())
            shader_instance.update()

            shader_instance.assign(sel)

        else:
            lcUtility.Utility.lc_print('nothing selected', mode='warning')


def lcTxGn_preview_shader(*args, **kwargs):
    ''' preview the shader in uv mode '''

    preview_mode = pm.PyNode(s_aogen_name).OutputUvSpace.get()
    if preview_mode == False:
        preview_mode = True
    else:
        preview_mode = False

    if preview_mode == True:
        # disable ssao
        pass

    pm.PyNode(s_aogen_name).OutputUvSpace.set(preview_mode)
    pm.PyNode(s_texgen_name).OutputUvSpace.set(preview_mode)


def lcTxGn_render_shader(*args, **kwargs):
    ''' render the shader in uv mode, skip visualization '''

    overwrite = not pm.checkBox(prefix + '_checkBox_overwrite', query=True, value=True)
    open_ps = pm.checkBox(prefix + '_checkBox_open', query=True, value=True)

    # disable ssao
    pm.setAttr("hardwareRenderingGlobals.ssaoEnable", 0)

    # store flat state
    preview_mode = pm.PyNode(s_aogen_name).OutputUvSpace.get()

    # set to flat
    if preview_mode == False:
        pm.PyNode(s_aogen_name).OutputUvSpace.set(True)
        pm.PyNode(s_texgen_name).OutputUvSpace.set(True)

    # render
    renderPath = None
    if open_ps:
        renderPath = lcRender.Render.renderToPhotoshop(width=2048, height=2048, unique=overwrite)
    else:
        renderPath = lcRender.Render.lcOgsRender(width=2048, height=2048, unique=overwrite)

    # return flat state
    pm.PyNode(s_aogen_name).OutputUvSpace.set(False)
    pm.PyNode(s_texgen_name).OutputUvSpace.set(False)
