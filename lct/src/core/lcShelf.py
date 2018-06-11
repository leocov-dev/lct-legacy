import os
import platform

import pymel.core as pm

import lct.src.core.lcPath as lcPath
import lct.src.core.lcUtility as lcUtility


class Shelf(object):

    @classmethod
    def makeLcToolboxShelfIcon(cls, *args, **kwargs):
        '''
        Mel:
            python "exec ('import lct.src.core.lcShelf as lcShelf\\nreload(lcShelf)\\nlcShelf.Shelf.makeLcToolboxShelfIcon()')";
        Python:
            exec 'import lct.src.core.lcShelf as lcShelf\nreload(lcShelf)\nlcShelf.Shelf.makeLcToolboxShelfIcon()'
        '''
        try:
            srcPath = lcPath.Path.getSrcPath()

            shelfCommand = 'import lct.src.lcToolbox.lcToolbox as lcTb\nreload(lcTb)\nlcTb.lcToolboxUI()'
            shelfIcon = os.path.join(srcPath, 'lcToolbox', 'lcToolbox.png')
            annotation = "LEOCOV Toolbox"
            cls.makeShelfButton('lcToolbox', shelfCommand, shelfIcon, annotation)
        except:
            lcUtility.Utility.lc_print_exception(message='Failed to make shelf icon')

    @classmethod
    def makeShelfButton(cls, name, command, icon, annotation='', *args, **kwargs):
        """ """
        myPlatform = platform.system()
        if myPlatform.startswith('Win'):
            icon = icon.replace('\\', '/')

        try:
            currentShelf = pm.mel.eval('tabLayout -q -st $gShelfTopLevel;')

            # find the button if it already exists and delete it
            buttonArray = pm.shelfLayout(currentShelf, query=True, childArray=True)
            if buttonArray:
                items = [item for item in buttonArray if
                         pm.objectTypeUI(item) == 'shelfButton']  # get only shelfButtons, just in case
                for i in items:
                    label = pm.shelfButton(i, query=True, label=True)
                    if label == name:
                        pm.deleteUI(i)

            pm.setParent(currentShelf)

            pm.shelfButton(label=name, annotation=annotation, image1=icon, command=command)
        except:
            lcUtility.Utility.lc_print_exception(message='Something went wrong making the shelf icon')

    @classmethod
    def makeLctShelf(cls, *args, **kwargs):
        """ """
        src = lcPath.Path.getSrcPath()
        mel = lcPath.Path.getMelPath()
        shelf = os.path.normpath(os.path.join(mel, 'shelf_LCT.mel'))

        file = open(shelf, 'w+')
        opening = 'global proc shelf_LCT () {\n    global string $gBuffStr;\n    global string $gBuffStr0;\n    global string $gBuffStr1;\n\n'
        closing = '\n}'

        file.write(opening)

        initShelfIcon = os.path.normpath(os.path.join(src, 'icons', 'shelf.png'))
        initShelfLabel = 'Init Shelf'
        initShelfAnno = 'Initialize LCT Shelf'
        initShelfCommand = 'from lct.src.core.lcShelf import Shelf as shelf\nshelf.makeLctShelf()'

        file.write(closing)

        file.close()

        if not pm.layout('LCT', ex=True):
            if os.name == 'nt':
                shelf = shelf.replace('\\', '/')
            pm.mel.loadNewShelf(shelf)
            pm.shelfButton(label=initShelfLabel, annotation=initShelfAnno, image1=initShelfIcon,
                           command=initShelfCommand)
        else:
            pm.mel.eval('shelfTabLayout -edit -selectTab "LCT" $gShelfTopLevel;')

        list = lcUtility.Utility.buildPublishList(inline=False)
        for item in list:
            if item[3] == 'True':
                label = item[0]
                annotation = item[2]
                icon = os.path.normpath(os.path.join(src, label, item[0] + '.png'))
                runCommand = item[4]

                cls.makeShelfButton(label, runCommand, icon, annotation)
