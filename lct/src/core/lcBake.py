import os
import pymel.core as pm

class Bake:

    def __init__(self, *args, **kwargs):
        """ Initialize class and variables """

    @classmethod
    def createBakeSet(cls, bakeSetName='mrBakeSet', type='texture', *args, **kwargs):
        ''' make a mental ray bake set and return the name '''
        #texture
        if type == 'texture':
            newBakeSet = pm.createNode('textureBakeSet', name='tex_'+bakeSetName)
            if pm.ls('textureBakePartition'):
                pm.partition(newBakeSet, add='textureBakePartition')
            else:
                pm.partition(newBakeSet, name='textureBakePartition')
        #vertex
        else:
            newBakeSet = pm.createNode('vertexBakeSet', name='vtx_'+bakeSetName)
            pm.mel.setFilterScript(newBakeSet)
            if pm.ls('vertexBakePartition'):
                pm.partition(newBakeSet, add='vertexBakePartition')
            else:
                pm.partition(newBakeSet, name='vertexBakePartition')

            pm.addAttr(newBakeSet, ln='filterSize', sn='fs', min=-1, dv=0.001)
            pm.addAttr(newBakeSet, ln='filterNormalTolerance', sn='fns', min=0, max=180, dv=5)

        return newBakeSet

    @classmethod
    def assignBakeSet(cls, objList, bakeSet, *args, **kwargs):
        ''' '''
        if objList:
            for obj in objList:
                #pm.set(obj, forceElement=bakeSet) #this does not seem to recognize the mental ray set as a true set
                pm.mel.assignBakeSet(bakeSet, obj)

    @classmethod
    def convertLightmap(cls, bakeSet, camera, dir, shadows, *args, **kwargs):
        ''' '''
        convertString = ''

        if shadows == True:
            shadowsSwitch = ' -sh'
        else:
            shadowsSwitch = ''

        pm.select(bakeSet)
        bakeObjs = pm.ls(selection=True)
        if bakeObjs:
            if (pm.nodeType(bakeSet) == 'textureBakeSet'):

                lightMapDir = os.path.normpath(os.path.join(dir, 'lightMap'))
                if not os.path.exists(lightMapDir):
                    os.makedirs(lightMapDir)
                if os.name == 'nt':
                    dir = dir.replace('\\','/')
                fileSwitch = ' -project "'+dir+'"'

                convertString = 'convertLightmap -camera '+camera+shadowsSwitch+fileSwitch
            else:
                convertString = 'convertLightmap -vm -camera '+camera+shadowsSwitch+' -bo '+bakeSet+' '

            for obj in bakeObjs:
                pm.select(obj)
                fullPath = pm.ls(selection=True, long=True)
                shadingGroup = pm.listConnections(obj, destination=True, source=False, plugs=False, type='shadingEngine')
                try:
                    convertString += ' '+shadingGroup[0]+' '+fullPath[0]
                except:
                    pm.warning('Your bake set contains geometry without shading groups, graph the connections and check or remove this item: {0} (there may be more than one)'.format(obj))

            try:
                pm.mel.eval(convertString)
            except:
                pm.warning('Something went wrong or you canceled')

        return convertString
