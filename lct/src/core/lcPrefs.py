import os
import pymel.core as pm

import lct.src.core.lcPath as lcPath


class MiniPrefsWindow(object):
    def __init__(self, hintCtrl=None, *args, **kwargs):
        """ Initialize class and variables """
        self.name = 'lcMiniPrefsWindow'
        self.window = None
        self.hintCtrl = hintCtrl

    def browse_path(self, ctrl, button=False, *args, **kwargs):
        '''
        '''
        if button:
            path = lcPath.Path.browsePathTextField(ctrl, '', 'Choose an Image Editor Application', mode=1)
            if path and os.path.isfile(path):
                if 'photoshop' in ctrl:
                    pm.optionVar(sv=['PhotoshopDir', path])
                if 'image' in ctrl:
                    pm.optionVar(sv=['EditImageDir', path])
        else:

            path = pm.textField('lcPrefs_photosohp', query=True, text=True)
            if path and os.path.isfile(path):
                pm.optionVar(sv=['PhotoshopDir', path])

            path = pm.textField('lcPrefs_image', query=True, text=True)
            if path and os.path.isfile(path):
                pm.optionVar(sv=['EditImageDir', path])

        if self.hintCtrl:
            if pm.optionVar(query='EditImageDir') and pm.optionVar(query='PhotoshopDir'):
                pm.control(self.hintCtrl, edit=True, visible=False)

    def save_and_close(self, *args, **kwargs):
        '''
        '''
        pm.savePrefs(general=True)
        self.window.delete()

    def show(self, *args, **kwargs):
        ''' '''
        width = 300
        height = 200

        if pm.window(self.name, ex=True):
            pm.deleteUI(self.name)

        self.window = pm.window(self.name, t=self.name, w=width, mxb=False, mnb=False, s=False, toolbox=True)

        pm.columnLayout('lcPrefs_column_main')

        pm.text(l='Maya Preferences', w=width, h=30, al='center', font='boldLabelFont')

        # Image Editing Applications
        # pm.text(l=' Image Editing Applications', font='boldLabelFont')
        pm.frameLayout(l='Image Editing Applications', w=width - 2)
        pm.separator(style='none', h=1)
        cw2 = 25
        cw1 = width - cw2 - 4
        ##Photoshop
        pm.text(l=' Photoshop (PSD) Files', w=width, al='left')
        pm.rowColumnLayout(nc=2, cw=([1, cw1], [2, cw2]))
        photoshop_dir = ''
        if pm.optionVar(query='PhotoshopDir') != 0:
            photoshop_dir = pm.optionVar(query='PhotoshopDir')
        pm.textField('lcPrefs_photosohp', w=cw2, text=photoshop_dir,
                     changeCommand=lambda *args: self.browse_path('lcPrefs_photosohp'))
        pm.symbolButton(image='navButtonBrowse.png', w=cw2,
                        command=lambda *args: self.browse_path('lcPrefs_photosohp', True))
        pm.setParent('..')
        # pm.separator(style='none', h=10)
        ##Others
        pm.text(l=' Other Image Files', w=width, al='left')
        pm.rowColumnLayout(nc=2, cw=([1, cw1], [2, cw2]))
        edit_image_dir = ''
        if pm.optionVar(query='EditImageDir') != 0:
            edit_image_dir = pm.optionVar(query='EditImageDir')
        pm.textField('lcPrefs_image', w=cw2, text=edit_image_dir,
                     changeCommand=lambda *args: self.browse_path('lcPrefs_image'))
        pm.symbolButton(image='navButtonBrowse.png', w=cw2,
                        command=lambda *args: self.browse_path('lcPrefs_image', True))
        pm.setParent('lcPrefs_column_main')
        # pm.separator(style='none', h=10)

        # Save and Close
        pm.separator(style='none', h=10)
        pm.button(l='Save and Close', w=width - 4, h=30, command=lambda *args: self.save_and_close())

        self.window.show()
        pm.window(self.name, edit=True, w=width, h=height)
