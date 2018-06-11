import os

import pymel.core as pm

import lct.src.core.lcColor as lcColor
import lct.src.core.lcConfiguration as lcConfiguration
import lct.src.core.lcGeometry as lcGeometry
import lct.src.core.lcPath as lcPath
import lct.src.core.lcPlugin as lcPlugin
import lct.src.core.lcUI as lcUI
import lct.src.core.lcUtility as lcUtility

# interface colors
hue = 0.6
colorWheel = lcColor.ColorWheel(divisions=2, hueRange=[hue,hue], satRange=[0.4,0.7], valRange=[0.4,0.4])

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

defaultPath = 'Export Path . . .'

# #setup configuration node and add necessary attributes
global_cfg = lcConfiguration.GlobalSettingsDictionary()
lct_cfg = lcConfiguration.ConfigurationNode(lcPath.Path.get_tools_settings_file(), global_cfg)
lct_cfg.add('lcObjToolsPop', False)
lct_cfg.add('lcObjToolsPath', defaultPath)
lct_cfg.add('lcObjToolsPrefix', '')
lct_cfg.add('lcObjToolsExportIndividual', True)
lct_cfg.add('lcObjToolsUseSmoothPreview', True)

def lcObjToolsUI(dockable=False, asChildLayout=False, *args, **kwargs):
    ''' '''
    global lct_cfg
    global prefix

    ci = 0 #color index iterator
    windowName = 'lcObjTools'
    shelfCommand = 'import lct.src.{0}.{0} as {1}\nreload({1})\n{1}.{0}UI()'.format(windowName, prefix)
    commandString = 'import lct.src.{0}.{0} as {1}\nreload({1})\n{1}.{0}UI(asChildLayout=True)'.format(windowName, prefix)
    icon = os.path.normpath(os.path.join(basePath, 'lcObjTools.png'))
    winWidth  = 205
    winHeight = 158

    if pm.window(windowName, ex=True):
        pm.deleteUI(windowName)

    if not asChildLayout:
        lcUI.UI.lcToolbox_child_popout(prefix+'_columnLayout_main', windowName, height, commandString, iconPath, lct_cfg)
        mainWindow = lcUI.lcWindow(prefix=prefix, windowName=windowName, width=winWidth, height=winHeight, icon=icon, shelfCommand=shelfCommand, annotation=annotation, dockable=dockable, menuBar=True)
        mainWindow.create()

    #
    pm.columnLayout(prefix+'_columnLayout_main')

    #
    lcUI.UI.lc_browse_field_button(width=200, textFieldName=prefix+'_textField_export_path', lct_cfg=lct_cfg, configAttr='lcObjToolsPath', placeholderText=defaultPath, annotation='Choose an OBJ export directory', fileMask='Wavefront Obj (*.obj)')
    pm.setParent(prefix+'_columnLayout_main')

    #
    pm.checkBox(prefix+'_checkBox_export_indi', l='Export Individual', v=True, changeCommand=lambda *args: lct_cfg.set('lcObjToolsExportIndividual', pm.checkBox(prefix+'_checkBox_export_indi', query=True, v=True)))
    pm.checkBox(prefix+'_checkBox_use_smooth', l='Use Smooth Preview', v=True, changeCommand=lambda *args: lct_cfg.set('lcObjToolsUseSmoothPreview', pm.checkBox(prefix+'_checkBox_use_smooth', query=True, v=True)))

    #
    pm.rowColumnLayout(nc=2, cw=([1,100], [2,100]) )
    pm.textField(prefix+'_textField_prefix', w=100, tx=' ', changeCommand=lambda *args: lct_cfg.set('lcObjToolsPrefix', pm.textField(prefix+'_textField_prefix', query=True, tx=True)))
    pm.text(l='   Prefix_', al='left')
    pm.setParent(prefix+'_columnLayout_main')

    #
    pm.rowColumnLayout(nc=2, cw=([1,166], [2,34]) )
    pm.columnLayout(w=169)
    pm.button(prefix+'_button_export', l='Export OBJ', bgc=colorWheel.getColorRGB(ci), annotation='Export the selected geometry', w=166, h=30, command=lambda *args: lcObj_exportObjs() )
    ci+=1
    pm.button(prefix+'_button_Import', l='Import Multiple OBJs', bgc=colorWheel.getColorRGB(ci), annotation='Clean import more than one obj', w=166, h=20, command=lambda *args: lcObj_importMultiple() )
    ci+=1
    pm.setParent('..')
    pm.columnLayout(w=31)
    pm.symbolButton(prefix+'_button_open_folder', w=30, h=50, bgc=(0.18,0.18,0.18), image=os.path.join(srcPath, 'icons', 'folder_med.png'), annotation='Open the export folder', command=lambda *args: lcObj_open_file_path(pm.textField(prefix+'_textField_export_path', query=True, text=True) ) )
    ci+=1

    #
    if not asChildLayout:
        mainWindow.show()
        pm.window(mainWindow.mainWindow, edit=True, h=winHeight, w=winWidth)
    else:
        pm.setParent('..')
        pm.setParent('..')

    #edit menus
    optionsMenu, helpMenu = lcUI.UI.lcToolbox_child_menu_edit(asChildLayout, windowName)

    pm.menuItem(parent=optionsMenu, divider=True, dividerLabel=windowName)
    pm.menuItem(parent=optionsMenu, l="Offset External .obj's", command=lambda *args: lcObj_offsetMultiple() )

    #restore interface selections
    pm.checkBox(prefix+'_checkBox_export_indi', edit=True, value=lct_cfg.get('lcObjToolsExportIndividual'))
    pm.checkBox(prefix+'_checkBox_use_smooth', edit=True, value=lct_cfg.get('lcObjToolsUseSmoothPreview'))
    pm.textField(prefix+'_textField_export_path', edit=True, text=lct_cfg.get('lcObjToolsPath'))
    pm.textField(prefix+'_textField_prefix', edit=True, text=lct_cfg.get('lcObjToolsPrefix'))

    #run extra stuff
    lcPlugin.Plugin.reload_plugin(plugin='objExport', autoload=True)
    # validate export directory
    lcPath.Path.validatePathTextField(prefix+'_textField_export_path', lct_cfg, 'lcObjToolsPath', defaultPath)

def lcObj_open_file_path(path):
    '''
        open the file path from the UI
        open the current scene path if textField path is not valid
    '''
    if not os.path.exists(path):
        path = os.path.dirname(pm.sceneName())

    lcPath.Path.openFilePath(path)

def lcObj_exportObjs(*args, **kwargs):
    ''' Export .obj files from selected geometry, either as one combined file or as individual files per object.  Will recognize and convert poly smooth preview to geometry for export '''
    global lct_cfg
    global prefix
    global defaultPath

    path = pm.textField(prefix+'_textField_export_path', query=True, text=True)
    objPrefix = pm.textField(prefix+'_textField_prefix', query=True, text=True)
    if objPrefix:
        objPrefix+='_'

    if path and path != defaultPath:

        sel = pm.ls(sl=True)

        if sel:
            sel = lcGeometry.Geometry.filterForGeometry(sel)
            #undo is the easiest way to work on geometry temporarily
            pm.undoInfo(openChunk=True)

            if sel:

                if pm.checkBox(prefix+'_checkBox_use_smooth', query=True, v=True):
                    for obj in sel:
                        pm.select(obj)
                        #find the objects currently displayed as smooth and create converted poly copies
                        if pm.displaySmoothness(q=True, polygonObject=True)[0] == 3:
                            pm.mel.performSmoothMeshPreviewToPolygon()

                if pm.checkBox(prefix+'_checkBox_export_indi', query=True, v=True):
                    #export objects individually
                    for obj in sel:
                        pm.select(obj)
                        nameSplit = str(obj).split('|')
                        if len(nameSplit) > 1:
                            name = nameSplit[-1]
                        else:
                            name = nameSplit[0]
                        exportString = os.path.normpath(os.path.join(path,str(objPrefix+name+'.obj')))
                        try:
                            pm.exportSelected(exportString, force=True, options='groups=1;ptgroups=1;materials=0;smoothing=1;normals=1', type='OBJexport', pr=True, es=True)
                            lcUtility.Utility.lc_print('Exporting: {0}'.format(exportString))
                        except:
                            lcUtility.Utility.lc_print_exception('Failed to export: {0}'.format(exportString))
                    #undo export individually
                    pm.undoInfo(closeChunk=True)
                    pm.undo()

                else:
                    #export as one object
                    pm.select(sel)
                    name = ''
                    while name == '':
                        dialog = pm.promptDialog(title='OBJ Name', message='Enter Name:', button=['OK', 'Cancel'], defaultButton='OK', cancelButton='Cancel', dismissString='Cancel')
                        if dialog == 'OK':
                            name = pm.promptDialog(query=True, text=True)
                            if name:
                                exportString = os.path.normpath(os.path.join(path,str(objPrefix+name+'.obj')))
                                try:
                                    pm.exportSelected(exportString, force=True, options='groups=1;ptgroups=1;materials=0;smoothing=1;normals=1', type='OBJexport', pr=True, es=True)
                                    pm.undoInfo(closeChunk=True)
                                    pm.undo()
                                    lcUtility.Utility.lc_print('Exporting: {0}'.format(exportString))
                                except:
                                    pm.undoInfo(closeChunk=True)
                                    pm.undo()
                                    lcUtility.Utility.lc_print('Failed to export: {0}'.format(exportString), mode='warning')
                            else:
                                pm.undoInfo(closeChunk=True)
                                pm.undo()
                                lcUtility.Utility.lc_print("You didn't type a name for your obj", mode='warning')
                        if dialog == 'Cancel':
                            pm.undoInfo(closeChunk=True)
                            pm.undo()
                            break

                pm.select(sel)

            else:
                lcUtility.Utility.lc_print('Select a mesh first', mode='warning')
        else:
            lcUtility.Utility.lc_print('Select a mesh first', mode='warning')
    else:
        lcUtility.Utility.lc_print('Did you set a path?', mode='warning')

def lcObj_importMultiple(*args, **kwargs):
    ''' select multiple .obj's and import them into the scene with best settings '''
    global lct_cfg

    path = pm.textField(prefix+'_textField_export_path', query=True, text=True)
    filter = "Wavefront Obj (*.obj)"
    files = pm.fileDialog2(ds=1, caption="Choose one or more Obj's to import", dir=path, fileFilter=filter, fileMode=4)
    if files:
        for obj in files:
            name = obj.split('/')[-1].split('.')[0]
            importedObj = pm.importFile(obj, type='OBJ', options='mo=0')

def lcObj_offsetMultiple(mode='select', files=None, offset=[0,0,0], *args, **kwargs):
    '''
    select multiple external .obj files and offset them in worldspace
    '''
    # Select ###########################
    if mode=='select':
        path = pm.textField(prefix+'_textField_export_path', query=True, text=True)
        filter = "Wavefront Obj (*.obj)"
        files = pm.fileDialog2(ds=1, caption="Choose one or more Obj's to offset", dir=path, fileFilter=filter, fileMode=4)
        if files:
            lcObj_offsetMultiple(mode='window', files=files)
        else:
            lcUtility.Utility.lc_print("You didn't select anything . . .")

    # Window ###########################
    windowName = 'lcObj_offset_window'

    if mode=='window':
        if pm.control(windowName, exists = True):
            pm.deleteUI(windowName)

        w=200
        h=85
        offsetWindow = pm.window(windowName, t="lcObjTools - Obj Offset", widthHeight=[w+2,h], rtf=False, mnb=False, mxb=False, s=False, toolbox=True)
        pm.columnLayout()
        pm.text(l='Enter Obj Offset', w=w, h=25, al='center', font='boldLabelFont')
        a=(w/3)*0.2
        b=(w/3)-a
        pm.rowColumnLayout(nc=6, cw=([1,a], [2,b], [3,a], [4,b], [5,a], [6,b]) )
        pm.text(l='X', w=a, al='center', font='boldLabelFont')
        pm.floatField('o_x', w=b, v=0.0)
        pm.text(l='Y', w=a, al='center', font='boldLabelFont')
        pm.floatField('o_y', w=b, v=0.0)
        pm.text(l='Z', w=a, al='center', font='boldLabelFont')
        pm.floatField('o_z', w=b, v=0.0)
        pm.setParent('..')
        pm.separator(style='none', h=5)
        b=100
        a=(w-b)/2
        pm.rowColumnLayout(nc=3, cw=([1,a], [2,b], [3,a]) )
        pm.text(l='')
        pm.button(l='Offset', w=b, command=lambda *args: lcObj_offsetMultiple(mode='execute', files=files, offset=[pm.floatField('o_x',q=True,v=True), pm.floatField('o_y',q=True,v=True), pm.floatField('o_z',q=True,v=True)]) )
        pm.text(l='')

        offsetWindow.show()
        pm.window(offsetWindow, edit=True, wh=[w+2,h])

    # Execute ###########################
    if mode=='execute':
        i = 1
        for f in files:
            fileName, fileExtension = os.path.splitext(f)
            outputFile = '{}_Offset{}'.format(fileName, fileExtension)
            obj = lcGeometry.Obj(f, True, '[{} of {}]'.format(i, len(files)) )
            obj.edit_verts(offset)
            obj.write(outputFile)
            obj.flush()

            i=i+1
        if pm.control(windowName, exists = True):
            pm.deleteUI(windowName)