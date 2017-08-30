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
from .checkWaterTight import isOneMesh
from .makeBricks import *
from ..classes.Brick import Bricks
from mathutils import Matrix, Vector, geometry
from mathutils.bvhtree import BVHTree
props = bpy.props

def modalRunning():
    try:
        if bpy.context.window_manager["list_modal_running"] == True:
            return True
    except:
        pass
    return False

def getSafeScn():
    safeScn = bpy.data.scenes.get("LEGOizer_storage (DO NOT RENAME)")
    if safeScn == None:
        safeScn = bpy.data.scenes.new("LEGOizer_storage (DO NOT RENAME)")
    return safeScn
def safeUnlink(obj, hide=True, protected=True):
    scn = bpy.context.scene
    safeScn = getSafeScn()
    scn.objects.unlink(obj)
    safeScn.objects.link(obj)
    if protected:
        obj.protected = True
    if hide:
        obj.hide = True
def safeLink(obj, unhide=False):
    scn = bpy.context.scene
    safeScn = getSafeScn()
    scn.objects.link(obj)
    obj.protected = False
    if unhide:
        obj.hide = False
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

def getClosestPolyIndex(point,maxLen,ob):
    """ returns nearest polygon to point within edgeLen """
    # initialize variables
    shortestLen = maxLen
    closestPolyIdx = None
    # run initial intersection check
    for direction in [(1,0,0), (0,1,0), (0,0,1), (-1,0,0), (0,-1,0), (0,0,-1)]:
        _,location,normal,index = ob.ray_cast(point,direction)#,distance=edgeLen*1.00000000001)
        if index == -1: continue
        nextLen = (Vector(point) - Vector(location)).length
        if nextLen < shortestLen:
            shortestLen = nextLen
            closestPolyIdx = index
    # return helpful information
    return closestPolyIdx

def setOriginToObjOrigin(toObj, fromObj=None, fromLoc=None, deleteFromObj=False):
    scn = bpy.context.scene
    oldCursorLocation = tuple(scn.cursor_location)
    unlinkToo = False
    if fromObj is not None:
        scn.cursor_location = fromObj.matrix_world.to_translation().to_tuple()
    elif fromLoc is not None:
        scn.cursor_location = fromLoc
    else:
        print("ERROR in 'setOriginToObjOrigin': fromObj and fromLoc are both None")
        return
    select(toObj, active=toObj)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    scn.cursor_location = oldCursorLocation
    if fromObj is not None:
        if deleteFromObj:
            m = fromObj.data
            bpy.data.objects.remove(fromObj)
            bpy.data.meshes.remove(m)

def storeTransformData(obj):
    """ store location, rotation, and scale data for model """
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    if obj is not None:
        cm.modelLoc = str(obj.location.to_tuple())[1:-1]
        cm.modelRot = str(tuple(obj.rotation_euler))[1:-1]
        cm.modelScale = str(obj.scale.to_tuple())[1:-1]
    elif obj is None:
        cm.modelLoc = "0,0,0"
        cm.modelRot = "0,0,0"
        cm.modelScale = "1,1,1"

def convertToFloats(lst):
    for i in range(len(lst)):
        lst[i] = float(lst[i])
    return lst

def setTransformData(objList, source=None, skipLocation=False):
    """ set location, rotation, and scale data for model """
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    objList = confirmList(objList)
    for obj in objList:
        l,r,s = getTransformData()
        if not skipLocation:
            obj.location = obj.location + Vector(l)
            if source is not None:
                n = cm.source_name
                LEGOizer_last_origin_on = "LEGOizer_%(n)s_last_origin" % locals()
                last_origin_obj = bpy.data.objects.get(LEGOizer_last_origin_on)
                if last_origin_obj is not None:
                    obj.location -= Vector(last_origin_obj.location) - Vector(source["previous_location"])
                else:
                    obj.location -= Vector(source.location) - Vector(source["previous_location"])
        obj.rotation_euler = Vector(obj.rotation_euler) + Vector(r)
        if source is not None:
            obj.rotation_euler = Vector(obj.rotation_euler) - (Vector(source.rotation_euler) - Vector(source["previous_rotation"]))
        obj.scale = (obj.scale[0] * s[0], obj.scale[1] * s[1], obj.scale[2] * s[2])
        if source is not None:
            obj.scale -= Vector(source.scale) - Vector(source["previous_scale"])

def getTransformData():
    """ set location, rotation, and scale data for model """
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    l = tuple(convertToFloats(cm.modelLoc.split(",")))
    r = tuple(convertToFloats(cm.modelRot.split(",")))
    s = tuple(convertToFloats(cm.modelScale.split(",")))
    return l,r,s

def setSourceTransform(source, obj=None, objParent=None, last_origin_obj=None):
    if obj is not None:
        objLoc = obj.location
        objRot = obj.rotation_euler
        objScale = obj.scale
    else:
        objLoc = Vector((0,0,0))
        objRot = Vector((0,0,0))
        objScale = Vector((1,1,1))
    if objParent is not None:
        objParentLoc = objParent.location
        objParentRot = objParent.rotation_euler
        objParentScale = objParent.scale
    else:
        objParentLoc = Vector((0,0,0))
        objParentRot = Vector((0,0,0))
        objParentScale = Vector((1,1,1))
    if last_origin_obj is not None:
        source.location = objParentLoc + objLoc - (Vector(last_origin_obj.location) - Vector(source["previous_location"]))
    else:
        source.location = objParentLoc + objLoc
    source.rotation_euler = (source.rotation_euler[0] + objRot[0] + objParentRot[0], source.rotation_euler[1] + objRot[1] + objParentRot[1], source.rotation_euler[2] + objRot[2] + objParentRot[2])
    source.scale = (source.scale[0] * objScale[0] * objParentScale[0], source.scale[1] * objScale[1] * objParentScale[1], source.scale[2] * objScale[2] * objParentScale[2])

def rayObjIntersections(point,direction,edgeLen,ob):
    """ returns True if ray intersects obj """
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    # initialize variables
    intersections = 0
    nextIntersection = None
    firstIntersection = None
    lastIntersection = None
    edgeIntersects = False
    outside = False
    orig = point
    doubleCheckDirection = -direction
    firstDirection0 = False
    firstDirection1 = False
    # run initial intersection check
    while True:
        _,location,normal,index = ob.ray_cast(orig,direction)#distance=edgeLen*1.00000000001)
        if index == -1: break
        if intersections == 0:
            firstDirection0 = direction.dot(normal)
        # get first and last intersection (used when getting materials of nearest (first or last intersected) face)
        if (location-point).length <= edgeLen*1.00001:
            if intersections == 0:
                edgeIntersects = True
                firstIntersection = {"idx":index, "dist":(location-point).length}
            lastIntersection = {"idx":index, "dist":edgeLen - (location-point).length}
        # set nextIntersection
        if intersections == 1:
            nextIntersection = location.copy()
        intersections += 1
        orig = location + direction*0.00001
    if intersections%2 == 0 and (not cm.useNormals or firstDirection0 <= 0):
        outside = True
    else:
        # double check vert is inside mesh
        count = 0
        orig = point
        while True:
            _,location,normal,index = ob.ray_cast(orig,doubleCheckDirection)#distance=edgeLen*1.00000000001)
            if index == -1: break
            if count == 0:
                firstDirection1 = doubleCheckDirection.dot(normal)
            count += 1
            orig = location + doubleCheckDirection*0.00001
        if count%2 == 0 and (not cm.useNormals or firstDirection1 <= 0):
            outside = True

    # return helpful information
    return not outside, edgeIntersects, intersections, nextIntersection, index, firstIntersection, lastIntersection

def updateBFMatrix(x0, y0, z0, coordMatrix, faceIdxMatrix, brickFreqMatrix, brickShell, source, x1, y1, z1, inside=None):
    orig = coordMatrix[x0][y0][z0]
    try:
        rayEnd = coordMatrix[x1][y1][z1]
    except:
        return -1, None
    # check if point can be thrown away
    ray = rayEnd - orig
    edgeLen = ray.length

    origInside, edgeIntersects, intersections, nextIntersection, index, firstIntersection, lastIntersection = rayObjIntersections(orig,ray,edgeLen,source)

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
        for z in range(len(coordMatrix[0][0])):
            # print status to terminal
            if not scn.printTimes:
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
                    intersections, nextIntersection = updateBFMatrix(x, y, z, coordMatrix, faceIdxMatrix, brickFreqMatrix, brickShell, source, x+1, y, z)
                    if intersections == 0:
                        break
    # print status to terminal
    if scn.printTimes:
        stopWatch("X Axis", time.time()-ct)
        ct = time.time()

    if "y" in axes:
        for z in range(len(coordMatrix[0][0])):
            # print status to terminal
            if not scn.printTimes:
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
                    intersections, nextIntersection = updateBFMatrix(x, y, z, coordMatrix, faceIdxMatrix, brickFreqMatrix, brickShell, source, x, y+1, z)
                    if intersections == 0:
                        break
    # print status to terminal
    if scn.printTimes:
        stopWatch("Y Axis", time.time()-ct)
        ct = time.time()

    if "z" in axes:
        for x in range(len(coordMatrix)):
            # print status to terminal
            if not scn.printTimes:
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
                    intersections, nextIntersection = updateBFMatrix(x, y, z, coordMatrix, faceIdxMatrix, brickFreqMatrix, brickShell, source, x, y, z+1)
                    if intersections == 0:
                        break
    # print status to terminal
    if scn.printTimes:
        stopWatch("Z Axis", time.time()-ct)
        ct = time.time()

    # adjust brickFreqMatrix values
    for x in range(len(coordMatrix)):
        for y in range(len(coordMatrix[0])):
            for z in range(len(coordMatrix[0][0])):
                # if current location is inside (-1) and adjacent location is out of bounds, current location is shell (2)
                if ((((z == len(coordMatrix[0][0])-1 or brickFreqMatrix[x][y][z+1] == 0) or (z == 0 or brickFreqMatrix[x][y][z-1] == 0)) and ("z" not in axes or cm.verifyExposure)) or
                    (((y == len(coordMatrix[0])-1 or brickFreqMatrix[x][y+1][z] == 0) or (y == 0 or brickFreqMatrix[x][y-1][z] == 0)) and ("y" not in axes or cm.verifyExposure)) or
                    (((x == len(coordMatrix)-1 or brickFreqMatrix[x+1][y][z] == 0) or (x == 0 or brickFreqMatrix[x-1][y][z] == 0))) and ("x" not in axes or cm.verifyExposure)):
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
    if not scn.printTimes:
        update_progress("Shell", 1)
        if cursorStatus:
            wm.progress_end()

    # set up brickFreqMatrix values for bricks inside shell
    j = 1
    denom = min([(cm.shellThickness-1), max(len(coordMatrix)-2, len(coordMatrix[0])-2, len(coordMatrix[0][0])-2)])/2
    for idx in range(cm.shellThickness-1): # TODO: set to 100 if brickFreqMatrix should be prepared for higher thickness values
        # print status to terminal
        if not scn.printTimes:
            linPercent = idx/denom
            update_progress("Internal", linPercent)
            # if linPercent == 0:
            #     update_progress("Internal", 0.0)
            # else:
            #     expPercent = linPercent + linPercent*(10/(linPercent*100))
            #     if expPercent < 100:
            #         update_progress("Internal", expPercent)
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
    if scn.printTimes:
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
    if scn.printTimes:
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

def makeBricksDict(source, source_details, dimensions, R, cursorStatus=False):
    """ Make bricks """
    ct = time.time()
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
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
    brickDict = {}
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
                    matName = ""
                    if type(faceIdxMatrix[x][y][z]) == dict:
                        nf = faceIdxMatrix[x][y][z]["idx"]
                        if len(source.material_slots) > 0:
                            f = source.data.polygons[nf]
                            slot = source.material_slots[f.material_index]
                            mat = slot.material
                            matName = mat.name
                    brickDict[str(x) + "," + str(y) + "," + str(z)] = {
                        "name":'LEGOizer_%(n)s_brick_%(j)s' % locals(),
                        "val":brickFreqMatrix[x][y][z],
                        "co":(co[0]-source_details.x.mid, co[1]-source_details.y.mid, co[2]-source_details.z.mid),
                        "nearestFaceIdx":nf,
                        "matName":matName,
                        "connected":False}
                else:
                    brickDict[str(x) + "," + str(y) + "," + str(z)] = {
                        "name":"DNE",
                        "val":brickFreqMatrix[x][y][z],
                        "co":None,
                        "nearestFaceIdx":None,
                        "matName":None,
                        "connected":False}


    stopWatch("Time Elapsed", time.time()-ct)

    # return list of created Brick objects
    return brickDict
