import os
import pymel.core as pm

import lct.src.core.lcPath as lcPath
import lct.src.core.lcUtility as lcUtility


class Render(object):

    def __init__(self, *args, **kwargs):
        """ Initialize class and variables """

    @classmethod
    def check_vp2(cls, *args, **kwargs):
        '''
        check if vp2 is active and available
        '''
        if pm.ogs(gfx=True) > 0:
            return True
        else:
            return False

    @classmethod
    def lcHWRender(cls, width=2048, height=2048, unique=False, *args, **kwargs):
        ''' '''
        filePath = pm.hwRender(w=width, h=height, edgeAntiAliasing=(2, 16), currentView=True)
        # fix file path for current os
        filePath = os.path.normpath(filePath)
        # rename with unique name
        if unique:
            filePath = lcPath.Path.renameWithTimestamp(filePath, 'render')
        # print the file path
        lcUtility.Utility.lc_print(filePath)

        return filePath

    @classmethod
    def lcOgsRender(cls, width=2048, height=2048, unique=False, *args, **kwargs):
        ''' '''
        filePath = None
        try:
            filePath = pm.ogsRender(w=width, h=height, currentView=True)
            # fix file path for current os
            filePath = os.path.normpath(filePath)
            # rename with unique name
            if unique:
                print "Unique"
                filePath = lcPath.Path.renameWithTimestamp(filePath, 'render')
            # print the file path
            lcUtility.Utility.lc_print(filePath)
        except:
            lcUtility.Utility.lc_print_exception('VP2 not supported')

        return filePath

    @classmethod
    def renderToPhotoshop(cls, width=2048, height=2048, unique=False, renderer='vp2', *args, **kwargs):
        ''' '''
        filePath = None
        if renderer == 'vp2':
            filePath = cls.lcOgsRender(width, height, unique)
        if renderer == 'hw':
            filePath = cls.lcHWRender(width, height, unique)

        lcPath.Path.openImage(filePath)

        return filePath
