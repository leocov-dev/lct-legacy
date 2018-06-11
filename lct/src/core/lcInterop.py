import os
import pymel.core as pm
import platform

from lct.src.core import lcUtility


class Photoshop(object):
    """ send files to Photoshop """

    def __init__(self, psPath='photoshop.exe', *args, **kwargs):
        """ """
        self.psPath = psPath  # os.environ['PHOTOSHOP']
        self.platform = platform.system()

    def openMesh(self, mesh, *args, **kwargs):
        """
        export a mesh as obj and open that file in photoshop
        """
        if self.platform.startswith('win'):

            texture = kwargs.get('texture', False)

            sel = pm.ls(sl=True)
            path = pm.workspace(q=True, rd=True)
            fileName = 'lcMtPs_temp.obj'
            exportFile = os.path.join(path, fileName)

            if texture:
                pm.exportSelected(exportFile, f=2, pr=0, typ='OBJexport', es=1,
                                  op="groups=1;ptgroups=1;materials=1;smoothing=1;normals=1")
            else:
                pm.exportSelected(exportFile, f=2, pr=0, typ='OBJexport', es=1,
                                  op="groups=1;ptgroups=1;materials=0;smoothing=1;normals=1")

            os.system('start "" "' + self.psPath + '" "' + os.path.normcase(exportFile) + '"')
        else:
            lcUtility.Utility.lc_print('Not implemented on your platform', mode='error')
