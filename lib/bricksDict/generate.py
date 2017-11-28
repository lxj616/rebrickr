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

# System imports
import bmesh
import math
import time

# Blender imports
import bpy
from bpy.types import Object
from mathutils import Matrix, Vector

# Rebrickr imports
from ...functions.common import *
from ...functions.general import *
from ...functions.generate_lattice import generateLattice
from ...functions.wrappers import *

def VectorRound(vec, dec, roundType="ROUND"):
    """ round all vals in Vector 'vec' to 'dec' precision using 'ROUND', 'FLOOR', or 'CEIL' """
    lst = []
    for i in range(len(vec)):
        if roundType == "ROUND":
            val = round(vec[i], dec)
        else:
            val = vec[i] * 10**dec
            if roundType == "FLOOR":
                val = math.floor(val)
            elif roundType in ["CEILING", "CEIL"]:
                val = math.ceil(val)
            val = val / 10**dec
        lst.append(val)
    return Vector(lst)

def castRays(obj, point, direction, miniDist, roundType="CEILING", edgeLen=0):
    # initialize variables
    firstDirection = False
    firstIntersection = None
    nextIntersection = None
    lastIntersection = None
    edgeIntersects = False
    edgeLen2 = edgeLen*1.00001
    orig = point
    intersections = 0
    origs = []
    # cast rays until no more rays to cast
    while True:
        _,location,normal,index = obj.ray_cast(orig,direction)#distance=edgeLen*1.00000000001)
        if index == -1: break
        if intersections == 0:
            firstDirection = direction.dot(normal)
        if edgeLen != 0:
            # get first and last intersection (used when getting materials of nearest (first or last intersected) face)
            if (location-point).length <= edgeLen2:
                if intersections == 0:
                    edgeIntersects = True
                    firstIntersection = {"idx":index, "dist":(location-point).length}
                lastIntersection = {"idx":index, "dist":edgeLen - (location-point).length}
            # set nextIntersection
            if intersections == 1:
                nextIntersection = location.copy()
        intersections += 1
        location = VectorRound(location, 5, roundType=roundType)
        orig = location + miniDist
        origs.append(orig)

    return intersections, firstDirection, firstIntersection, nextIntersection, lastIntersection, edgeIntersects

def rayObjIntersections(point, direction, miniDist:Vector, edgeLen, obj):
    """
    cast ray(s) from point in direction to determine insideness and whether edge intersects obj within edgeLen

    returned:
    - not outside       - 'point' is inside object 'obj'
    - edgeIntersects    - ray from 'point' in 'direction' of length 'edgeLen' intersects object 'obj'
    - intersections     - number of ray-obj intersections from 'point' in 'direction' to infinity
    - nextIntersection  - second ray intersection from 'point' in 'direction'
    - firstIntersection - dictionary containing 'idx':index of first intersection and 'distance:distance from point to first intersection within edgeLen
    - lastIntersection  - dictionary containing 'idx':index of last intersection and 'distance:distance from point to last intersection within edgeLen

    """

    # initialize variables
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    intersections = 0
    noMoreChecks = False
    outsideL = []
    # set axis of direction
    if direction[0] > 0:
        axes = "XYZ"
    elif direction[1] > 0:
        axes = "YZX"
    else:
        axes = "ZXY"
    # run initial intersection check
    intersections, firstDirection, firstIntersection, nextIntersection, lastIntersection, edgeIntersects = castRays(obj, point, direction, miniDist, edgeLen=edgeLen)
    if cm.insidenessRayCastDir == "High Efficiency" or axes[0] in cm.insidenessRayCastDir:
        outsideL.append(0)
        if intersections%2 == 0 and not (cm.useNormals and firstDirection > 0):
            outsideL[0] = 1
        elif cm.castDoubleCheckRays:
            # double check vert is inside mesh
            count, firstDirection,_,_,_,_ = castRays(obj, point, -direction, -miniDist, roundType="FLOOR")
            if count%2 == 0 and not (cm.useNormals and firstDirection > 0):
                outsideL[0] = 1

    # run more checks if verifyExposure is True
    if cm.insidenessRayCastDir != "High Efficiency":
        dir0 = Vector((direction[2], direction[0], direction[1]))
        dir1 = Vector((direction[1], direction[2], direction[0]))
        miniDist0 = Vector((miniDist[2], miniDist[0], miniDist[1]))
        miniDist1 = Vector((miniDist[1], miniDist[2], miniDist[0]))
        dirs = [[dir0, miniDist0], [dir1, miniDist1]]
        for i in range(2):
            if axes[i+1] in cm.insidenessRayCastDir:
                outsideL.append(0)
                direction = dirs[i][0]
                miniDist = dirs[i][1]
                count, firstDirection,_,_,_,_ = castRays(obj, point, direction, miniDist)
                if count%2 == 0 and not (cm.useNormals and firstDirection > 0):
                    outsideL[i] = 1
                elif cm.castDoubleCheckRays:
                    # double check vert is inside mesh
                    count, firstDirection,_,_,_,_ = castRays(obj, point, -direction, -miniDist, roundType="FLOOR")
                    if count%2 == 0 and not (cm.useNormals and firstDirection > 0):
                        outsideL[i] = 1

    # find average of outsideL and set outside accordingly (<0.5 is False, >=0.5 is True)
    outside = sum(outsideL)/len(outsideL) >= 0.5

    # return helpful information
    return not outside, edgeIntersects, intersections, nextIntersection, firstIntersection, lastIntersection

def updateBFMatrix(x0, y0, z0, coordMatrix, faceIdxMatrix, brickFreqMatrix, brickShell, source, x1, y1, z1, miniDist, inside=None):
    """ update brickFreqMatrix[x0][y0][z0] based on results from rayObjIntersections """
    orig = coordMatrix[x0][y0][z0]
    try:
        rayEnd = coordMatrix[x1][y1][z1]
    except IndexError:
        return -1, None
    # check if point can be thrown away
    ray = rayEnd - orig
    edgeLen = ray.length

    origInside, edgeIntersects, intersections, nextIntersection, firstIntersection, lastIntersection = rayObjIntersections(orig,ray,miniDist,edgeLen,source)

    if origInside:
        if brickFreqMatrix[x0][y0][z0] == 0:
            # define brick as inside shell
            brickFreqMatrix[x0][y0][z0] = -1
    if edgeIntersects:
        if (origInside and brickShell == "Inside Mesh") or (not origInside and brickShell == "Outside Mesh") or brickShell == "Inside and Outside":
            # define brick as part of shell
            brickFreqMatrix[x0][y0][z0] = 1
            # set or update nearest face to brick
            if type(faceIdxMatrix[x0][y0][z0]) != dict or faceIdxMatrix[x0][y0][z0]["dist"] > firstIntersection["dist"]:
                faceIdxMatrix[x0][y0][z0] = firstIntersection
        if (not origInside and brickShell == "Inside Mesh") or (origInside and brickShell == "Outside Mesh") or brickShell == "Inside and Outside":
            # define brick as part of shell
            brickFreqMatrix[x1][y1][z1] = 1
            # set or update nearest face to brick
            if type(faceIdxMatrix[x1][y1][z1]) != dict or faceIdxMatrix[x1][y1][z1]["dist"] > lastIntersection["dist"]:
                faceIdxMatrix[x1][y1][z1] = lastIntersection

    return intersections, nextIntersection

def setNF(matShellDepth, j, orig, target, faceIdxMatrix):
    """ match value in faceIdxMatrix of 'target' to 'orig' if within matShellDepth """
    if ((1-j)*100) < matShellDepth:
        faceIdxMatrix[target[0]][target[1]][target[2]] = faceIdxMatrix[orig[0]][orig[1]][orig[2]]

def isInternal(bricksDict, key):
    val = bricksDict[key]["val"]
    return (val > 0 and val < 1) or val == -1

def updateInternal(bricksDict, cm, keys="ALL", clearExisting=False):
    if keys == "ALL": keys = list(bricksDict.keys())
    # clear extisting internal structure
    if clearExisting:
        zStep = getZStep(cm)
        # set all bricks as unmerged
        Bricks.splitAll(bricksDict, keys=keys, cm=cm)
        # clear internal
        for key in keys:
            if isInternal(bricksDict, key):
                bricksDict[key]["draw"] = False
    # Draw column supports
    if cm.internalSupports == "Columns":
        step = cm.colStep + cm.colThickness
        for key in keys:
            x,y,z = strToList(key)
            if x % step in range(cm.colThickness):
                if y % step in range(cm.colThickness):
                    if isInternal(bricksDict, key):
                        bricksDict[key]["draw"] = True
    # draw lattice supports
    elif cm.internalSupports == "Lattice":
        step = cm.latticeStep
        for key in keys:
            x,y,z = strToList(key)
            if x % step == 0 and (not cm.alternateXY or z % 2 == 0):
                if isInternal(bricksDict, key):
                    bricksDict[key]["draw"] = True
            elif y % step == 0 and (not cm.alternateXY or z % 2 == 1):
                if isInternal(bricksDict, key):
                    bricksDict[key]["draw"] = True

def getBrickMatrix(source, faceIdxMatrix, coordMatrix, brickShell, axes="xyz", cursorStatus=False):
    """ returns new brickFreqMatrix """
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    brickFreqMatrix = [[[0 for _ in range(len(coordMatrix[0][0]))] for _ in range(len(coordMatrix[0]))] for _ in range(len(coordMatrix))]
    # convert source to bmesh and convert faces to tri's
    sourceBM = bmesh.new()
    sourceBM.from_mesh(source.data)
    bmesh.ops.triangulate(sourceBM, faces=sourceBM.faces)

    # initialize values used for printing status
    denom = (len(coordMatrix[0][0]) + len(coordMatrix[0]) + len(coordMatrix))/100
    if cursorStatus:
        wm = bpy.context.window_manager
        wm.progress_begin(0, 100)

    axes = axes.lower()
    ct = time.time()
    breakNextTime = True
    if "x" in axes:
        miniDist = Vector((0.00015, 0.0, 0.0))
        for z in range(len(coordMatrix[0][0])):
            # print status to terminal
            if not scn.Rebrickr_printTimes:
                percent0 = len(coordMatrix)/denom * (z/(len(coordMatrix[0][0])-1))
                if percent0 < 100:
                    update_progress("Shell", percent0/100.0)
                    if cursorStatus: wm.progress_update(percent0)
            for y in range(len(coordMatrix[0])):
                for x in range(len(coordMatrix)):
                    if x != 0:
                        if not breakNextTime and nextIntersection and nextIntersection[0] < coordMatrix[x][y][z][0]:
                            continue
                    intersections, nextIntersection = updateBFMatrix(x, y, z, coordMatrix, faceIdxMatrix, brickFreqMatrix, brickShell, source, x+1, y, z, miniDist)
                    if intersections == 0:
                        break
    else:
        percent0 = 0
    # print status to terminal
    if scn.Rebrickr_printTimes:
        stopWatch("X Axis", time.time()-ct)
        ct = time.time()

    if "y" in axes:
        miniDist = Vector((0.0, 0.00015, 0.0))
        for z in range(len(coordMatrix[0][0])):
            # print status to terminal
            if not scn.Rebrickr_printTimes:
                percent1 = percent0 + (len(coordMatrix[0])/denom * (z/(len(coordMatrix[0][0])-1)))
                if percent1 < 100:
                    update_progress("Shell", percent1/100.0)
                    if cursorStatus: wm.progress_update(percent1)
            for x in range(len(coordMatrix)):
                for y in range(len(coordMatrix[0])):
                    if y != 0:
                        if not breakNextTime and nextIntersection and nextIntersection[1] < coordMatrix[x][y][z][1]:
                            continue
                    intersections, nextIntersection = updateBFMatrix(x, y, z, coordMatrix, faceIdxMatrix, brickFreqMatrix, brickShell, source, x, y+1, z, miniDist)
                    if intersections == 0:
                        break
    else:
        percent1 = percent0
    # print status to terminal
    if scn.Rebrickr_printTimes:
        stopWatch("Y Axis", time.time()-ct)
        ct = time.time()

    if "z" in axes:
        miniDist = Vector((0.0, 0.0, 0.00015))
        for x in range(len(coordMatrix)):
            # print status to terminal
            if not scn.Rebrickr_printTimes:
                percent2 = percent1 + (len(coordMatrix[0][0])/denom * (x/(len(coordMatrix)-1)))
                if percent2 < 100:
                    update_progress("Shell", percent2/100.0)
                    if cursorStatus: wm.progress_update(percent2)
            for y in range(len(coordMatrix[0])):
                for z in range(len(coordMatrix[0][0])):
                    if z != 0:
                        if not breakNextTime and nextIntersection and nextIntersection[2] < coordMatrix[x][y][z][2]:
                            continue
                    intersections, nextIntersection = updateBFMatrix(x, y, z, coordMatrix, faceIdxMatrix, brickFreqMatrix, brickShell, source, x, y, z+1, miniDist)
                    if intersections == 0:
                        break
    # print status to terminal
    if scn.Rebrickr_printTimes:
        stopWatch("Z Axis", time.time()-ct)
        ct = time.time()

    # adjust brickFreqMatrix values
    for x in range(len(coordMatrix)):
        for y in range(len(coordMatrix[0])):
            for z in range(len(coordMatrix[0][0])):
                # if current location is inside (-1) and adjacent location is out of bounds, current location is shell (1)
                if (("z" not in axes and
                     (z in [0, len(coordMatrix[0][0])-1] or
                      brickFreqMatrix[x][y][z+1] == 0 or
                      brickFreqMatrix[x][y][z-1] == 0)) or
                    ("y" not in axes and
                     (y in [0, len(coordMatrix[0])-1] or
                      brickFreqMatrix[x][y+1][z] == 0 or
                      brickFreqMatrix[x][y-1][z] == 0)) or
                    ("x" not in axes and
                     (x in [0, len(coordMatrix)-1] or
                      brickFreqMatrix[x+1][y][z] == 0 or
                      brickFreqMatrix[x-1][y][z] == 0))):
                    if brickFreqMatrix[x][y][z] == -1:
                        brickFreqMatrix[x][y][z] = 1
                        # TODO: set faceIdxMatrix value to nearest shell value using some sort of built in nearest poly to point function
                    # break from current location, as boundary locs should not be verified
                    continue
                if cm.verifyExposure:
                    # If inside location (-1) intersects outside location (0), make it ouside (0)
                    if brickFreqMatrix[x][y][z] == -1:
                        if brickFreqMatrix[x+1][y][z] == 0 or brickFreqMatrix[x-1][y][z] == 0 or brickFreqMatrix[x][y+1][z] == 0 or brickFreqMatrix[x][y-1][z] == 0 or brickFreqMatrix[x][y][z+1] == 0 or brickFreqMatrix[x][y][z-1] == 0:
                            brickFreqMatrix[x][y][z] = 0
                    # If shell location (1) does not intersect outside location (0), make it inside (-1)
                    if brickFreqMatrix[x][y][z] == 1 and brickFreqMatrix[x+1][y][z] != 0 and brickFreqMatrix[x-1][y][z] != 0 and brickFreqMatrix[x][y+1][z] != 0 and brickFreqMatrix[x][y-1][z] != 0 and brickFreqMatrix[x][y][z+1] != 0 and brickFreqMatrix[x][y][z-1] != 0:
                        brickFreqMatrix[x][y][z] = -1

    # print status to terminal
    if not scn.Rebrickr_printTimes:
        update_progress("Shell", 1)
        if cursorStatus: wm.progress_end()

    # set up brickFreqMatrix values for bricks inside shell
    j = 1
    # NOTE: Following two lines are alternative for calculating partial brickFreqMatrix (insideness only calculated as deep as necessary)
    # denom = min([(cm.shellThickness-1), max(len(coordMatrix)-2, len(coordMatrix[0])-2, len(coordMatrix[0][0])-2)])/2
    # for idx in range(cm.shellThickness-1):
    # NOTE: Following two lines are alternative for calculating full brickFreqMatrix
    denom = max(len(coordMatrix)-2, len(coordMatrix[0])-2, len(coordMatrix[0][0])-2)/2
    for idx in range(100):
        # print status to terminal
        if not scn.Rebrickr_printTimes:
            percent = idx/denom
            if percent < 1:
                update_progress("Internal", percent**0.9)
        j = round(j-0.01, 2)
        gotOne = False
        for x in range(len(coordMatrix)):
            for y in range(len(coordMatrix[0])):
                for z in range(len(coordMatrix[0][0])):
                    if brickFreqMatrix[x][y][z] == -1:
                        try:
                            idxsToCheck = [(x+1, y, z),
                                           (x-1, y, z),
                                           (x, y+1, z),
                                           (x, y-1, z),
                                           (x, y, z+1),
                                           (x, y, z-1)]
                            for idxs in idxsToCheck:
                                if brickFreqMatrix[idxs[0]][idxs[1]][idxs[2]] == round(j + 0.01,2):
                                    brickFreqMatrix[x][y][z] = j
                                    setNF(cm.matShellDepth, j, idxs, (x,y,z), faceIdxMatrix)
                                    gotOne = True
                                    break
                        except Exception as e:
                            print(e)
                            pass
        if not gotOne:
            break

    # print status to terminal
    if scn.Rebrickr_printTimes:
        stopWatch("Internal", time.time()-ct)
        ct = time.time()
    update_progress("Internal", 1)

    # bm = bmesh.new()
    # for x in range(len(coordMatrix)):
    #     for y in range(len(coordMatrix[0])):
    #         for z in range(len(coordMatrix[0][0])):
    #             if brickFreqMatrix[x][y][z] > 1:
    #                 bm.verts.new(coordMatrix[x][y][z])
    # drawBMesh(bm)

    # print status to terminal
    if scn.Rebrickr_printTimes:
        stopWatch("Supports", time.time()-ct)
        ct = time.time()

    return brickFreqMatrix

def getThreshold(cm):
    """ returns threshold (draw bricks if val >= threshold) """
    return 1.01 - (cm.shellThickness / 100)

def createBricksDictEntry(name, val=0, draw=False, co=(0,0,0), nearest_face=None, mat_name=None, parent_brick=None, size=None, attempted_merge=False, top_exposed=None, bot_exposed=None, type=None):
    return {"name":name,
            "val":val,
            "draw":draw,
            "co":co,
            "nearest_face":nearest_face,
            "mat_name":mat_name,
            "parent_brick":parent_brick,
            "size":size,
            "attempted_merge":attempted_merge,
            "top_exposed":top_exposed,
            "bot_exposed":bot_exposed,
            "type":type}

@timed_call('Time Elapsed')
def makeBricksDict(source, source_details, dimensions, R, cursorStatus=False):
    """ Make bricksDict """
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    # update source data in case data needs to be refreshed
    source.data.update()
    for scn in bpy.data.scenes:
        scn.update()
    # get lattice bmesh
    print("\ngenerating blueprint...")
    lScale = (source_details.x.dist, source_details.y.dist, source_details.z.dist)
    offset = (source_details.x.mid, source_details.y.mid, source_details.z.mid)
    if source.parent is not None:
        offset = Vector(offset)-source.parent.location
        offset = offset.to_tuple()
    # get coordinate list from intersections of edges with faces
    coordMatrix = generateLattice(R, lScale, offset)
    if len(coordMatrix) == 0:
        coordMatrix.append((source_details.x.mid, source_details.y.mid, source_details.z.mid))
    # set calculationAxes
    calculationAxes = cm.calculationAxes if cm.brickShell != "Inside Mesh" else "XYZ"
    # set up faceIdxMatrix and brickFreqMatrix
    faceIdxMatrix = [[[0 for _ in range(len(coordMatrix[0][0]))] for _ in range(len(coordMatrix[0]))] for _ in range(len(coordMatrix))]
    brickFreqMatrix = getBrickMatrix(source, faceIdxMatrix, coordMatrix, cm.brickShell, axes=calculationAxes, cursorStatus=cursorStatus)

    # create bricks dictionary with brickFreqMatrix values
    keys = []
    i = 0
    bricksDict = {}
    threshold = getThreshold(cm)
    for x in range(len(coordMatrix)):
        for y in range(len(coordMatrix[0])):
            for z in range(len(coordMatrix[0][0])):
                co = coordMatrix[x][y][z]
                i += 1
                n = cm.source_name

                # get nearest face index and mat name
                nf = faceIdxMatrix[x][y][z]["idx"] if type(faceIdxMatrix[x][y][z]) == dict else None
                bKey = listToStr([x,y,z])
                keys.append(bKey)
                drawBrick = brickFreqMatrix[x][y][z] >= threshold
                bricksDict[bKey] = createBricksDictEntry(
                    name=         'Rebrickr_%(n)s_brick_%(i)s__%(bKey)s' % locals(),
                    val=          brickFreqMatrix[x][y][z],
                    draw=         drawBrick,
                    co=           (co[0]-source_details.x.mid, co[1]-source_details.y.mid, co[2]-source_details.z.mid),
                    nearest_face= nf,
                    mat_name=     "", # defined in 'addMaterialsToBricksDict' function
                )
    cm.numBricksGenerated = i

    # return list of created Brick objects
    return bricksDict
