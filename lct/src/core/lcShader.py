import pymel.core as pm
import os

import lct.src.core.lcUtility as lcUtility


class ShaderNode(object):
    ''' '''

    def __init__(self, shaderName, kind='lambert', *args, **kwargs):
        ''' '''
        self.shaderName = shaderName
        self.kind = kind
        self.shader = None
        self.shadingGroup = None
        self.shaderFile = None

    def update(self, *args, **kwargs):
        ''' update self '''
        try:
            self.shader = pm.PyNode(self.shaderName)
            self.shadingGroup = self.shaderName + 'SG'
            self.shaderFile = self.shader.shader
        except:
            self.create()
            self.setShaderFile(self.shaderFile)

    def reset(self, *args, **kwargs):
        ''' update self '''
        try:
            pm.delete(self.shaderName)
            self.create()
        except:
            self.create()

    def create(self, *args, **kwargs):
        ''' make the shader  '''

        if not pm.objExists(self.shaderName):
            self.shader = pm.shadingNode(self.kind, asShader=True, name=self.shaderName)
            self.shadingGroup = self.shaderName + 'SG'
            if not pm.objExists(self.shadingGroup):
                self.shadingGroup = pm.sets(renderable=True, noSurfaceShader=True, empty=True,
                                            name=(self.shaderName + 'SG'))
            pm.connectAttr(self.shader + '.outColor', self.shadingGroup + '.surfaceShader', force=True)
        else:
            self.shader = pm.PyNode(self.shaderName)
            self.shadingGroup = pm.PyNode(self.shaderName + 'SG')

    def assign(self, objs, *args, **kwargs):
        ''' assign the shader to the list '''

        try:
            shadingGroup = pm.connectionInfo(self.shader.outColor, dfs=True)
            shadingGroup = shadingGroup[0].split('.')[0]

            if objs:
                for obj in objs:
                    pm.select(obj, r=True)
                    pm.sets(shadingGroup, edit=True, forceElement=True)
                pm.select(clear=True)

        except:
            pm.warning('This Shader has no Shading Group')

    def setShaderFile(self, shaderFile, *args, **kwargs):
        ''' assign the shader file to realtime shader '''
        realtimeShaderTypes = ['cgfxShader', 'hlslShader', 'dx11Shader', 'GLSLShader']
        self.shaderFile = shaderFile

        if self.kind in realtimeShaderTypes:
            self.shader.shader.set(self.shaderFile)
        else:
            lcUtility.Utility.lc_print('You can only set a shader file on cgfx, hlsl, dx11, or GLSL shaders',
                                       mode='warning')

    def setFileTexture(self, texAttr, texPath, texName='texture', *args, **kwargs):
        ''' link a file texture node to the specified attribute '''
        texName = texAttr
        if os.path.exists(texPath):
            if pm.objExists(texName):
                fileNode = pm.PyNode(texName)
            else:
                fileNode = pm.createNode('file', name=texName)

            if self.shader.hasAttr(texAttr) and not self.shader.attr(texAttr).isConnected():
                fileNode.fileTextureName.set(texPath)
                fileNode.outColor.connect(self.shader.attr(texAttr))

    def openAttributeEditor(self, *args, **kwargs):
        ''' open the shaders attribute editor '''
        pm.mel.showEditor(self.shader)


class Shader(object):
    """
        make and work with shaders in general

    """

    def __init__(self, *args, **kwargs):
        """ """

    @classmethod
    def intelligentRepath(cls, shaderList, rootPath):
        ''' '''
        try:
            shader_list = []
            found_list = []
            walk_list = []
            if shaderList:
                if os.path.exists(rootPath):
                    for root, dirs, files in os.walk(rootPath):
                        for file in files:
                            walk_list.append([root, file])

                    for shader in shaderList:
                        old_path = shader.shader.get()
                        if old_path:
                            shader_name = os.path.basename(old_path)
                            shader_list.append((shader, shader_name))

                    for shader_obj in shader_list:
                        for file_obj in walk_list:
                            if shader_obj[1] == file_obj[1]:
                                # Found the shader
                                shader_path = os.path.join(file_obj[0], file_obj[1])
                                try:
                                    lcUtility.Utility.lc_print("FOUND: {} at {}".format(file_obj[1], shader_path))
                                    # Link to new path
                                    shader_obj[0].shader.set(shader_path)
                                except:
                                    lcUtility.Utility.lc_print(
                                        "Could not set Shader on {} to {}".format(shader_obj[0], shader_path))
                                finally:
                                    found_list.append(shader_obj)

                    shader_list = [x for x in shader_list if x not in found_list]

                    if shader_list:
                        shader_string = ""
                        for shader_obj in shader_list:
                            shader_string = shader_string + "Shader: {}, {}\n".format(shader_obj[0], shader_obj[1])
                        lcUtility.Utility.lc_print(
                            "Some shaders not found at new path\nPath: {}\n{}".format(rootPath, shader_string),
                            mode='warning')
                else:
                    lcUtility.Utility.lc_print("{} is not a valid path".format(rootPath), mode='error')
            else:
                lcUtility.Utility.lc_print("No shaders passed to function", mode='error')
        except:
            lcUtility.Utility.lc_print_exception("Problem repathing shader list")

    @classmethod
    def intelligentRepathAll(cls, rootPath):
        ''' '''
        try:
            # rootPath = os.path.normpath(rootPath.encode('string-escape'));
            if os.path.exists(rootPath):
                shaderList = pm.ls(exactType='dx11Shader')
                cls.intelligentRepath(shaderList, rootPath)
            else:
                lcUtility.Utility.lc_print("{} is not a valid path".format(rootPath), mode='error')

        except:
            lcUtility.Utility.lc_print_exception("Problem repathing all shaders")

    @classmethod
    def assignShader(cls, shader, objs, *args, **kwargs):
        ''' assign the shader to the list '''
        shadingGroup = pm.connectionInfo(shader.outColor, dfs=True)
        try:
            shadingGroup = shadingGroup[0].split('.')[0]
        except:
            pm.warning('This Shader has no Shading Group')

        if objs:
            for obj in objs:
                pm.select(obj, r=True)
                pm.sets(shadingGroup, edit=True, forceElement=True)
            pm.select(clear=True)

    @classmethod
    def filterForShaders(cls, objs, kindList=['dx11Shader']):
        ''' '''
        filtered_list = []
        for item in objs:
            try:
                if pm.nodeType(item) in kindList:
                    filtered_list.append(item)
            except:
                lcUtility.Utility.lc_print("pm.nodeType({}) failed!".format(item))
        return filtered_list

# class CGFX():
#     """
#         make and work with cgfx shaders

#     """
#     def __init__(self, *args, **kwargs):
#         """ """

#     @classmethod
#     def toggleLinear(cls,toggle, *args, **kwargs):
#         """ switch all cgfx shaders to linear shading mode """
#         cgfx=pm.ls(exactType='cgfxShader')
#         for obj in cgfx:
#             pm.setAttr(obj.linear, toggle)# will error if this attr '.linear' is not available

#     @classmethod
#     def switchToTechnique(cls,technique, *args, **kwargs):
#         """ switch all cgfx shaders to the specified technique """
#         cgfx=pm.ls(exactType='cgfxShader')
#         for obj in cgfx:
#             pm.setAttr(obj.technique, technique, type='string')# will error if this attr '.technique' is not available

#     @classmethod
#     def getAllShaders(cls, *args, **kwargs):
#         """ return a list of all the cgfx shaders in the scene """
#         return pm.ls(type='cgfxShader')

#     @classmethod
#     def connectVector(cls, plug, src, *args, **kwargs):
#         """ runs the connectVector method from this mel script cgfxShader_util.mel; installed with Maya """
#         pm.mel.cgfxShader_connectVector(plug, src)

#     @classmethod
#     def revertToLambert(cls, shader, textureSampler='.diffuseMapSampler', *args, **kwargs):
#         """ create lambert copies of all the cgfx shaders and connect the diffuse texture """
#         if pm.getAttr(shader+'.shader'):
#             diffuseTexNode = pm.connectionInfo(shader+textureSampler, sourceFromDestination=True)
#             lambert = pm.shadingNode('lambert', asShader=True, name='L_'+shader )
#             lambertSG = pm.sets(renderable=True, noSurfaceShader=True, empty=True, name='L_'+shader+'SG' )
#             pm.connectAttr(lambert+'.outColor', lambertSG+'.surfaceShader', force=True)
#             if diffuseTexNode:
#                 pm.connectAttr(diffuseTexNode, lambert+'.color', force=True)

#             pm.hyperShade(objects=shader)
#             pm.sets(lambertSG, edit=True, forceElement=True)
#             pm.select(clear=True)

#     @classmethod
#     def reloadShader(cls, shader, *args, **kwargs):
#         """ reload the cgfx shader file """
#         cgfxFile = pm.getAttr(shader+'.shader')
#         if cgfxFile:
#             pm.cgfxShader(shader, edit=True, fx=cgfxFile)

#     @classmethod
#     def repathShader(cls, shader, newPath, *args, **kwargs):
#         """ reload the shader from a new path """
#         cgfxFile = pm.getAttr(shader+'.shader')
#         if cgfxFile:
#             pm.cgfxShader(shader, edit=True, fx=lcPath.Path.repath(cgfxFile, newPath) )

#     @classmethod
#     def createShader(cls, name, path, *args, **kwargs):
#         """
#             'name' is the name you want to give the shader
#             'path' is the filepath with .cgfx file

#         """
#         lcPlugin.Plugin.reloadPlugin('cgfxShader', True)

#         shaderCGFX = pm.shadingNode('cgfxShader', asShader=True, name=name+'_CGFX_01' )
#         SG = pm.sets(renderable=True, noSurfaceShader=True, empty=True, name=(shaderCGFX+'_SG') )
#         pm.connectAttr(shaderCGFX.outColor, SG.surfaceShader, force=True)

#         pm.cgfxShader(shaderCGFX, edit=True, fx=path) #this will fail if the cgfxShader plugin is not loaded

#         return shaderCGFX

#     @classmethod
#     def createShaderLambert(cls, name, path, *args, **kwargs):
#         """
#             name is the name you want to give the shader
#             path is the filepath with .cgfx file

#         """
#         lcPlugin.Plugin.reloadPlugin('cgfxShader', True)

#         shaderBase = pm.shadingNode('lambert', asShader=True, name=name+'_01')
#         shaderBase.color.set(0.5, 0.0, 1.0)
#         shaderCGFX = pm.shadingNode('cgfxShader', asShader=True, name=name+'_CGFX_01' )
#         SG = pm.sets(renderable=True, noSurfaceShader=True, empty=True, name=(shaderBase+'_SG') )
#         pm.connectAttr(shaderBase.outColor, SG.surfaceShader, force=True)
#         pm.connectAttr(shaderCGFX.outColor, shaderBase.hardwareShader, force=True)

#         pm.cgfxShader(shaderCGFX, edit=True, fx=path) #this will fail if the cgfxShader plugin is not loaded

#         return shaderBase

#     @classmethod
#     def buildShaderList(cls, sourcePath, *args, **kwargs):
#         """
#             return a list of all the cgfx files from a directory by name type
#             ex. dir has:
#                         lcWalkable_2.1.cgfx
#                         lcComicShader_1.5.cgfx
#                         lcLiveShader_4.4.cgfx
#                     return:
#                         [lcWalkable, lcComicShader, lcLiveShader]

#         """
#         shaderFiles = [shaderFile for shaderFile in os.listdir(sourcePath) if shaderFile.lower().endswith(".cgfx")]
#         shaderList = []

#         for fileName in shaderFiles:
#             fileName = fileName.split('_')
#             baseName = fileName[0]
#             if baseName not in shaderList:
#                 shaderList.append(baseName)

#         return shaderList

#     @classmethod
#     def getLatestVersion(cls, sourcePath, baseName, *args, **kwargs):
#         """
#             if there are multiple versions of the same shader file, pick the highest version number
#             ex. lcLiveShader_4.6.cgfx

#         """
#         shaderFiles = [shaderFile for shaderFile in os.listdir(sourcePath) if shaderFile.lower().endswith(".cgfx")]

#         oldest = 00
#         age = -1
#         latest = ''

#         for fname in shaderFiles:
#             if baseName in fname:
#                 splitName = fname.split('_')
#                 version = splitName[1].split('.')
#                 age = version[0]+version[1]
#                 if age > oldest:
#                     oldest = age
#                     latest = splitName[0]+'_'+version[0]+'.'+version[1]+'.cgfx'
#         return latest

# class HLSL:
#     """ """

#     def __init__(self, *args, **kwargs):
#         """ """

#     @classmethod
#     def getAllShaders(cls, *args, **kwargs):
#         """ return a list of all the hlsl shaders in the scene """
#         return pm.ls(type='hlslShader')

#     @classmethod
#     def reloadShader(cls, shader, *args, **kwargs):
#         """ reload the shader """
#         hlslFile = shader.shader.get()
#         shader.shader.set(hlslFile)
#         print '# hlslShader :  \"{0}\" loaded effect \"{1}\" #'.format(shader, hlslFile)

#     @classmethod
#     def createShader(cls, name, path, *args, **kwargs):
#         """
#             name is the name you want to give the shader
#             path is the filepath with .fx file

#         """
#         lcPlugin.Plugin.reloadPlugin('hlslShader', True)

#         shaderHLSL = pm.shadingNode('hlslShader', asShader=True, name=name+'_HLSL_01' )
#         SG = pm.sets(renderable=True, noSurfaceShader=True, empty=True, name=(shaderHLSL+'_SG') )
#         pm.connectAttr(shaderHLSL.outColor, SG.surfaceShader, force=True)
#         shaderHLSL.shader.set(path)
#         print '# hlslShader :  \"{0}\" loaded effect \"{1}\" #'.format(shaderHLSL, path)

#         return shaderHLSL

#     @classmethod
#     def createShaderLambert(cls, name, path, *args, **kwargs):
#         """
#             name is the name you want to give the shader
#             path is the filepath with .fx file

#         """
#         lcPlugin.Plugin.reloadPlugin('hlslShader', True)

#         shaderBase = pm.shadingNode('lambert', asShader=True, name=name+'_01')
#         shaderBase.color.set(0.0, 0.5, 1.0)
#         shaderHLSL = pm.shadingNode('hlslShader', asShader=True, name=name+'_HLSL_01' )
#         SG = pm.sets(renderable=True, noSurfaceShader=True, empty=True, name=(shaderBase+'_SG') )
#         pm.connectAttr(shaderBase.outColor, SG.surfaceShader, force=True)
#         pm.connectAttr(shaderHLSL.outColor, shaderBase.hardwareShader, force=True)
#         shaderHLSL.shader.set(path)
#         print '# hlslShader :  \"{0}\" loaded effect \"{1}\" #'.format(shaderHLSL, path)

#         return shaderBase
