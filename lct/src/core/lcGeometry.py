import os
import re

import pymel.core as pm

import lct.src.core.lcColor as lcColor
import lct.src.core.lcUtility as lcUtility


class Obj(object):
    '''
    working with Wavefront .obj files
    handles only subset of file spec
    '''

    def __init__(self, objGeo=None, objPath='', verbose=True, notation='[1 of 1]', *args, **kwargs):
        """Loads a Wavefront OBJ file. """
        # containers for file contents
        self.comments = []
        self.v = []
        self.vt = []
        self.vn = []
        self.f = []
        self.mrgb = []
        self.g = []
        self.remainder = []
        # helpers and args
        self.verbose = verbose
        self.notation = notation
        self.objGeo = objGeo
        self.objPath = objPath
        self.objName = os.path.basename(objPath)

        # if you pass a list, such as the selection list, only grab the first xform element
        # also applies to newly created geo - maya preselects the primative creation node
        if isinstance(self.objGeo, list):
            for item in self.objGeo:
                if isinstance(item, pm.nt.Transform):
                    self.objGeo = item
                    break
            lcUtility.Utility.lc_print('You supplied a list. Making only first Xform element: {0}'.format(self.objGeo),
                                       mode='warning')

        # decide how to load based on given parameters
        if self.objPath and self.objGeo is None:
            self.get_data_file()
        elif self.objGeo is not None:
            self.get_data_geo()
        else:
            lcUtility.Utility.lc_print('not loading anything')

    def flush(self, *args, **kwargs):
        '''
        reset the OBJ class object
        '''
        self.comments = []
        self.v = []
        self.vt = []
        self.vn = []
        self.f = []
        self.mrgb = []
        self.g = []
        self.remainder = []

    def get_data_file(self, *args, **kwargs):
        '''
        get obj data from an obj file
        '''
        if self.objPath:
            # add path exists check
            if os.path.splitext(self.objName)[1].lower() == '.obj':
                if self.verbose:
                    lcUtility.Utility.lc_print('{} loading: {}'.format(self.notation, self.objPath))
                    pm.refresh()
                for i, line in enumerate(open(self.objPath, "r")):
                    if line.startswith('#') and not line.startswith('#MRGB'):
                        self.comments.append(line.rstrip('\n'))
                    elif line.split(' ')[0] == 'v':
                        values = line.split()
                        if values:
                            self.v.append(map(float, values[1:4]))
                    elif line.startswith('#MRGB'):
                        # zbrush mrgb notation is MMRRGGBB for each vert stacked in lines of up to 64
                        line = line[6:]  # remove '#MRGB ' from begining of line
                        self.mrgb.extend(re.findall('........', line))
                    elif line.startswith('g'):
                        self.g.append(line.split()[1])
                    else:
                        # if not 'g default' in line:
                        self.remainder.append(line.rstrip('\n'))
        else:
            lcUtility.Utility.lc_print('obj path not set')

    def get_data_geo(self, *args, **kwargs):
        '''
        get obj data from a maya geometry object
        '''
        try:
            # if the mesh is selected jump up to the transform
            if self.objGeo.nodeType() == 'mesh':
                self.objGeo = Geometry.getTransformsFromShapes({self.objGeo})[0]
            # if the selected transform is connected to a mesh, proceed
            if self.objGeo.getShape().nodeType() == 'mesh':
                # create vertex list
                for v in self.objGeo.verts:
                    self.v.append(v.getPosition(space='world'))
                    # create vertex color list
                    self.mrgb.append(lcColor.color.rgba_to_hex(v.getColor()))

                    # create uv list

                    # create vertex normals list

                # set group from obj name
                self.g.append(self.objGeo)  # .name().encode('ascii','replace'))
                # create face winding list
                for f in self.objGeo.faces:
                    lcUtility.Utility.lc_print('{} connected: {}'.format(f, f.connectedVertices()))

                lcUtility.Utility.lc_print(self.comments)
                lcUtility.Utility.lc_print(self.v)
                lcUtility.Utility.lc_print(self.vt)
                lcUtility.Utility.lc_print(self.vn)
                lcUtility.Utility.lc_print(self.f)
                lcUtility.Utility.lc_print(self.mrgb)
                lcUtility.Utility.lc_print(self.g)
                lcUtility.Utility.lc_print(self.remainder)

        except:
            lcUtility.Utility.lc_print_exception()(
                'Something went wrong loading this object, is it geometry? {0}'.format(self.objGeo))

    def to_string(self, *args, **kwargs):
        ''' '''
        string = None
        vData = []  # hold vertex data for export
        cData = ['#MRGB ']  # hold vertex color for export
        self.comments = ['# Exported by lct tool lcGeometry.py']

        if self.v:
            # prepare vertex data###############################
            i = 0
            trigger = 0
            for i in range(len(self.v)):
                if self.verbose:
                    prog = float(i) / len(self.v)
                    prog = int(100 * prog)
                    if prog >= trigger:
                        trigger = prog + 10
                        lcUtility.Utility.lc_print(
                            '{} digesting vertex: {} {}%'.format(self.notation, self.objName, int(prog)))
                        pm.refresh()
                # begin a vertex line notation
                line = 'v'
                for item in self.v[i]:
                    line = '{} {}'.format(line, item)
                vData.append(line)

        if self.mrgb:
            # prepare vertex color data###############################
            i = 0
            j = 0
            trigger = 0
            for i in range(len(self.mrgb)):
                if self.verbose:
                    prog = float(i) / len(self.mrgb)
                    prog = 100 * prog
                    if prog >= trigger:
                        trigger = prog + 10
                        lcUtility.Utility.lc_print(
                            '{} digesting  color: {} {}%'.format(self.notation, self.objName, int(prog)))
                        pm.refresh()
                # generate a 64 color line
                if i % 64 == 0 and not i == 0:
                    cData.append('#MRGB ')
                    j = j + 1
                cData[j] = cData[j] + self.mrgb[i]

        if vData:
            # build string
            string = '\n'.join(map(str, self.comments + ['', 'g default'] + vData + cData + self.remainder + ['']))

        if self.verbose:
            lcUtility.Utility.lc_print('{} complete: {} 100%'.format(self.notation, self.objName))
            pm.refresh()

        return string

    # temporary ****
    def edit_verts(self, offset, *args, **kwargs):
        ''' '''
        for i in range(len(self.v)):
            coord = self.v[i]
            coord = [x + y for x, y in zip(coord, offset)]
            self.v[i] = coord

    def translate(self, offset, *args, **kwargs):
        '''
        translate a obj mesh based on an offset
        '''
        for i in range(len(self.v)):
            coord = self.v[i]
            coord = [x + y for x, y in zip(coord, offset)]
            self.v[i] = coord

    def write(self, outputFile, *args, **kwargs):
        ''' '''
        contents = self.to_string()

        if self.verbose:
            lcUtility.Utility.lc_print('{} output: {}'.format(self.notation, outputFile))

        f = open(outputFile, 'w')
        f.write(contents)
        f.close()

    def import_maya(self, useVertexColor=False, *args, **kwargs):
        '''
        import obj into maya and apply vertex colors if available
        '''
        imported = pm.importFile(self.objPath, type='OBJ', options='mo=0', returnNewNodes=True)
        for item in imported:
            if pm.nodeType(item) == 'transform':
                imported = item
                break
        if useVertexColor:
            imported.setColors(self.mrgb)
            imported.updateSurface()
            # zipped = zip(imported.vtx, self.mrgb)
            # for item in zipped:
            #     #lcUtility.Utility.lc_print('{} - {}'.format(item[0], lcColor.color.hex_to_rgba(item[1]) ) )
            #     item[0].setColor(lcColor.color.hex_to_rgba(item[1]) )
            #     # item[0].setColor((0,0,1,1))
            # # lcUtility.Utility.lc_print(zipped)

            # # trigger=0
            # # for i in range(len(imported.vtx)):
            # #     if self.verbose:
            # #         prog = float(i)/len(imported.vtx)
            # #         prog = int(100*prog)
            # #         if prog>=trigger:
            # #             trigger = prog+10
            # #             lcUtility.Utility.lc_print('applying color: {}%'.format(int(prog) ) )
            # #     imported.vtx[i].setColor(lcColor.color.hex_to_rgba(self.mrgb[i]))
            # #     pm.refresh()

        imported.setDisplayColors(True)
        return imported

    def export_maya(self, *args, **kwargs):
        '''
        maya python obj exporter with vertex color support
        '''

    def export_selected_maya(self, obj, name, path, *args, **kwargs):
        '''
        export hacked
        '''
        exportString = os.path.normpath(os.path.join(path, str(name + '.obj')))
        print exportString
        exported = pm.exportSelected(exportString, force=True,
                                     options='groups=1;ptgroups=1;materials=0;smoothing=1;normals=1', type='OBJexport',
                                     pr=True, es=True)

        # self.objPath = exportString
        # self.get_data_file()

        for v in obj.vtx:
            self.mrgb.append(lcColor.color.rgba_to_hex(v.getColor()))
            # print lcColor.color.rgba_to_hex(v.getColor() )

        print self.mrgb

        self.write(exportString)


class Geometry(object):
    ''' '''

    def __init__(self, *args, **kwargs):
        ''' '''

    @classmethod
    def getAllGeometry(cls, *args, **kwargs):
        ''' '''
        # meshFilter = pm.itemFilter(byType='mesh')
        # allGeometry = pm.lsThroughFilter(meshFilter)

        return cls.filterForGeometry(pm.ls(tr=True))

    @classmethod
    def getTransformsFromShapes(cls, shapes, *args, **kwargs):
        ''' '''
        if not isinstance(shapes, list):
            shapes = {shapes}
        return [pm.PyNode(shape).getParent() for shape in shapes]

    @classmethod
    def getVertsFromSelection(cls, sel, *args, **kwargs):
        ''' retains current selection, returns vert list flattented '''
        verts = pm.polyListComponentConversion(sel, tv=True)
        # pm.select(verts, r=True)
        # outVerts = pm.ls(sl=True, flatten=True)

        # pm.select(sel, r=True)
        outVerts = pm.filterExpand(verts, sm=31, ex=True)

        return outVerts

    @classmethod
    def getMeshSelectionType(cls, mesh, *args, **kwargs):
        ''' '''
        if mesh.nodeType() == 'mesh':
            componentType = mesh.split('.')[1].split('[')[0]
            return componentType
        else:
            return 'mesh'

    @classmethod
    def switchSelectType(cls, type, *args, **kwargs):
        ''' '''
        if type == 'mesh':
            pm.selectMode(object=True)
        if type == 'vtx':
            pm.selectType(ocm=True, alc=False)
            pm.selectType(ocm=True, polymeshVertex=True)
        if type == 'e':
            pm.selectMode(component=True)
            pm.selectType(ocm=True, alc=False)
            pm.selectType(ocm=True, polymeshEdge=True)
        if type == 'f':
            pm.selectType(ocm=True, alc=False)
            pm.selectType(ocm=True, polymeshFace=True)

    @classmethod
    def filterForGeometry(cls, sel, *args, **kwargs):
        ''' filter the list for only geometry '''
        # This has problems, only works for selections from the viewport, as in things with transforms
        if not isinstance(sel, list):
            sel = {sel}
        try:
            return [obj for obj in sel if obj.getShape() and obj.getShape().nodeType() == 'mesh']
        except:
            return None

    @classmethod
    def checkMultipleShapes(cls, transform, *args, **kwargs):
        ''' '''
        shapes = pm.listRelatives(transform, fullPath=True, shapes=True)
        if len(shapes) > 1:
            return None
        else:
            return shapes[0]

    @classmethod
    def fixNamespaceNames(cls, *args, **kwargs):
        ''' '''
        sel = pm.ls(sl=True)
        if sel:
            for obj in sel:
                nameSplit = obj.split(':')
                if len(nameSplit) > 1:
                    pm.rename(sel, nameSplit[-1])

    @classmethod
    def relaxVerts(cls, verts, mesh, progBarList=None, *args, **kwargs):
        ''' '''
        if verts:
            pm.polyAverageVertex(verts, i=1)
            cls.shrinkWrap(verts, mesh, progBarList)
        else:
            pm.warning('No verts selected')

    @classmethod
    def shrinkWrap(cls, verts, mesh, progBarList=None, *args, **kwargs):
        ''' '''
        # print'mesh: {}'.format(mesh)
        currentUnit = pm.currentUnit(query=True, linear=True)

        for bar in progBarList:
            pm.progressBar(bar, edit=True, endProgress=True)
            pm.progressBar(bar, edit=True, beginProgress=True, isInterruptable=True, maxValue=len(verts), en=True,
                           status='Running . . .')

        if mesh:
            # closestNode = pm.createNode('closestPointOnMesh')
            # pm.connectAttr(mesh.worldMesh[0], closestNode.inMesh)
            # pm.connectAttr(mesh.worldMatrix[0], closestNode.inputMatrix)

            pm.currentUnit(linear='cm')
            for vert in verts:
                vert = pm.PyNode(vert)

                if pm.progressBar(progBarList[0], query=True, isCancelled=True):
                    for bar in progBarList:
                        pm.progressBar(bar, edit=True, en=False)
                    break
                else:
                    # print 'vert: {}'.format(vert)
                    # vertPos = pm.pointPosition(vert, w=True)
                    vertPos = vert.getPosition(space='world')
                    # print 'vertPos: {}'.format(vertPos)
                    # closestNode.inPosition.set(vertPos)
                    # meshPos = closestNode.position.get()
                    meshPos = mesh.getClosestPoint(vertPos, space='world')[0]
                    # print 'meshPos: {}'.format(meshPos)

                    vert.setPosition(meshPos, space='world')
                    # pm.move(vert, meshPos, ws=True)
                    # vertPos2 = pm.pointPosition(vert, w=True)
                    # print 'vertPos2: {}'.format(vertPos2)

                    for bar in progBarList:
                        pm.progressBar(bar, edit=True, step=1)

            pm.currentUnit(linear=currentUnit)
            # pm.delete(closestNode)
            for bar in progBarList:
                pm.progressBar(bar, edit=True, en=False)
                pm.progressBar(bar, edit=True, endProgress=True)
        else:
            pm.warning('No verts selected')

    @classmethod
    def merge_and_weld(cls, polyList=None, *args, **kwargs):
        '''
        merge and weld items from a list, or if empty selection
        '''
        if not polyList:
            polyList = pm.ls(sl=True)
        if len(polyList) > 1:
            merged = pm.PyNode(pm.polyUnite(polyList)[0])
            pm.polyMergeVertex(merged, distance=0.001)
            pm.delete(merged, constructionHistory=True)
        else:
            lcUtility.Utility.lc_print('Select 2 or more polygon objects', mode='warning')

    @classmethod
    def unlock_attrs(cls, transforms, attrList, *args, **kwargs):
        '''
        accepts transforms as a list or singly
        unlocks the given list of attrs if they are found
        '''
        if not isinstance(transforms, list):
            transforms = {transforms}  # make a one item list from the single item input

        for transform in transforms:
            if transform.nodeType() == 'transform':
                attrs = transform.listAttr()

                for attr in attrs:
                    if attr.split('.')[1] in attrList:
                        try:
                            if attr.get(lock=True) == True:
                                attr.set(lock=False)
                        except:
                            lcUtility.Utility.lc_print("Could not unlock {0}".format(attr))
            else:
                lcUtility.Utility.lc_print("{0} is not a transform".format(transform))

    @classmethod
    def unlock_translate_rotate_scale(cls, transform, *args, **kwargs):
        ''' '''
        attrList = {'translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ', 'scaleX', 'scaleY',
                    'scaleZ'}
        cls.unlock_attrs(transform, attrList)


class UV(object):
    def __init__(self, aspect=[1, 1]):
        """ """
        self.aspect = aspect

    @classmethod
    def grabShell(cls, *args, **kwargs):
        ''' from a selection of UV's selects the shell '''
        pm.polySelectConstraint(type=0x0010, shell=True, border=False, mode=2)  # select the uv shell
        pm.polySelectConstraint(shell=False, border=False, mode=0)  # reset the selection constraint

    def move(self, uvw, *args, **kwargs):
        ''' moves a selection of uv's '''
        pm.polyEditUV(uValue=uvw[0], vValue=uvw[1])

    def moveShell(self, uvw, *args, **kwargs):
        ''' moves the shell of a selection of uv's '''
        pm.polyEditUVShell(uValue=uvw[0], vValue=uvw[1])

    def rotate(self, angle, pivot, aspect, *args, **kwargs):
        scaleDownU = float(aspect[0]) / float(aspect[1])
        scaleUpU = float(aspect[1]) / float(aspect[0])
        pm.polyEditUV(pivotU=pivot[0], pivotV=pivot[1], r=False, scaleU=scaleDownU)
        pm.polyEditUV(pivotU=pivot[0], pivotV=pivot[1], a=angle)
        pm.polyEditUV(pivotU=pivot[0], pivotV=pivot[1], r=False, scaleU=scaleUpU)

    def rotateShell(self, angle, pivot, aspect, *args, **kwargs):
        scaleDownU = float(aspect[0]) / float(aspect[1])
        scaleUpU = float(aspect[1]) / float(aspect[0])
        pm.polyEditUVShell(pivotU=pivot[0], pivotV=pivot[1], r=False, scaleU=scaleDownU)
        pm.polyEditUVShell(pivotU=pivot[0], pivotV=pivot[1], a=angle)
        pm.polyEditUVShell(pivotU=pivot[0], pivotV=pivot[1], r=False, scaleU=scaleUpU)

    def scale(self, uv, pivot, *args, **kwargs):
        pm.polyEditUV(pivotU=pivot[0], pivotV=pivot[1], scaleU=uv[0], scaleV=uv[1])

    def scaleShell(self, uv, pivot, *args, **kwargs):
        pm.polyEditUVShell(pivotU=pivot[0], pivotV=pivot[1], scaleU=uv[0], scaleV=uv[1])

    def getBoundingBoxCenter(self, shell=False, *args, **kwargs):
        """Get the center point of the UV's bounding box"""
        if shell:
            self.grabShell()
        uvBB = pm.polyEvaluate(boundingBoxComponent2d=True)
        uvCenter = [((uvBB[0][1] + uvBB[0][0]) / 2), ((uvBB[1][1] + uvBB[1][0]) / 2)]
        return uvCenter

    # def getBoundingBoxCenterShell(self, *args, **kwargs):
    #   """Get the center point of the UV shell's bounding box"""
    #   self.grabShell()
    #   uvBB = pm.polyEvaluate(boundingBoxComponent2d=True)
    #   uvCenter=[((uvBB[0][1]+uvBB[0][0])/2),((uvBB[1][1]+uvBB[1][0])/2)]
    #   return uvCenter

    @classmethod
    def getUVSets(cls, *args, **kwargs):
        """ """
        return pm.polyUVSet(query=True, allUVSets=True)

    @classmethod
    def removeExtraSets(cls, obj, *args, **kwargs):
        """ remove all uv sets except for the default one """
        for i in pm.polyUVSet(obj, query=True, allUVSetsIndices=True)[1:]:
            name = pm.getAttr(obj + '.uvSet[' + str(i) + '].uvSetName')
            pm.polyUVSet(obj, delete=True, uvSet=name)
