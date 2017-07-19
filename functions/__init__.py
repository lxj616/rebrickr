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

def pointInsideMesh(point,ob):
    axes = [ Vector((1,0,0)) , Vector((0,1,0)), Vector((0,0,1))  ]
    outside = False
    for axis in axes:
        orig = point
        count = 0
        while True:
            _,location,normal,index = ob.ray_cast(orig,orig+axis*10000.0)
            if index == -1: break
            count += 1
            orig = location + axis*0.00001
        if count%2 == 0:
            outside = True
            break
    return not outside

def rayObjIntersections(point,direction,edgeLen,ob):
    """ returns True if ray intersects obj """
    intersections = 0
    orig = point
    while True:
        _,location,normal,index = ob.ray_cast(orig,direction,distance=edgeLen*1.00000000001)
        if index == -1: break
        intersections += 1
        orig = location + direction*0.00001
    return intersections

def updateBFMatrix(x0, y0, z0, coordMatrix, brickFreqMatrix, source, x1, y1, z1, inside=None):
    orig = coordMatrix[x0][y0][z0]
    try:
        rayEnd = coordMatrix[x1][y1][z1]
    except:
        return
    # check if point can be thrown away
    edgeLen = (orig - rayEnd).length
    rayX = rayEnd[0] - orig[0]
    rayY = rayEnd[1] - orig[1]
    rayZ = rayEnd[2] - orig[2]
    ray = Vector((rayX, rayY, rayZ))

    if pointInsideMesh(orig, source):
        if brickFreqMatrix[x0][y0][z0] == 0:
            brickFreqMatrix[x0][y0][z0] = -1
            brickFreqMatrix[x0][y0][z0] = -1
    intersections = rayObjIntersections(orig,ray,edgeLen,source)
    if intersections > 0:
        brickFreqMatrix[x0][y0][z0] = 2
        brickFreqMatrix[x1][y1][z1] = 2

def getBrickMatrix(source, coordMatrix, axes="xyz"):
    brickFreqMatrix = [[[0 for _ in range(len(coordMatrix[0][0]))] for _ in range(len(coordMatrix[0]))] for _ in range(len(coordMatrix))]
    # convert source to bmesh and convert faces to tri's
    sourceBM = bmesh.new()
    sourceBM.from_mesh(source.data)
    bmesh.ops.triangulate(sourceBM, faces=sourceBM.faces)

    axes = axes.lower()
    if "x" in axes:
        for z in range(len(coordMatrix[0][0])):
            for y in range(len(coordMatrix[0])):
                for x in range(len(coordMatrix)):
                    updateBFMatrix(x, y, z, coordMatrix, brickFreqMatrix, source, x+1, y, z)
    if "y" in axes:
        for z in range(len(coordMatrix[0][0])):
            for x in range(len(coordMatrix)):
                for y in range(len(coordMatrix[0])):
                    updateBFMatrix(x, y, z, coordMatrix, brickFreqMatrix, source, x, y+1, z)
    if "z" in axes:
        for x in range(len(coordMatrix)):
            for y in range(len(coordMatrix[0])):
                for z in range(len(coordMatrix[0][0])):
                    updateBFMatrix(x, y, z, coordMatrix, brickFreqMatrix, source, x, y, z+1)
    for x in range(len(coordMatrix)):
        for y in range(len(coordMatrix[0])):
            for z in range(len(coordMatrix[0][0])):
                if brickFreqMatrix[x][y][z] == -1:
                    if ((((z == len(coordMatrix[0][0])-1 or brickFreqMatrix[x][y][z+1] == 0) or (z == 0 or brickFreqMatrix[x][y][z-1] == 0)) and "z" not in axes) or
                        (((y == len(coordMatrix[0])-1 or brickFreqMatrix[x][y+1][z] == 0) or (y == 0 or brickFreqMatrix[x][y-1][z] == 0)) and "y" not in axes) or
                        (((x == len(coordMatrix)-1 or brickFreqMatrix[x+1][y][z] == 0) or (x == 0 or brickFreqMatrix[x-1][y][z] == 0)) and "x" not in axes)):
                        brickFreqMatrix[x][y][z] = 2
    j = 1
    for idx in range(100):
        j -= 0.01
        gotOne = False
        for x in range(len(coordMatrix)):
            for y in range(len(coordMatrix[0])):
                for z in range(len(coordMatrix[0][0])):
                    if brickFreqMatrix[x][y][z] == -1:
                        if (j == 0.99 and
                           (brickFreqMatrix[x+1][y][z] == 2 or
                           brickFreqMatrix[x-1][y][z] == 2 or
                           brickFreqMatrix[x][y+1][z] == 2 or
                           brickFreqMatrix[x][y-1][z] == 2 or
                           brickFreqMatrix[x][y][z+1] == 2 or
                           brickFreqMatrix[x][y][z-1] == 2) or
                           (brickFreqMatrix[x+1][y][z] == j + 0.01 or
                           brickFreqMatrix[x-1][y][z] == j + 0.01 or
                           brickFreqMatrix[x][y+1][z] == j + 0.01 or
                           brickFreqMatrix[x][y-1][z] == j + 0.01 or
                           brickFreqMatrix[x][y][z+1] == j + 0.01 or
                           brickFreqMatrix[x][y][z-1] == j + 0.01)):
                            brickFreqMatrix[x][y][z] = round(j, 2)
                            gotOne = True


        if not gotOne:
            break

    # bm = bmesh.new()
    # for x in range(len(coordMatrix)):
    #     for y in range(len(coordMatrix[0])):
    #         for z in range(len(coordMatrix[0][0])):
    #             if brickFreqMatrix[x][y][z] > 1:
    #                 bm.verts.new(coordMatrix[x][y][z])
    # drawBMesh(bm)
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

def makeBricksDict(source, source_details, dimensions, R, preHollow=False):
    """ Make bricks """
    ct = time.time()
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    # # set refBricks
    # refBrickHidden = refBricks[0]
    # refBrickUpper = refBricks[1]
    # refBrickLower = refBricks[2]
    # refBrickUpperLower = refBricks[3]
    # get lattice bmesh
    lScale = (source_details.x.distance, source_details.y.distance, source_details.z.distance)
    offset = (source_details.x.mid, source_details.y.mid, source_details.z.mid)
    coordMatrix = generateLattice(R, lScale, offset)
    # drawBMesh(makeLattice(R, lScale, offset))
    brickFreqMatrix = getBrickMatrix(source, coordMatrix, axes=cm.calculationAxes)
    # get coordinate list from intersections of edges with faces
    if not cm.preHollow:
        threshold = 0
    else:
        threshold = 1.01 - (cm.shellThickness / 100)
    coList = getCOList(brickFreqMatrix, coordMatrix, threshold)
    # if no coords in coList, add a coord at center of source
    if len(coList) == 0:
        coList.append((source_details.x.mid, source_details.y.mid, source_details.z.mid))
    # make bricks at determined locations
    bricks = []
    i = 0
    # TODO: Improve efficiency of the following nested for loop
    brickDict = {}
    denom = len(coList)/20
    for x in range(len(coList)):
        for y in range(len(coList[0])):
            for z in range(len(coList[0][0])):
                co = coList[x][y][z]
                if co != -1:
                    i += 1
                    # # brick = bricks.new(name='LEGOizer_%(n)s_brick_%(i)s' % locals(), location=Vector(co))
                    # if (z != 0 and brickFreqMatrix[x][y][z-1] != 0) and (z != len(coList[0][0])-1 and brickFreqMatrix[x][y][z+1] != 0):
                    #     brickMesh = refBrickHidden.data
                    #     # brick.update_data(refBrickHidden.data)
                    # elif (z != 0 and brickFreqMatrix[x][y][z-1] != 0) and (z == len(coList[0][0])-1 or brickFreqMatrix[x][y][z+1] == 0):
                    #     brickMesh = refBrickUpper.data
                    #     # brick.update_data(refBrickUpper.data)
                    # elif (z == 0 or brickFreqMatrix[x][y][z-1] == 0) and (z != len(coList[0][0])-1 and brickFreqMatrix[x][y][z+1] != 0):
                    #     brickMesh = refBrickLower.data
                    #     # brick.update_data(refBrickLower.data)
                    # elif (z == 0 or brickFreqMatrix[x][y][z-1] == 0) and (z == len(coList[0][0])-1 or brickFreqMatrix[x][y][z+1] == 0):
                    #     brickMesh = refBrickUpperLower.data
                    #     # brick.update_data(refBrickUpperLower.data)
                    # else:
                    #     print("shouldn't get here")
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
                        "co":co,
                        "connected":False}
        # print status to terminal
        if x % denom < 1:
            percent = x*100//len(coList)+5
            if percent > 100:
                percent = 100
            print("generating blueprint... " + str(percent) + "%")

    stopWatch("Time Elapsed (makeBricksDict)", time.time()-ct)

    # return list of created Brick objects
    return brickDict
