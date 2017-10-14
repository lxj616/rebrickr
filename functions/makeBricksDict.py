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
from mathutils import Matrix, Vector

# Rebrickr imports
from .common_functions import *
from .generate_lattice import generateLattice
from .wrappers import *

def VectorRound(vec, dec, roundType="ROUND"):
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

def rayObjIntersections(point,direction,miniDist,edgeLen,ob):
    """ returns True if ray intersects obj """
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    # initialize variables
    intersections = 0
    nextIntersection = None
    firstIntersection = None
    lastIntersection = None
    edgeIntersects = False
    outsideL = []
    orig = point
    firstDirection0 = False
    firstDirection1 = False
    edgeLen2 = edgeLen*1.00001
    # set axis of direction
    if direction[0] > 0:
        axes = "XYZ"
    elif direction[1] > 0:
        axes = "YZX"
    else:
        axes = "ZXY"
    # run initial intersection check
    while True:
        _,location,normal,index = ob.ray_cast(orig,direction)#distance=edgeLen*1.00000000001)
        if index == -1: break
        if intersections == 0:
            firstDirection0 = direction.dot(normal)
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
        location = VectorRound(location, 5, roundType="CEILING")
        orig = location + miniDist
    if cm.insidenessRayCastDir == "High Efficiency" or axes[0] in cm.insidenessRayCastDir:
        outsideL.append(0)
        if intersections%2 == 0 and (not cm.useNormals or firstDirection0 <= 0):
            outsideL[0] = 1
        elif cm.castDoubleCheckRays:
            # double check vert is inside mesh
            count = 0
            orig = point
            while True:
                _,location,normal,index = ob.ray_cast(orig,-direction)#distance=edgeLen*1.00000000001)
                if index == -1: break
                if count == 0:
                    firstDirection1 = (-direction).dot(normal)
                count += 1
                location = VectorRound(location, 5, roundType="FLOOR")
                orig = location - miniDist
            if count%2 == 0 and (not cm.useNormals or firstDirection1 <= 0):
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
                while True:
                    _,location,normal,i = ob.ray_cast(orig,direction)#distance=edgeLen*1.00000000001)
                    if i == -1: break
                    if intersections == 0:
                        firstDirection0 = direction.dot(normal)
                    intersections += 1
                    location = VectorRound(location, 5, roundType="CEILING")
                    orig = location + miniDist
                if intersections%2 == 0 and (not cm.useNormals or firstDirection0 <= 0):
                    outsideL[i] = 1
                elif cm.castDoubleCheckRays:
                    # double check vert is inside mesh
                    count = 0
                    orig = point
                    while True:
                        _,location,normal,i = ob.ray_cast(orig,-direction)#distance=edgeLen*1.00000000001)
                        if i == -1: break
                        if count == 0:
                            firstDirection1 = (-direction).dot(normal)
                        count += 1
                        location = VectorRound(location, 5, roundType="FLOOR")
                        orig = location - miniDist
                    if count%2 == 0 and (not cm.useNormals or firstDirection1 <= 0):
                        outsideL[i] = 1

    # find average of outsideL and set outside accordingly (<0.5 is False, >=0.5 is True)
    total = 0
    for v in outsideL:
        total += v
    outside = total/len(outsideL) >= 0.5

    # return helpful information
    return not outside, edgeIntersects, intersections, nextIntersection, index, firstIntersection, lastIntersection

def updateBFMatrix(x0, y0, z0, coordMatrix, faceIdxMatrix, brickFreqMatrix, brickShell, source, x1, y1, z1, miniDist, inside=None):
    orig = coordMatrix[x0][y0][z0]
    try:
        rayEnd = coordMatrix[x1][y1][z1]
    except:
        return -1, None
    # check if point can be thrown away
    ray = rayEnd - orig
    edgeLen = ray.length

    origInside, edgeIntersects, intersections, nextIntersection, index, firstIntersection, lastIntersection = rayObjIntersections(orig,ray,miniDist,edgeLen,source)

    if origInside:
        if brickFreqMatrix[x0][y0][z0] == 0:
            # define brick as inside shell
            brickFreqMatrix[x0][y0][z0] = -1
    if edgeIntersects:
        if (origInside and brickShell == "Inside Mesh") or (not origInside and brickShell == "Outside Mesh") or brickShell == "Inside and Outside":
            # define brick as part of shell
            brickFreqMatrix[x0][y0][z0] = 2
            # set or update nearest face to brick
            if type(faceIdxMatrix[x0][y0][z0]) != dict or faceIdxMatrix[x0][y0][z0]["dist"] > firstIntersection["dist"]:
                faceIdxMatrix[x0][y0][z0] = firstIntersection
        if (not origInside and brickShell == "Inside Mesh") or (origInside and brickShell == "Outside Mesh") or brickShell == "Inside and Outside":
            # define brick as part of shell
            brickFreqMatrix[x1][y1][z1] = 2
            # set or update nearest face to brick
            if type(faceIdxMatrix[x1][y1][z1]) != dict or faceIdxMatrix[x1][y1][z1]["dist"] > lastIntersection["dist"]:
                faceIdxMatrix[x1][y1][z1] = lastIntersection

    return intersections, nextIntersection

def setNF(j, orig, target, faceIdxMatrix):
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    if ((1-j)*100) < cm.matShellDepth:
        faceIdxMatrix[target[0]][target[1]][target[2]] = faceIdxMatrix[orig[0]][orig[1]][orig[2]]

# TODO: Make this more efficient
def getBrickMatrix(source, faceIdxMatrix, coordMatrix, brickShell, axes="xyz", cursorStatus=False):
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
        miniDist = (coordMatrix[1][0][0] - coordMatrix[0][0][0])*0.00001
        for z in range(len(coordMatrix[0][0])):
            # print status to terminal
            if not scn.Rebrickr_printTimes:
                percent0 = len(coordMatrix)/denom * (z/(len(coordMatrix[0][0])-1))
                if percent0 < 100:
                    update_progress("Shell", percent0/100.0)
                    if cursorStatus:
                        wm.progress_update(percent0)
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
        miniDist = (coordMatrix[0][1][0] - coordMatrix[0][0][0])*0.00001
        for z in range(len(coordMatrix[0][0])):
            # print status to terminal
            if not scn.Rebrickr_printTimes:
                percent1 = percent0 + (len(coordMatrix[0])/denom * (z/(len(coordMatrix[0][0])-1)))
                if percent1 < 100:
                    update_progress("Shell", percent1/100.0)
                    if cursorStatus:
                        wm.progress_update(percent1)
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
        miniDist = (coordMatrix[0][0][1] - coordMatrix[0][0][0])*0.00001
        for x in range(len(coordMatrix)):
            # print status to terminal
            if not scn.Rebrickr_printTimes:
                percent2 = percent1 + (len(coordMatrix[0][0])/denom * (x/(len(coordMatrix)-1)))
                if percent2 < 100:
                    update_progress("Shell", percent2/100.0)
                    if cursorStatus:
                        wm.progress_update(percent2)
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
                # if current location is inside (-1) and adjacent location is out of bounds, current location is shell (2)
                if ((((z == len(coordMatrix[0][0])-1 or brickFreqMatrix[x][y][z+1] == 0) or (z == 0 or brickFreqMatrix[x][y][z-1] == 0)) and ("z" not in axes)) or# or cm.verifyExposure)) or
                    (((y == len(coordMatrix[0])-1 or brickFreqMatrix[x][y+1][z] == 0) or (y == 0 or brickFreqMatrix[x][y-1][z] == 0)) and ("y" not in axes)) or# or cm.verifyExposure)) or
                    (((x == len(coordMatrix)-1 or brickFreqMatrix[x+1][y][z] == 0) or (x == 0 or brickFreqMatrix[x-1][y][z] == 0))) and ("x" not in axes)):# or cm.verifyExposure)):
                    if brickFreqMatrix[x][y][z] == -1:
                        brickFreqMatrix[x][y][z] = 2
                        # TODO: set faceIdxMatrix value to nearest shell value using some sort of built in nearest poly to point function
                    # break from current location, as boundary locs should not be verified
                    continue
                if cm.verifyExposure:
                    # If inside location (-1) intersects outside location (0), make it ouside (0)
                    if brickFreqMatrix[x][y][z] == -1:
                        if brickFreqMatrix[x+1][y][z] == 0 or brickFreqMatrix[x-1][y][z] == 0 or brickFreqMatrix[x][y+1][z] == 0 or brickFreqMatrix[x][y-1][z] == 0 or brickFreqMatrix[x][y][z+1] == 0 or brickFreqMatrix[x][y][z-1] == 0:
                            brickFreqMatrix[x][y][z] = 0
                    # If shell location (2) does not intersect outside location (0), make it inside (-1)
                    if brickFreqMatrix[x][y][z] == 2 and brickFreqMatrix[x+1][y][z] != 0 and brickFreqMatrix[x-1][y][z] != 0 and brickFreqMatrix[x][y+1][z] != 0 and brickFreqMatrix[x][y-1][z] != 0 and brickFreqMatrix[x][y][z+1] != 0 and brickFreqMatrix[x][y][z-1] != 0:
                        brickFreqMatrix[x][y][z] = -1

    # print status to terminal
    if not scn.Rebrickr_printTimes:
        update_progress("Shell", 1)
        if cursorStatus:
            wm.progress_end()

    # set up brickFreqMatrix values for bricks inside shell
    j = 1
    # NOTE: Following two lines are alternative for calculating partial brickFreqMatrix (insideness only calculated as deep as necessary)
    denom = min([(cm.shellThickness-1), max(len(coordMatrix)-2, len(coordMatrix[0])-2, len(coordMatrix[0][0])-2)])/2
    for idx in range(cm.shellThickness-1):
    # NOTE: Following two lines are alternative for calculating full brickFreqMatrix
    # denom = max(len(coordMatrix)-2, len(coordMatrix[0])-2, len(coordMatrix[0][0])-2)/2
    # for idx in range(100):
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
                            origVal = brickFreqMatrix[x][y][z]
                            brickFreqMatrix[x][y][z] = j
                            missed = False
                            if j == 0.99:
                                if brickFreqMatrix[x+1][y][z] == 2:
                                    setNF(j, (x+1,y,z), (x,y,z), faceIdxMatrix)
                                elif brickFreqMatrix[x-1][y][z] == 2:
                                    setNF(j, (x-1,y,z), (x,y,z), faceIdxMatrix)
                                elif brickFreqMatrix[x][y+1][z] == 2:
                                    setNF(j, (x,y+1,z), (x,y,z), faceIdxMatrix)
                                elif brickFreqMatrix[x][y-1][z] == 2:
                                    setNF(j, (x,y-1,z), (x,y,z), faceIdxMatrix)
                                elif brickFreqMatrix[x][y][z+1] == 2:
                                    setNF(j, (x,y,z+1), (x,y,z), faceIdxMatrix)
                                elif brickFreqMatrix[x][y][z-1] == 2:
                                    setNF(j, (x,y,z-1), (x,y,z), faceIdxMatrix)
                                else:
                                    brickFreqMatrix[x][y][z] = origVal
                                    missed = True
                            else:
                                if brickFreqMatrix[x+1][y][z] == round(j + 0.01,2):
                                    setNF(j, (x+1,y,z), (x,y,z), faceIdxMatrix)
                                elif brickFreqMatrix[x-1][y][z] == round(j + 0.01,2):
                                    setNF(j, (x-1,y,z), (x,y,z), faceIdxMatrix)
                                elif brickFreqMatrix[x][y+1][z] == round(j + 0.01,2):
                                    setNF(j, (x,y+1,z), (x,y,z), faceIdxMatrix)
                                elif brickFreqMatrix[x][y-1][z] == round(j + 0.01,2):
                                    setNF(j, (x,y-1,z), (x,y,z), faceIdxMatrix)
                                elif brickFreqMatrix[x][y][z+1] == round(j + 0.01,2):
                                    setNF(j, (x,y,z+1), (x,y,z), faceIdxMatrix)
                                elif brickFreqMatrix[x][y][z-1] == round(j + 0.01,2):
                                    setNF(j, (x,y,z-1), (x,y,z), faceIdxMatrix)
                                else:
                                    brickFreqMatrix[x][y][z] = origVal
                                    missed = True
                            if not missed:
                                gotOne = True
                        except:
                            pass
        if not gotOne:
            break

    # print status to terminal
    if scn.Rebrickr_printTimes:
        stopWatch("Internal", time.time()-ct)
        ct = time.time()
    elif cm.shellThickness-1:
        update_progress("Internal", 1)

    # Draw supports
    if cm.internalSupports == "Columns":
        start = cm.colStep + cm.colThickness
        stop = len(coordMatrix)
        step = cm.colStep + cm.colThickness
        for x in range(start, stop, step):
            for y in range(start, len(coordMatrix[0]), step):
                for z in range(0, len(coordMatrix[0][0])):
                    for j in range(cm.colThickness):
                        for k in range(cm.colThickness):
                            if (brickFreqMatrix[x-j][y-k][z] > 0 and brickFreqMatrix[x-j][y-k][z] < 1) or brickFreqMatrix[x-j][y-k][z] == -1:
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
                    if (brickFreqMatrix[x][y][z] > 0 and brickFreqMatrix[x][y][z] < 1) or brickFreqMatrix[x][y][z] == -1:
                        brickFreqMatrix[x][y][z] = 1.5

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

@timed_call('Time Elapsed')
def makeBricksDict(source, source_details, dimensions, R, cursorStatus=False):
    """ Make bricks """
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    # update source data in case data needs to be refreshed
    source.data.update()
    for scn in bpy.data.scenes:
        scn.update()
    # get lattice bmesh
    print("\ngenerating blueprint...")
    lScale = (source_details.x.distance, source_details.y.distance, source_details.z.distance)
    offset = (source_details.x.mid, source_details.y.mid, source_details.z.mid)
    if source.parent is not None:
        offset = Vector(offset)-source.parent.location
        offset = offset.to_tuple()
    if cm.brickType == "Custom":
        R = (R[0] * cm.distOffsetX, R[1] * cm.distOffsetY, R[2] * cm.distOffsetZ)
    coordMatrix = generateLattice(R, lScale, offset)
    # drawBMesh(makeLattice(R, lScale, offset))
    if cm.brickShell != "Inside Mesh":
        calculationAxes = cm.calculationAxes
    else:
        calculationAxes = "XYZ"

    faceIdxMatrix = [[[0 for _ in range(len(coordMatrix[0][0]))] for _ in range(len(coordMatrix[0]))] for _ in range(len(coordMatrix))]

    brickFreqMatrix = getBrickMatrix(source, faceIdxMatrix, coordMatrix, cm.brickShell, axes=calculationAxes, cursorStatus=cursorStatus)

    # get coordinate list from intersections of edges with faces
    threshold = 1.01 - (cm.shellThickness / 100)

    coList = getCOList(brickFreqMatrix, coordMatrix, threshold)
    # if no coords in coList, add a coord at center of source
    if len(coList) == 0:
        coList.append((source_details.x.mid, source_details.y.mid, source_details.z.mid))

    # create bricks dictionary with brickFreqMatrix values
    bricks = []
    i = 0
    bricksDict = {}
    for x in range(len(coList)):
        for y in range(len(coList[0])):
            for z in range(len(coList[0][0])):
                co = coList[x][y][z]
                if co != -1:
                    i += 1
                    n = cm.source_name
                    j = str(i+1)

                    # get nearest face index and mat name
                    nf = None
                    if type(faceIdxMatrix[x][y][z]) == dict:
                        nf = faceIdxMatrix[x][y][z]["idx"]
                    bricksDict[str(x) + "," + str(y) + "," + str(z)] = {
                        "name":'Rebrickr_%(n)s_brick_%(j)s' % locals(),
                        "val":brickFreqMatrix[x][y][z],
                        "co":(co[0]-source_details.x.mid, co[1]-source_details.y.mid, co[2]-source_details.z.mid),
                        "nearestFaceIdx":nf,
                        "matName":"", # defined in 'addMaterialsToBricksDict' function
                        "connected":False}
                else:
                    bricksDict[str(x) + "," + str(y) + "," + str(z)] = {
                        "name":"DNE",
                        "val":brickFreqMatrix[x][y][z],
                        "co":None,
                        "nearestFaceIdx":None,
                        "matName":None,
                        "connected":False}

    # return list of created Brick objects
    return bricksDict

def addMaterialsToBricksDict(bricksDict, source):
    for key in bricksDict.keys():
        nf = bricksDict[key]["nearestFaceIdx"]
        if bricksDict[key]["name"] != "DNE" and nf is not None:
            f = source.data.polygons[nf]
            slot = source.material_slots[f.material_index]
            mat = slot.material
            matName = mat.name
            bricksDict[key]["matName"] = matName
    return bricksDict
