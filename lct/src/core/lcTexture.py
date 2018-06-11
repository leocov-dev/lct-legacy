import os
import xml.dom.minidom
from xml.dom.minidom import Document

import pymel.core as pm

import lct.src.core.lcPath as lcPath
import lct.src.core.lcUtility as lcUtility


class Texture(object):

    def __init__(self, *args, **kwargs):
        """ Initialize class and variables """
        self.settingsPath = lcPath.Path.getSettingsPath() + '/'

    @classmethod
    def filterForTextures(cls, textureList, *args, **kwargs):
        ''' filter a list for only file texture nodes '''
        newList = []
        if textureList:
            for item in textureList:
                type = pm.nodeType(item)
                if type == 'file':
                    newList.append(item)
        return newList

    @classmethod
    def renameAllTextureNodes(cls, prefix='tx', *args, **kwargs):
        """ rename texture nodes based on the name of linked file """
        textures = pm.ls(exactType='file')
        for tex in textures:
            pre = prefix
            if tex.fileTextureName.get() != "":
                path = tex.fileTextureName.get()
                fileName = os.path.split(path)[1].split('.')[0]
                if prefix:
                    pre = '{}_'.format(pre)
                try:
                    pm.rename(tex, pre + fileName)
                except:
                    lcUtility.Utility.lc_print("Could not rename: {}".format(tex), mode='warning')

    @classmethod
    def repathTextures(cls, texList, newPath, *args, **kwargs):
        ''' repath the textures in a given list '''
        if texList:
            for tex in texList:
                try:
                    oldPath = pm.getAttr(tex + '.fileTextureName')
                    fixedPath = lcPath.Path.repath(oldPath, newPath)
                    if os.path.exists(fixedPath):
                        pm.setAttr(tex + '.fileTextureName', fixedPath)
                except:
                    lcUtility.Utility.lc_print_exception()

    @classmethod
    def intelligentRepath(cls, texList, rootPath):
        # use filePathEditor command instead
        ''' start from a given rootPath and find matches to the texList to link '''
        try:
            # rootPath = os.path.normpath(rootPath.encode('string-escape'));
            texture_list = []
            found_list = []
            walk_list = []
            if texList:
                if os.path.exists(rootPath):
                    for root, dirs, files in os.walk(rootPath):
                        for file in files:
                            walk_list.append([root, file])

                    for tex in texList:
                        # Build a master list of the file node and texture name
                        old_path = pm.getAttr(tex + '.fileTextureName')
                        if old_path:
                            # in case of empty texture node
                            file_name = os.path.basename(old_path)
                            texture_list.append((tex, file_name))

                    for tex_obj in texture_list:
                        for file_obj in walk_list:
                            if tex_obj[1] == file_obj[1]:
                                # file found
                                file_path = os.path.join(file_obj[0], file_obj[1])
                                try:
                                    lcUtility.Utility.lc_print("FOUND: {} at {}".format(tex_obj[1], file_path))
                                    # Link to new path
                                    tex_obj[0].fileTextureName.set(file_path)
                                except:
                                    lcUtility.Utility.lc_print(
                                        "Could not set texture on {} to {}".format(tex_obj[0], file_path))
                                finally:
                                    found_list.append(tex_obj)

                    texture_list = [x for x in texture_list if x not in found_list]

                    if texture_list:
                        texture_string = ""
                        for tex in texture_list:
                            texture_string = texture_string + "Texture: {}, {}\n".format(tex[0], tex[1])
                        lcUtility.Utility.lc_print(
                            "Some textures not found at new path\nPath: {}\n{}".format(rootPath, texture_string),
                            mode='warning')
                else:
                    lcUtility.Utility.lc_print("{} is not a valid path".format(rootPath), mode='error')
            else:
                lcUtility.Utility.lc_print("No textures passed to function", mode='error')
        except:
            lcUtility.Utility.lc_print_exception("Problem repathing texture list")

    @classmethod
    def intelligentRepathAll(cls, rootPath):
        ''' start from a given rootPath and find matches to the texList to link '''
        try:
            # rootPath = os.path.normpath(rootPath.encode('string-escape'));
            if os.path.exists(rootPath):
                texList = pm.ls(exactType='file')
                cls.intelligentRepath(texList, rootPath)
            else:
                lcUtility.Utility.lc_print("{} is not a valid path".format(rootPath), mode='error')
        except:
            lcUtility.Utility.lc_print_exception("Problem repathing all textures")

    @classmethod
    def reloadTexture(cls, texNode, *args, **kwargs):
        ''' reloads a single texture node '''
        path = pm.getAttr(texNode + '.fileTextureName')
        if os.path.exists(path):
            pm.setAttr(texNode + '.fileTextureName', path)
            lcUtility.Utility.lc_print('Reload Node: {0}, Path: {1}'.format(texNode, path))
        pm.refresh()

    @classmethod
    def reloadTextures(cls, *args, **kwargs):
        ''' reloads all texture files in a scene '''
        sel = pm.ls(typ='file')
        for tex in sel:
            cls.reloadTexture(tex)

    @classmethod
    def reloadTextureList(cls, texList, *args, **kwargs):
        ''' reloads a list of texture nodes '''
        for tex in texList:
            cls.reloadTexture(tex)

    @classmethod
    def openTextureList(cls, texList, *args, **kwargs):
        ''' open a list of file nodes in default program ie. photoshop '''
        for item in texList:
            texPath = pm.getAttr(item + '.fileTextureName')
            lcPath.Path.openImage(texPath)

    def saveTextureList(self, *args, **kwargs):
        '''
        write an xml file with a list of the scenes textures and timestamps
        '''
        fileNodes = pm.ls(type='file')
        sceneName = lcPath.Path.getSceneName()
        xmlFileName = sceneName + '_textureList'

        doc = Document()
        textureList = doc.createElement('textureList')
        textureList.setAttribute('sceneName', sceneName)
        doc.appendChild(textureList)

        for node in fileNodes:
            fileTextureName = pm.getAttr(node + '.fileTextureName')
            if os.path.isfile(fileTextureName):
                time = os.path.getmtime(fileTextureName)

                textureNode = doc.createElement('textureNode')
                textureNode.setAttribute('nodeName', node)
                textureList.appendChild(textureNode)

                texturePath = doc.createElement('path')
                texturePath.appendChild(doc.createTextNode(fileTextureName))
                textureNode.appendChild(texturePath)

                textureTime = doc.createElement('time')
                textureTime.appendChild(doc.createTextNode(str(time)))
                textureNode.appendChild(textureTime)

        f = open(self.settingsPath + xmlFileName + '.xml', 'w+')
        # f.write(doc.toprettyxml(indent='    ') ) #This is super slow !!!!!
        doc.writexml(f)
        f.close()

    def reloadChangedTextures(self, *args, **kwargs):
        ''' '''
        fileNodes = pm.ls(type='file')
        sceneName = lcPath.Path.getSceneName()
        xmlFileName = sceneName + '_textureList'

        if os.path.exists(self.settingsPath + xmlFileName + '.xml'):
            textureList = xml.dom.minidom.parse(self.settingsPath + xmlFileName + '.xml')

            for node in fileNodes:
                fileTextureName = pm.getAttr(node + '.fileTextureName')

                for nodeStored in textureList.getElementsByTagName('textureNode'):
                    nodeNameStored = nodeStored.getAttribute('nodeName')
                    if node == nodeNameStored:
                        time = os.path.getmtime(fileTextureName)

                        timeList = nodeStored.getElementsByTagName('time')
                        timeNode = timeList[0]
                        timeChild = timeNode.firstChild
                        timeStored = timeChild.data

                        if str(time) != timeStored:
                            self.reloadTexture(node)

            self.saveTextureList()
        else:
            self.saveTextureList()
            self.reloadTextures()


class TextureEditor(object):
    """
        Methods to get and set info related to the UV Editor and objects linked to it

    """

    def __init__(self, *args, **kwargs):
        """ set some initial values """
        self.uvTextureView = pm.getPanel(
            scriptType='polyTexturePlacementPanel')  # specifies the UV Texture Editor, there is only one

    def getTextureTiling(self, *args, **kwargs):
        '''
            return format is [U min, V min, U max, V max]
            return the sizing matrix for the UV Editor's image tiling

        '''
        currentSize = pm.textureWindow(self.uvTextureView[0], q=True, imageTileRange=True)
        return currentSize

    def setTextureTiling(self, resizeMatrix, *args, **kwargs):
        '''
            input and return format is [U min, V min, U max, V max]
            Resizes the range the texture image is tiled in the UV Editor

        '''
        currentSize = pm.textureWindow(self.uvTextureView[0], q=True, imageTileRange=True)
        newSize = [currentSize[0] + resizeMatrix[0], currentSize[1] + resizeMatrix[1], currentSize[2] + resizeMatrix[2],
                   currentSize[3] + resizeMatrix[3]]  # add the matrices together
        pm.textureWindow(self.uvTextureView[0], e=True, imageTileRange=list(newSize))
        return newSize

    def getTextureDimensions(self, *args, **kwargs):
        '''
            returns the dimensions of the currently displayed texture in the UV Editor
            If there is no texture loaded returns a default [1,1]

        '''
        textureDimensions = [1, 1]

        numImages = pm.textureWindow(self.uvTextureView[0], q=True, ni=True)
        if numImages > 0:

            if int(pm.about(version=True)) < 2014:
                currentTextureImage = pm.textureWindow(self.uvTextureView[0], q=True, imageNumber=True)
                imageList = pm.textureWindow(self.uvTextureView[0], q=True, imageNames=True)
                currentTextureString = imageList[currentTextureImage].split('|')
                currentTextureNode = currentTextureString[len(currentTextureString) - 1].strip()
                if pm.nodeType(currentTextureNode) == 'file':
                    textureDimensions = pm.getAttr(currentTextureNode + '.outSize')
            else:
                textureDimensions = pm.textureWindow(self.uvTextureView[0], q=True, imageSize=True)

        return textureDimensions

    def uvSnapshot(self, name, xr, yr, aa, *args, **kwargs):
        ''' takes a snapshot image from the UV Editor in TGA format '''
        try:
            pm.uvSnapshot(name=name, xr=xr, yr=yr, overwrite=True, aa=aa, fileFormat='tga')
        except:
            lcUtility.Utility.lc_print_exception('Could not take UV snapshot, do you have geo selected?')

    def getTextureList(self, *args, **kwargs):
        '''
            returns a list of file texture nodes currently loaded in the UV Editor
            list items are formatted: [texture number, texture node]
            texture number is the index associated with the texture in the UV Editor
            texture node is the name of the maya file texture node
            SHADING GROUPS ARE EXCLUDED FROM THIS LIST

        '''
        texList = []
        numImages = pm.textureWindow(self.uvTextureView[0], q=True, ni=True)
        if numImages > 0:
            imageList = pm.textureWindow(self.uvTextureView[0], q=True, imageNames=True)

            for i in range(0, numImages):
                shadString = imageList[i].split('|')
                shadNode = shadString[len(shadString) - 1].strip()
                if pm.nodeType(shadNode) == 'file':
                    texList.append([i, shadNode])

        return texList
