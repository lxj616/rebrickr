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
import time
from copy import copy, deepcopy
from .common_functions import *
from .generate_lattice import generateLattice
from .makeBricks import *
from ..classes.Brick import Bricks
from mathutils import Matrix, Vector, geometry
from mathutils.bvhtree import BVHTree
props = bpy.props

def modalRunning():
    try:
        if bpy.context.window_manager["modal_running"] == True:
            return True
    except:
        pass
    return False

def listModalRunning():
    try:
        if bpy.context.window_manager["list_modal_running"] == True:
            return True
    except:
        pass
    return False

def getSafeScn():
    safeScn = bpy.data.scenes.get("LEGOizer_storage")
    if safeScn == None:
        safeScn = bpy.data.scenes.new("LEGOizer_storage")
    return safeScn
def safeUnlink(obj):
    scn = bpy.context.scene
    safeScn = getSafeScn()
    scn.objects.unlink(obj)
    safeScn.objects.link(obj)
def safeLink(obj):
    scn = bpy.context.scene
    safeScn = getSafeScn()
    scn.objects.link(obj)
    try:
        safeScn.objects.unlink(obj)
    except:
        pass

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

def importLogo():
    """ import logo object from legoizer addon folder """
    addonsPath = bpy.utils.user_resource('SCRIPTS', "addons")
    legoizer = props.addon_name
    logoObjPath = "%(addonsPath)s/%(legoizer)s/lego_logo.obj" % locals()
    bpy.ops.import_scene.obj(filepath=logoObjPath)
    logoObj = bpy.context.selected_objects[0]
    return logoObj

def rayObjIntersections(point,direction,edgeLen,ob):
    """ returns True if ray intersects obj """
    # initialize variables
    intersections = 0
    nextIntersection = None
    edgeIntersects = False
    outside = False
    orig = point
    doubleCheckDirection = -direction
    # run initial intersection check
    while True:
        _,location,normal,index = ob.ray_cast(orig,direction)#distance=edgeLen*1.00000000001)
        if index == -1: break
        if intersections == 0:
            if (location-orig).length <= edgeLen*1.00001:
                edgeIntersects = True
        elif intersections == 1:
            nextIntersection = location.copy()
        intersections += 1
        orig = location + direction*0.00001
    if intersections%2 == 0:
        outside = True
    # double check vert is inside mesh
    count = 0
    orig = point
    while True:
        _,location,normal,index = ob.ray_cast(orig,doubleCheckDirection)#distance=edgeLen*1.00000000001)
        if index == -1: break
        count += 1
        orig = location + doubleCheckDirection*0.00001
    if count%2 == 0:
        outside = True
    # return helpful information
    return not outside, edgeIntersects, intersections, nextIntersection, index

def updateBFMatrix(x0, y0, z0, coordMatrix, brickFreqMatrix, brickShell, source, x1, y1, z1, inside=None):
    orig = coordMatrix[x0][y0][z0]
    try:
        rayEnd = coordMatrix[x1][y1][z1]
    except:
        return -1, None
    # check if point can be thrown away
    ray = rayEnd - orig
    edgeLen = ray.length

    origInside, edgeIntersects, intersections, nextIntersection, index = rayObjIntersections(orig,ray,edgeLen,source)

    if origInside:
        if brickFreqMatrix[x0][y0][z0] == 0:
            brickFreqMatrix[x0][y0][z0] = -1
    if edgeIntersects:
        if (origInside and brickShell == "Inside Mesh") or (not origInside and brickShell == "Outside Mesh") or brickShell == "Inside and Outside":
            brickFreqMatrix[x0][y0][z0] = 2
        if (not origInside and brickShell == "Inside Mesh") or (origInside and brickShell == "Outside Mesh") or brickShell == "Inside and Outside":
            brickFreqMatrix[x1][y1][z1] = 2
    # elif not origInside:
    #     brickFreqMatrix[x0][y0][z0] = 0

    return intersections, nextIntersection

# TODO: Make this more efficient
def getBrickMatrix(source, coordMatrix, brickShell, axes="xyz"):
    ct = time.time()
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    brickFreqMatrix = [[[0 for _ in range(len(coordMatrix[0][0]))] for _ in range(len(coordMatrix[0]))] for _ in range(len(coordMatrix))]
    # convert source to bmesh and convert faces to tri's
    sourceBM = bmesh.new()
    sourceBM.from_mesh(source.data)
    bmesh.ops.triangulate(sourceBM, faces=sourceBM.faces)

    axes = axes.lower()
    stopWatch("2a", time.time()-ct)
    ct = time.time()
    breakNextTime = True
    if "x" in axes:
        for z in range(len(coordMatrix[0][0])):
            for y in range(len(coordMatrix[0])):
                for x in range(len(coordMatrix)):
                    if x != 0:
                        if not breakNextTime and nextIntersection and nextIntersection[0] < coordMatrix[x][y][z][0]:
                            continue
                    intersections, nextIntersection = updateBFMatrix(x, y, z, coordMatrix, brickFreqMatrix, brickShell, source, x+1, y, z)
                    if intersections == 0:
                        break
    stopWatch("2b", time.time()-ct)
    ct = time.time()
    if "y" in axes:
        for z in range(len(coordMatrix[0][0])):
            for x in range(len(coordMatrix)):
                for y in range(len(coordMatrix[0])):
                    if y != 0:
                        if not breakNextTime and nextIntersection and nextIntersection[1] < coordMatrix[x][y][z][1]:
                            continue
                    intersections, nextIntersection = updateBFMatrix(x, y, z, coordMatrix, brickFreqMatrix, brickShell, source, x, y+1, z)
                    if intersections == 0:
                        break
    stopWatch("2c", time.time()-ct)
    ct = time.time()
    if "z" in axes:
        for x in range(len(coordMatrix)):
            for y in range(len(coordMatrix[0])):
                for z in range(len(coordMatrix[0][0])):
                    if z != 0:
                        if not breakNextTime and nextIntersection and nextIntersection[2] < coordMatrix[x][y][z][2]:
                            continue
                    intersections, nextIntersection = updateBFMatrix(x, y, z, coordMatrix, brickFreqMatrix, brickShell, source, x, y, z+1)
                    if intersections == 0:
                        break
    stopWatch("2d", time.time()-ct)
    ct = time.time()
    for x in range(len(coordMatrix)):
        for y in range(len(coordMatrix[0])):
            for z in range(len(coordMatrix[0][0])):
                if brickFreqMatrix[x][y][z] == -1:
                    if ((((z == len(coordMatrix[0][0])-1 or brickFreqMatrix[x][y][z+1] == 0) or (z == 0 or brickFreqMatrix[x][y][z-1] == 0)) and "z" not in axes) or
                        (((y == len(coordMatrix[0])-1 or brickFreqMatrix[x][y+1][z] == 0) or (y == 0 or brickFreqMatrix[x][y-1][z] == 0)) and "y" not in axes) or
                        (((x == len(coordMatrix)-1 or brickFreqMatrix[x+1][y][z] == 0) or (x == 0 or brickFreqMatrix[x-1][y][z] == 0)) and "x" not in axes)):
                        brickFreqMatrix[x][y][z] = 2
    stopWatch("2e", time.time()-ct)
    ct = time.time()
    j = 1
    for idx in range(100):
        j = round(j-0.01, 2)
        gotOne = False
        for x in range(len(coordMatrix)):
            for y in range(len(coordMatrix[0])):
                for z in range(len(coordMatrix[0][0])):
                    if brickFreqMatrix[x][y][z] == -1:
                        try:
                            if ((j == 0.99 and
                               (brickFreqMatrix[x+1][y][z] == 2 or
                               brickFreqMatrix[x-1][y][z] == 2 or
                               brickFreqMatrix[x][y+1][z] == 2 or
                               brickFreqMatrix[x][y-1][z] == 2 or
                               brickFreqMatrix[x][y][z+1] == 2 or
                               brickFreqMatrix[x][y][z-1] == 2)) or
                               (brickFreqMatrix[x+1][y][z] == round(j + 0.01,2) or
                               brickFreqMatrix[x-1][y][z] == round(j + 0.01,2) or
                               brickFreqMatrix[x][y+1][z] == round(j + 0.01,2) or
                               brickFreqMatrix[x][y-1][z] == round(j + 0.01,2) or
                               brickFreqMatrix[x][y][z+1] == round(j + 0.01,2) or
                               brickFreqMatrix[x][y][z-1] == round(j + 0.01,2))):
                                brickFreqMatrix[x][y][z] = j
                                gotOne = True
                        except:
                            pass
        if not gotOne:
            break

    # Draw supports
    if cm.internalSupports == "Columns":
        print(brickFreqMatrix[len(coordMatrix)//2][len(coordMatrix[0])//2])
        for x in range(cm.colStep + cm.colThickness, len(coordMatrix), cm.colStep + cm.colThickness):
            for y in range(cm.colStep + cm.colThickness, len(coordMatrix[0]), cm.colStep + cm.colThickness):
                for z in range(0, len(coordMatrix[0][0])):
                    for j in range(cm.colThickness):
                        for k in range(cm.colThickness):
                            if brickFreqMatrix[x-j][y-k][z] > 0 and brickFreqMatrix[x-j][y-k][z] < 1:
                                brickFreqMatrix[x-j][y-k][z] = 1.5
    elif cm.internalSupports == "Lattice":
        if cm.alternateXY:
            alt = 0
        else:
            alt = 0.5
        for z in range(0, len(coordMatrix[0][0])):
            alt += 1
            for x in range(0, len(coordMatrix)):
                for y in range(0, len(coordMatrix[0])):
                    if x % cm.latticeStep != 0 or alt % 2 == 1:
                        if y % cm.latticeStep != 0 or alt % 2 == 0:
                            continue
                    if brickFreqMatrix[x][y][z] > 0 and brickFreqMatrix[x][y][z] < 1:
                        brickFreqMatrix[x][y][z] = 1.5

    # bm = bmesh.new()
    # for x in range(len(coordMatrix)):
    #     for y in range(len(coordMatrix[0])):
    #         for z in range(len(coordMatrix[0][0])):
    #             if brickFreqMatrix[x][y][z] > 1:
    #                 bm.verts.new(coordMatrix[x][y][z])
    # drawBMesh(bm)
    stopWatch("2f", time.time()-ct)
    ct = time.time()
    return brickFreqMatrix

def getCOList(brickFreqMatrix, coordMatrix, threshold):
    coList = [[[-1 for _ in range(len(coordMatrix[0][0]))] for _ in range(len(coordMatrix[0]))] for _ in range(len(coordMatrix))]
    for x in range(len(coordMatrix)):
        for y in range(len(coordMatrix[0])):
            for z in range(len(coordMatrix[0][0])):
                if brickFreqMatrix[x][y][z] >= threshold:
                    coList[x][y][z] = coordMatrix[x][y][z]
    return coList

def uniquify3DMatrix(matrix):
    for i in range(len(matrix)):
        for j in range(len(matrix[i])):
            matrix[i][j] = uniquify(matrix[i][j], lambda x: (round(x[0], 2), round(x[1], 2), round(x[2], 2)))
    return matrix

def makeBricksDict(source, source_details, dimensions, R):
    """ Make bricks """
    ct = time.time()
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    # get lattice bmesh
    print("generating blueprint...")
    lScale = (source_details.x.distance, source_details.y.distance, source_details.z.distance)
    offset = (source_details.x.mid, source_details.y.mid, source_details.z.mid)
    if cm.brickType == "Custom":
        R = (R[0] * cm.distOffsetX, R[1] * cm.distOffsetY, R[2] * cm.distOffsetZ)
    coordMatrix = generateLattice(R, lScale, offset)
    # drawBMesh(makeLattice(R, lScale, offset))
    if cm.brickShell != "Inside Mesh":
        calculationAxes = cm.calculationAxes
    else:
        calculationAxes = "XYZ"

    brickFreqMatrix = getBrickMatrix(source, coordMatrix, cm.brickShell, axes=calculationAxes)
    # get coordinate list from intersections of edges with faces
    threshold = 1.01 - (cm.shellThickness / 100)

    coList = getCOList(brickFreqMatrix, coordMatrix, threshold)
    # if no coords in coList, add a coord at center of source
    if len(coList) == 0:
        coList.append((source_details.x.mid, source_details.y.mid, source_details.z.mid))

    # create bricks dictionary with brickFreqMatrix values
    bricks = []
    i = 0
    brickDict = {}
    for x in range(len(coList)):
        for y in range(len(coList[0])):
            for z in range(len(coList[0][0])):
                co = coList[x][y][z]
                if co != -1:
                    i += 1
                    n = cm.source_name
                    j = str(i+1)
                    brickDict[str(x) + "," + str(y) + "," + str(z)] = {
                        "name":'LEGOizer_%(n)s_brick_%(j)s' % locals(),
                        "val":brickFreqMatrix[x][y][z],
                        "co":(co[0]-source_details.x.mid, co[1]-source_details.y.mid, co[2]-source_details.z.mid),
                        "connected":False}
                else:
                    brickDict[str(x) + "," + str(y) + "," + str(z)] = {
                        "name":"DNE",
                        "val":brickFreqMatrix[x][y][z],
                        "co":None,
                        "connected":False}


    stopWatch("Time Elapsed (generating blueprint)", time.time()-ct)

    # return list of created Brick objects
    return brickDict
