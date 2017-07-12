"""
Copyright (C) 2017 Bricks Brought to Life
http://bblanimation.com/
chris@bblanimation.com

Created by Christopher Gearhart

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# system imports
import bpy
import bmesh
import math
from copy import copy, deepcopy
from .crossSection import slices, drawBMesh
from .common_mesh_generate import *
from .common_functions import *
from .binvox_rw import *
from ..classes.Brick import Bricks
from mathutils import Matrix, Vector, geometry
from mathutils.bvhtree import BVHTree
props = bpy.props

def confirmList(objList):
    """ if single object passed, convert to list """
    if type(objList) != list:
        objList = [objList]
    return objList

def bounds(obj, local=False):

    local_coords = obj.bound_box[:]
    om = obj.matrix_world

    if not local:
        worldify = lambda p: om * Vector(p[:])
        coords = [worldify(p).to_tuple() for p in local_coords]
    else:
        coords = [p[:] for p in local_coords]

    rotated = zip(*coords[::-1])

    push_axis = []
    for (axis, _list) in zip('xyz', rotated):
        info = lambda: None
        info.max = max(_list)
        info.min = min(_list)
        info.mid = (info.min + info.max) / 2
        info.distance = info.max - info.min
        push_axis.append(info)

    import collections

    originals = dict(zip(['x', 'y', 'z'], push_axis))

    o_details = collections.namedtuple('object_details', 'x y z')
    return o_details(**originals)

def addItemToCMList(name="New Model"):
    scn = bpy.context.scene
    item = scn.cmlist.add()
    item.id = len(scn.cmlist)
    scn.cmlist_index = (len(scn.cmlist)-1)
    if bpy.context.active_object == None:
        item.source_name = ""
    else:
        item.source_name = bpy.context.active_object.name # assign name of selected object
    item.name = name
    return True

def importLogo():
    """ import logo object from legoizer addon folder """
    addonsPath = bpy.utils.user_resource('SCRIPTS', "addons")
    legoizer = props.addon_name
    logoObjPath = "%(addonsPath)s/%(legoizer)s/lego_logo.obj" % locals()
    bpy.ops.import_scene.obj(filepath=logoObjPath)
    logoObj = bpy.context.selected_objects[0]
    return logoObj

def merge(bricks):
    return

# R = resolution, s = 3D scale tuple, o = offset lattice center from origin
def generateLattice(R, s, o=(0,0,0)):
    # TODO: Raise exception if R is less than 2
    bme = bmesh.new()
    # initialize variables
    coordMatrix = []
    xR = R[0]
    yR = R[1]
    zR = R[2]
    xS = s[0]
    yS = s[1]
    zS = s[2]
    xL = int(round((xS)/xR))+1
    if xL != 1: xL += 1
    yL = int(round((yS)/yR))+1
    if yL != 1: yL += 1
    zL = int(round((zS)/zR))+1
    if zL != 1: zL += 1
    # iterate through x,y,z dimensions and create verts/connect with edges
    for x in range(xL):
        coordList1 = []
        xCO = (x-(xS/(2*xR)))*xR
        for y in range(yL):
            coordList2 = []
            yCO = (y-(yS/(2*yR)))*yR
            for z in range(zL):
                # create verts
                zCO = (z-(zS/(2*zR)))*zR
                p = (xCO, yCO, zCO)
                v = bme.verts.new(tupleAdd(p, o))
                coordList2.append(v.co.copy())
            coordList1.append(coordList2)
        coordMatrix.append(coordList1)
    # return bmesh
    return coordMatrix

def rayIntersectsObj(point,direction,edgeLen,ob):
    """ returns True if ray intersects obj """
    _,location,normal,index = ob.ray_cast(point,direction,distance=edgeLen*1.00000000001)
    if index == -1:
        return False
    else:
        return True

def getBrickMatrix(source, coordMatrix, axes="xyz"):
    brickFreqMatrix = [[[0 for _ in range(len(coordMatrix[0][0]))] for _ in range(len(coordMatrix[0]))] for _ in range(len(coordMatrix))]
    # convert source to bmesh and convert faces to tri's
    sourceBM = bmesh.new()
    sourceBM.from_mesh(source.data)
    bmesh.ops.triangulate(sourceBM, faces=sourceBM.faces)

    bm = bmesh.new()
    axes = axes.lower()
    if "x" in axes:
        for z in range(len(coordMatrix[0][0])):
            for y in range(len(coordMatrix[0])):
                inside = 0
                for x in range(len(coordMatrix)):
                    orig = coordMatrix[x][y][z]
                    nextVerts = []
                    try:
                        rayEnd = coordMatrix[x+1][y][z]
                    except:
                        continue
                    # check if point can be thrown away
                    edgeLen = (orig - rayEnd).length
                    rayX = rayEnd[0] - orig[0]
                    rayY = rayEnd[1] - orig[1]
                    rayZ = rayEnd[2] - orig[2]
                    ray = Vector((rayX, rayY, rayZ))

                    if rayIntersectsObj(orig,ray,edgeLen,source):
                        for f in sourceBM.faces:
                            v1 = f.verts[0].co.copy()
                            v2 = f.verts[1].co.copy()
                            v3 = f.verts[2].co.copy()
                            pointOfIntersection = geometry.intersect_ray_tri(v1, v2, v3, ray, orig)
                            if pointOfIntersection:
                                if (orig - pointOfIntersection).length <= edgeLen:
                                    inside += 1
                                    bm.verts.new(pointOfIntersection)
                                    brickFreqMatrix[x][y][z] = 2
                                    brickFreqMatrix[x+1][y][z] = 2
                            elif inside % 2 == 1 and brickFreqMatrix[x][y][z] == 0:
                                brickFreqMatrix[x][y][z] = 1
                    else:
                        if inside % 2 == 1:
                            brickFreqMatrix[x][y][z] = 1
    if "y" in axes:
        for z in range(len(coordMatrix[0][0])):
            for x in range(len(coordMatrix)):
                inside = 0
                for y in range(len(coordMatrix[0])):
                    orig = coordMatrix[x][y][z]
                    nextVerts = []
                    try:
                        rayEnd = coordMatrix[x][y+1][z]
                    except:
                        continue
                    edgeLen = (orig - rayEnd).length
                    rayX = rayEnd[0] - orig[0]
                    rayY = rayEnd[1] - orig[1]
                    rayZ = rayEnd[2] - orig[2]
                    ray = Vector((rayX, rayY, rayZ))

                    if rayIntersectsObj(orig,ray,edgeLen,source):
                        for f in sourceBM.faces:
                            v1 = f.verts[0].co.copy()
                            v2 = f.verts[1].co.copy()
                            v3 = f.verts[2].co.copy()
                            pointOfIntersection = geometry.intersect_ray_tri(v1, v2, v3, ray, orig)
                            if pointOfIntersection:
                                if (orig - pointOfIntersection).length <= edgeLen:
                                    inside += 1
                                    bm.verts.new(pointOfIntersection)
                                    brickFreqMatrix[x][y][z] = 2
                                    brickFreqMatrix[x][y+1][z] = 2
                            elif inside % 2 == 1 and brickFreqMatrix[x][y][z] == 0:
                                brickFreqMatrix[x][y][z] = 1
                    else:
                        if inside % 2 == 1:
                            brickFreqMatrix[x][y][z] = 1
    if "z" in axes:
        for x in range(len(coordMatrix)):
            for y in range(len(coordMatrix[0])):
                inside = 0
                for z in range(len(coordMatrix[0][0])):
                    orig = coordMatrix[x][y][z]
                    nextVerts = []
                    try:
                        rayEnd = coordMatrix[x][y][z+1]
                    except:
                        continue
                    edgeLen = (orig - rayEnd).length
                    rayX = rayEnd[0] - orig[0]
                    rayY = rayEnd[1] - orig[1]
                    rayZ = rayEnd[2] - orig[2]
                    ray = Vector((rayX, rayY, rayZ))

                    if rayIntersectsObj(orig,ray,edgeLen,source):
                        for f in sourceBM.faces:
                            v1 = f.verts[0].co.copy()
                            v2 = f.verts[1].co.copy()
                            v3 = f.verts[2].co.copy()
                            pointOfIntersection = geometry.intersect_ray_tri(v1, v2, v3, ray, orig)
                            if pointOfIntersection:
                                if (orig - pointOfIntersection).length <= edgeLen:
                                    inside += 1
                                    bm.verts.new(pointOfIntersection)
                                    brickFreqMatrix[x][y][z] = 2
                                    brickFreqMatrix[x][y][z+1] = 2
                            elif inside % 2 == 1 and brickFreqMatrix[x][y][z] == 0:
                                brickFreqMatrix[x][y][z] = 1
                    else:
                        if inside % 2 == 1:
                            brickFreqMatrix[x][y][z] = 1
    for x in range(len(coordMatrix)):
        for y in range(len(coordMatrix[0])):
            for z in range(len(coordMatrix[0][0])):
                if brickFreqMatrix[x][y][z] == 1:
                    if (((brickFreqMatrix[x][y][z+1] == 0 or brickFreqMatrix[x][y][z-1] == 0) and "z" not in axes) or
                        ((brickFreqMatrix[x][y+1][z] == 0 or brickFreqMatrix[x][y-1][z] == 0) and "y" not in axes) or
                        ((brickFreqMatrix[x+1][y][z] == 0 or brickFreqMatrix[x-1][y][z] == 0) and "x" not in axes)):
                        brickFreqMatrix[x][y][z] = 1.5
    # drawBMesh(bm)
    return brickFreqMatrix

def getCOList(brickFreqMatrix, coordMatrix, threshold):
    coList = [[[-1 for _ in range(len(coordMatrix[0][0]))] for _ in range(len(coordMatrix[0]))] for _ in range(len(coordMatrix))]
    for x in range(len(coordMatrix)):
        for y in range(len(coordMatrix[0])):
            for z in range(len(coordMatrix[0][0])):
                if brickFreqMatrix[x][y][z] > threshold:
                    coList[x][y][z] = coordMatrix[x][y][z]
    return coList

def uniquify3DMatrix(matrix):
    for i in range(len(matrix)):
        for j in range(len(matrix[i])):
            matrix[i][j] = uniquify(matrix[i][j], lambda x: (round(x[0], 2), round(x[1], 2), round(x[2], 2)))
    return matrix

def makeBricks(refBricks, source, source_details, dimensions, R, preHollow=False):
    """ Make bricks """
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    # initialize temporary object
    tempMesh = bpy.data.meshes.new('tempM')
    tempObj = bpy.data.objects.new('temp', tempMesh)
    # set refBricks
    refBrickHidden = refBricks[0]
    refBrickUpper = refBricks[1]
    refBrickLower = refBricks[2]
    refBrickUpperLower = refBricks[3]

    # get lattice bmesh
    lScale = (source_details.x.distance, source_details.y.distance, source_details.z.distance)
    offset = (source_details.x.mid, source_details.y.mid, source_details.z.mid)
    coordMatrix = generateLattice(R, lScale, offset)
    coordMatrixLast = deepcopy(coordMatrix)
    # drawBMesh(makeLattice(R, lScale, offset))
    brickFreqMatrix = getBrickMatrix(source, coordMatrix, axes=cm.calculationAxes)
    # b = bmesh.new()
    # for x in range(len(coordMatrix)):
    #     for y in range(len(coordMatrix[x])):
    #         for z in range(len(coordMatrix[x][y])):
    #             if brickFreqMatrix[x][y][z] == 1:
    #                 b.verts.new(coordMatrix[x][y][z])
    # drawBMesh(b)

    # get coordinate list from intersections of edges with faces
    if not cm.preHollow:
        threshold = 0
    elif cm.shellThickness == 1:
        threshold = 1
    else:
        threshold = 0
    coList = getCOList(brickFreqMatrix, coordMatrix, threshold)

    # create group for lego bricks
    n = cm.source_name
    LEGOizer_bricks = 'LEGOizer_%(n)s_bricks' % locals()
    if groupExists(LEGOizer_bricks):
        bpy.data.groups.remove(group=bpy.data.groups[LEGOizer_bricks], do_unlink=True)
    bGroup = bpy.data.groups.new(LEGOizer_bricks)

    # if no coords in coList, add a coord at center of source
    if len(coList) == 0:
        coList.append((source_details.x.mid, source_details.y.mid, source_details.z.mid))

    # make bricks at determined locations
    bricks = Bricks()
    i = 0
    # TODO: Improve efficiency of the following nested for loop
    for x in range(len(coList)):
        print("x: " + str(x))
        for y in range(len(coList[0])):
            for z in range(len(coList[0][0])):
                co = coList[x][y][z]
                if co != -1:
                    i += 1
                    brick = bricks.new(name='LEGOizer_%(n)s_brick_%(i)s' % locals(), location=Vector(co))
                    if (z == 0 or brickFreqMatrix[x][y][z-1] != 0) and (z == len(coList[0][0])-1 or brickFreqMatrix[x][y][z+1] != 0):
                        brick.update_data(refBrickHidden.data)
                    elif (z == 0 or brickFreqMatrix[x][y][z-1] != 0) and (z == len(coList[0][0])-1 or brickFreqMatrix[x][y][z+1] == 0):
                        brick.update_data(refBrickUpper.data)
                    elif (z == 0 or brickFreqMatrix[x][y][z-1] == 0) and (z == len(coList[0][0])-1 or brickFreqMatrix[x][y][z+1] != 0):
                        brick.update_data(refBrickLower.data)
                    elif (z == 0 or brickFreqMatrix[x][y][z-1] == 0) and (z == len(coList[0][0])-1 or brickFreqMatrix[x][y][z+1] == 0):
                        brick.update_data(refBrickUpperLower.data)
                    elif z == len(coList[0][0])-1:
                        if brickFreqMatrix[x][y][z+1] == 0:
                            brickFreqMatrix[x][y][z] == 1

                    brick.link_to_scene(scn)
                    bGroup.objects.link(brick.obj)

    select(bricks.getAllObjs())

    scn.update()

    # return list of created Brick objects
    return bricks
