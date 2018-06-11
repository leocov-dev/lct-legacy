import os

import pymel.core as pm

import lct.src.core.lcCamera as lcCamera
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
lct_cfg.add('lcCamUtilPop', False)


def lcCamUtilUI(dockable=False, asChildLayout=False, *args, **kwargs):
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

    # UI HERE
    pm.columnLayout(prefix + '_columnLayout_main')
    w = 200
    pm.text(l="Values update for active camera", w=w, h=25, align='center', font='boldLabelFont')

    pm.separator(style='in', h=3, w=winWidth)

    pm.rowColumnLayout(prefix + '_rowColumnMain', nc=2, cw=([1, 150], [2, 50]))

    pm.text(l="Camera Focal Length", w=150)
    ff_focal = pm.floatField(v=35, min=2.5, pre=1, step=1.0, w=50,
                             enterCommand=lambda *args: set_camera_attrs(ui_elements),
                             dragCommand=lambda *args: set_camera_attrs(ui_elements),
                             rfc=lambda *args: get_camera_attrs(ui_elements))

    pm.text(l="Camera Near Clip Plane", w=150)
    ff_near = pm.floatField(v=0.100, min=0.001, pre=3, step=0.001, w=50,
                            enterCommand=lambda *args: set_camera_attrs(ui_elements),
                            dragCommand=lambda *args: set_camera_attrs(ui_elements),
                            rfc=lambda *args: get_camera_attrs(ui_elements))

    pm.text(l="Camera Far Clip Plane", w=150)
    ff_far = pm.floatField(v=1000.0, min=0.001, pre=0, step=10.0, w=50,
                           enterCommand=lambda *args: set_camera_attrs(ui_elements),
                           dragCommand=lambda *args: set_camera_attrs(ui_elements),
                           rfc=lambda *args: get_camera_attrs(ui_elements))

    pm.text(l="Camera Overscan", w=150)
    ff_overscan = pm.floatField(v=1.0, min=0.001, pre=3, step=0.01, w=50,
                                enterCommand=lambda *args: set_camera_attrs(ui_elements),
                                dragCommand=lambda *args: set_camera_attrs(ui_elements),
                                rfc=lambda *args: get_camera_attrs(ui_elements))

    pm.text(l="Camera Background Color", w=150)
    csg_background = pm.colorSliderGrp(cw1=50, rgb=(0.36, 0.36, 0.36),
                                       changeCommand=lambda *args: set_camera_attrs(ui_elements))

    pm.text(l="Camera Gradient Top", w=150)
    csg_top = pm.colorSliderGrp(cw1=50, rgb=(0.54, 0.62, 0.7),
                                changeCommand=lambda *args: set_camera_attrs(ui_elements))

    pm.text(l="Camera Gradient Bottom", w=150)
    csg_bottom = pm.colorSliderGrp(cw1=50, rgb=(0.5, 0.5, 0.5),
                                   changeCommand=lambda *args: set_camera_attrs(ui_elements))

    pm.setParent('..')

    pm.button(l="Toggle Background Gradient", w=winWidth, h=32, al='center', bgc=(0.75, 0.5, 0.2),
              command=lambda *args: lcCamera.Camera.toggle_background())

    ui_elements = [ff_focal, ff_near, ff_far, ff_overscan, csg_background, csg_top, csg_bottom]

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

    # misc
    get_camera_attrs(ui_elements)
    set_camera_attrs(ui_elements)


def set_camera_attrs(ui_elements):
    ''''''
    camera = lcCamera.Camera.get_current_camera()
    focal = ui_elements[0]
    near = ui_elements[1]
    far = ui_elements[2]
    overscan = ui_elements[3]
    background = ui_elements[4]
    top = ui_elements[5]
    bottom = ui_elements[6]

    background_rgb = background.getRgbValue()
    top_rgb = top.getRgbValue()
    bottom_rgb = bottom.getRgbValue()

    camera.focalLength.set(focal.getValue())
    camera.nearClipPlane.set(near.getValue())
    camera.farClipPlane.set(far.getValue())
    camera.overscan.set(overscan.getValue())
    camera.backgroundColor.set(background_rgb)

    pm.displayRGBColor('background', background_rgb[0], background_rgb[1], background_rgb[2])
    pm.displayRGBColor('backgroundTop', top_rgb[0], top_rgb[1], top_rgb[2])
    pm.displayRGBColor('backgroundBottom', bottom_rgb[0], bottom_rgb[1], bottom_rgb[2])


def get_camera_attrs(ui_elements):
    ''''''
    camera = lcCamera.Camera.get_current_camera()
    focal = ui_elements[0]
    near = ui_elements[1]
    far = ui_elements[2]
    overscan = ui_elements[3]
    background = ui_elements[4]
    top = ui_elements[5]
    bottom = ui_elements[6]

    focal.setValue(camera.focalLength.get())
    near.setValue(camera.nearClipPlane.get())
    far.setValue(camera.farClipPlane.get())
    overscan.setValue(camera.overscan.get())
    background.setRgbValue(pm.displayRGBColor('background', q=True))
    top.setRgbValue(pm.displayRGBColor('backgroundTop', q=True))
    bottom.setRgbValue(pm.displayRGBColor('backgroundBottom', q=True))
