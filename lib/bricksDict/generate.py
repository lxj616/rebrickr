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
import numpy as np

# Blender imports
import bpy
from bpy.types import Object
from mathutils import Matrix, Vector

# Addon imports
from .functions import *
from ...functions.common import *
from ...functions.general import *
from ...functions.generate_lattice import generateLattice
from ...functions.wrappers import *
from ...functions.smoke_sim import *
from ..Brick import Bricks
from bpy.types import Object

def VectorRound(vec, dec, roundType="ROUND"):
    """ round all vals in Vector 'vec' to 'dec' precision """
    if roundType == "ROUND":
        lst = [round(vec[i], dec) for i in range(len(vec))]
    elif roundType == "FLOOR":
        lst = [(math.floor(vec[i] * 10**dec)) / 10**dec for i in range(len(vec))]
    elif roundType in ["CEILING", "CEIL"]:
        lst = [(math.ceil(vec[i] * 10**dec)) / 10**dec for i in range(len(vec))]
    return Vector(lst)

def castRays(obj:Object, point:Vector, direction:Vector, miniDist:float, roundType:str="CEILING", edgeLen:int=0):
    """
    obj       -- source object to test intersections for
    point     -- origin point for ray casting
    direction -- cast ray in this direction
    miniDist  -- Vector with miniscule amount to add after intersection
    roundType -- round final intersection location Vector with this type
    edgeLen   -- distance to test for intersections
    """
    # initialize variables
    firstDirection = False
    firstIntersection = None
    nextIntersection = None
    lastIntersection = None
    edgeIntersects = False
    edgeLen2 = edgeLen*1.00001
    orig = point
    intersections = 0
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
                    firstIntersection = {"idx":index, "dist":(location-point).length, "loc":location, "normal":normal}
                lastIntersection = {"idx":index, "dist":edgeLen - (location-point).length, "loc":location, "normal":normal}

            # set nextIntersection
            if intersections == 1:
                nextIntersection = location.copy()
        intersections += 1
        location = VectorRound(location, 5, roundType=roundType)
        orig = location + miniDist

    return intersections, firstDirection, firstIntersection, nextIntersection, lastIntersection, edgeIntersects

def rayObjIntersections(scn, cm, point, direction, miniDist:Vector, edgeLen, obj):
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
    if cm.insidenessRayCastDir == "HIGH EFFICIENCY" or axes[0] in cm.insidenessRayCastDir:
        outsideL.append(0)
        if intersections%2 == 0 and not (cm.useNormals and firstDirection > 0):
            outsideL[0] = 1
        elif cm.castDoubleCheckRays:
            # double check vert is inside mesh
            count, firstDirection,_,_,_,_ = castRays(obj, point, -direction, -miniDist, roundType="FLOOR")
            if count%2 == 0 and not (cm.useNormals and firstDirection > 0):
                outsideL[0] = 1

    # run more checks if verifyExposure is True
    if cm.insidenessRayCastDir != "HIGH EFFICIENCY":
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
                    outsideL[len(outsideL) - 1] = 1
                elif cm.castDoubleCheckRays:
                    # double check vert is inside mesh
                    count, firstDirection,_,_,_,_ = castRays(obj, point, -direction, -miniDist, roundType="FLOOR")
                    if count%2 == 0 and not (cm.useNormals and firstDirection > 0):
                        outsideL[len(outsideL) - 1] = 1

    # find average of outsideL and set outside accordingly (<0.5 is False, >=0.5 is True)
    outside = sum(outsideL)/len(outsideL) >= 0.5

    # return helpful information
    return not outside, edgeIntersects, intersections, nextIntersection, firstIntersection, lastIntersection

def updateBFMatrix(scn, cm, x0, y0, z0, coordMatrix, faceIdxMatrix, brickFreqMatrix, brickShell, source, x1, y1, z1, miniDist, inside=None):
    """ update brickFreqMatrix[x0][y0][z0] based on results from rayObjIntersections """
    orig = coordMatrix[x0][y0][z0]
    try:
        rayEnd = coordMatrix[x1][y1][z1]
    except IndexError:
        return -1, None
    # check if point can be thrown away
    ray = rayEnd - orig
    edgeLen = ray.length

    origInside, edgeIntersects, intersections, nextIntersection, firstIntersection, lastIntersection = rayObjIntersections(scn, cm, orig, ray, miniDist, edgeLen, source)
    if origInside and brickFreqMatrix[x0][y0][z0] == 0:
        # define brick as inside shell
        brickFreqMatrix[x0][y0][z0] = -1
    if edgeIntersects:
        if (origInside and brickShell == "INSIDE") or (not origInside and brickShell == "OUTSIDE") or brickShell == "INSIDE AND OUTSIDE":
            # define brick as part of shell
            brickFreqMatrix[x0][y0][z0] = 1
            # set or update nearest face to brick
            if type(faceIdxMatrix[x0][y0][z0]) != dict or faceIdxMatrix[x0][y0][z0]["dist"] > firstIntersection["dist"]:
                faceIdxMatrix[x0][y0][z0] = firstIntersection
        if (not origInside and brickShell == "INSIDE") or (origInside and brickShell == "OUTSIDE") or brickShell == "INSIDE AND OUTSIDE":
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
    """ check if brick entry in bricksDict is internal """
    val = bricksDict[key]["val"]
    return (val > 0 and val < 1) or val == -1

def addColumnSupports(cm, bricksDict, keys):
    """ update bricksDict internal entries to draw columns
    cm         -- active cmlist object
    bricksDict -- dictionary with brick information at each lattice coordinate
    keys       -- keys to test in bricksDict
    """
    step = cm.colStep + cm.colThickness
    for key in keys:
        x,y,z = strToList(key)
        if (x % step in range(cm.colThickness) and
            y % step in range(cm.colThickness) and
            isInternal(bricksDict, key)
           ):
            bricksDict[key]["draw"] = True

def addLatticeSupports(cm, bricksDict, keys):
    """ update bricksDict internal entries to draw lattice supports
    cm         -- active cmlist object
    bricksDict -- dictionary with brick information at each lattice coordinate
    keys       -- keys to test in bricksDict
    """
    step = cm.latticeStep
    for key in keys:
        x,y,z = strToList(key)
        if x % step == 0 and (not cm.alternateXY or z % 2 == 0):
            if isInternal(bricksDict, key):
                bricksDict[key]["draw"] = True
        elif y % step == 0 and (not cm.alternateXY or z % 2 == 1):
            if isInternal(bricksDict, key):
                bricksDict[key]["draw"] = True

def updateInternal(bricksDict, cm, keys="ALL", clearExisting=False):
    """ update bricksDict internal entries
    cm            -- active cmlist object
    bricksDict    -- dictionary with brick information at each lattice coordinate
    keys          -- keys to test in bricksDict
    clearExisting -- set draw for all internal bricks to False before adding supports
    """
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
    if cm.internalSupports == "COLUMNS":
        addColumnSupports(cm, bricksDict, keys)
    # draw lattice supports
    elif cm.internalSupports == "LATTICE":
        addLatticeSupports(cm, bricksDict, keys)

def getBrickMatrix(source, faceIdxMatrix, coordMatrix, brickShell, axes="xyz", cursorStatus=False):
    """ returns new brickFreqMatrix """
    scn, cm, _ = getActiveContextInfo()
    brickFreqMatrix = deepcopy(faceIdxMatrix)
    axes = axes.lower()

    # initialize values used for printing status
    denom = (len(brickFreqMatrix[0][0]) + len(brickFreqMatrix[0]) + len(brickFreqMatrix))/100
    if cursorStatus:
        wm = bpy.context.window_manager
        wm.progress_begin(0, 100)

    def printStatus(percentStart, num0, denom0, lastPercent):
        # print status to terminal
        percent = percentStart + (len(brickFreqMatrix)/denom * (num0/(denom0-1))) / 100
        updateProgressBars(True, cursorStatus, percent, 0, "Shell")
        return percent

    percent0 = 0
    if "x" in axes:
        miniDist = Vector((0.00015, 0.0, 0.0))
        for z in range(len(brickFreqMatrix[0][0])):
            # # print status to terminal
            percent0 = printStatus(0, z, len(brickFreqMatrix[0][0]), percent0)
            for y in range(len(brickFreqMatrix[0])):
                for x in range(len(brickFreqMatrix)):
                    intersections, nextIntersection = updateBFMatrix(scn, cm, x, y, z, coordMatrix, faceIdxMatrix, brickFreqMatrix, brickShell, source, x+1, y, z, miniDist)
                    if intersections == 0:
                        break

    percent1 = percent0
    if "y" in axes:
        miniDist = Vector((0.0, 0.00015, 0.0))
        for z in range(len(brickFreqMatrix[0][0])):
            # # print status to terminal
            percent1 = printStatus(percent0, z, len(brickFreqMatrix[0][0]), percent1)
            for x in range(len(brickFreqMatrix)):
                for y in range(len(brickFreqMatrix[0])):
                    intersections, nextIntersection = updateBFMatrix(scn, cm, x, y, z, coordMatrix, faceIdxMatrix, brickFreqMatrix, brickShell, source, x, y+1, z, miniDist)
                    if intersections == 0:
                        break

    percent2 = percent1
    if "z" in axes:
        miniDist = Vector((0.0, 0.0, 0.00015))
        for x in range(len(brickFreqMatrix)):
            # # print status to terminal
            percent2 = printStatus(percent1, x, len(brickFreqMatrix), percent2)
            for y in range(len(brickFreqMatrix[0])):
                for z in range(len(brickFreqMatrix[0][0])):
                    intersections, nextIntersection = updateBFMatrix(scn, cm, x, y, z, coordMatrix, faceIdxMatrix, brickFreqMatrix, brickShell, source, x, y, z+1, miniDist)
                    if intersections == 0:
                        break


    # mark inside freqs as internal (-1) and outside next to outsides for removal
    adjustBFM(brickFreqMatrix, cm.verifyExposure, axes=axes)

    # print status to terminal
    updateProgressBars(True, cursorStatus, 1, 0, "Shell", end=True)

    # update internals of brickFreqMatrix
    updateInternals(brickFreqMatrix, cm=cm, faceIdxMatrix=faceIdxMatrix)

    return brickFreqMatrix


def getBrickMatrixSmoke(source, faceIdxMatrix, brickShell, cursorStatus=False):
    scn, cm, _ = getActiveContextInfo()
    density_grid, flame_grid, color_grid, smoke_res = getSmokeInfo(source)
    brickFreqMatrix = deepcopy(faceIdxMatrix)
    colorMatrix = deepcopy(faceIdxMatrix)
    denom = len(faceIdxMatrix) * len(faceIdxMatrix[0]) * len(faceIdxMatrix[0][0])
    old_percent = 0

    xn0 = smoke_res[0] // len(faceIdxMatrix)
    yn0 = smoke_res[1] // len(faceIdxMatrix[0])
    zn0 = smoke_res[2] // len(faceIdxMatrix[0][0])
    step = 1

    if 0 in [xn0, yn0, zn0]:
        return brickFreqMatrix, colorMatrix

    # set up brickFreqMatrix values
    for x in range(len(faceIdxMatrix)):
        for y in range(len(faceIdxMatrix[0])):
            for z in range(len(faceIdxMatrix[0][0])):
                # print status to terminal
                old_percent = updateProgressBars(True, cursorStatus, (x * y * z) / denom, old_percent, "Shell")
                d_acc = 0
                c_acc = Vector((0, 0, 0))
                for x1 in range(xn0 * x, xn0 * (x+1), step):
                    for y1 in range(yn0 * y, yn0 * (y+1), step):
                        for z1 in range(zn0 * z, zn0 * (z+1), step):
                            cur_idx = (z1 * smoke_res[1] + y1) * smoke_res[0] + x1
                            d_acc += density_grid[cur_idx]
                            c_acc += Vector((color_grid[cur_idx], color_grid[cur_idx + 1], color_grid[cur_idx + 2]))
                d_ave = d_acc / (xn0 / step)
                c_ave = c_acc / (xn0 / step)
                brickFreqMatrix[x][y][z] = 0 if d_ave < cm.smokeThresh else 1
                colorMatrix[x][y][z] = list(c_ave) + [d_ave]
    # end progress bar
    updateProgressBars(True, cursorStatus, 1, 0, "Shell", end=True)

    # mark inside freqs as internal (-1) and outside next to outsides for removal
    adjustBFM(brickFreqMatrix, False)

    # update internals of brickFreqMatrix
    updateInternals(brickFreqMatrix)

    return brickFreqMatrix, colorMatrix


def adjustBFM(brickFreqMatrix, verifyExposure, axes=""):
    """ adjust brickFreqMatrix values """
    for x in range(len(brickFreqMatrix)):
        for y in range(len(brickFreqMatrix[0])):
            for z in range(len(brickFreqMatrix[0][0])):
                # if current location is inside (-1) and adjacent location is out of bounds, current location is shell (1)
                if (("z" not in axes and
                     (z in [0, len(brickFreqMatrix[0][0])-1] or
                      brickFreqMatrix[x][y][z+1] == 0 or
                      brickFreqMatrix[x][y][z-1] == 0)) or
                    ("y" not in axes and
                     (y in [0, len(brickFreqMatrix[0])-1] or
                      brickFreqMatrix[x][y+1][z] == 0 or
                      brickFreqMatrix[x][y-1][z] == 0)) or
                    ("x" not in axes and
                     (x in [0, len(brickFreqMatrix)-1] or
                      brickFreqMatrix[x+1][y][z] == 0 or
                      brickFreqMatrix[x-1][y][z] == 0))
                   ):
                    if brickFreqMatrix[x][y][z] == -1:
                        brickFreqMatrix[x][y][z] = 1
                        # TODO: set faceIdxMatrix value to nearest shell value using some sort of built in nearest poly to point function
                    # continue since boundary locs should not be verified in this case
                    continue
                # If inside location (-1) intersects outside location (0), make it ouside (0)
                if verifyExposure:
                    if (brickFreqMatrix[x][y][z] == -1 and
                        (brickFreqMatrix[x+1][y][z] == 0 or
                         brickFreqMatrix[x-1][y][z] == 0 or
                         brickFreqMatrix[x][y+1][z] == 0 or
                         brickFreqMatrix[x][y-1][z] == 0 or
                         brickFreqMatrix[x][y][z+1] == 0 or
                         brickFreqMatrix[x][y][z-1] == 0)):
                        brickFreqMatrix[x][y][z] = 0
                # If shell location (1) does not intersect outside location (0), make it inside (-1)
                if (brickFreqMatrix[x][y][z] == 1 and
                    brickFreqMatrix[x+1][y][z] != 0 and
                    brickFreqMatrix[x-1][y][z] != 0 and
                    brickFreqMatrix[x][y+1][z] != 0 and
                    brickFreqMatrix[x][y-1][z] != 0 and
                    brickFreqMatrix[x][y][z+1] != 0 and
                    brickFreqMatrix[x][y][z-1] != 0):
                    brickFreqMatrix[x][y][z] = -1
                # mark outside brickFreqMatrix values not adjacent to an inside value for removal
                if (brickFreqMatrix[x][y][z] == 0 and
                    (x == len(brickFreqMatrix) - 1 or       brickFreqMatrix[x+1][y][z] == 0) and
                    (x == 0 or                              brickFreqMatrix[x-1][y][z] == 0) and
                    (y == len(brickFreqMatrix[0]) - 1 or    brickFreqMatrix[x][y+1][z] == 0) and
                    (y == 0 or                              brickFreqMatrix[x][y-1][z] == 0) and
                    (z == len(brickFreqMatrix[0][0]) - 1 or brickFreqMatrix[x][y][z+1] == 0) and
                    (z == 0 or                              brickFreqMatrix[x][y][z-1] == 0)):
                    brickFreqMatrix[x][y][z] = None


def updateInternals(brickFreqMatrix, cm=None, faceIdxMatrix=None):
    """ set up brickFreqMatrix values for bricks inside shell (-1) """
    j = 1
    # NOTE: Following two lines are alternative for calculating partial brickFreqMatrix (insideness only calculated as deep as necessary)
    # denom = min([(cm.shellThickness-1), max(len(brickFreqMatrix)-2, len(brickFreqMatrix[0])-2, len(brickFreqMatrix[0][0])-2)])/2
    # for idx in range(cm.shellThickness-1):
    # NOTE: Following two lines are alternative for calculating full brickFreqMatrix
    denom = max(len(brickFreqMatrix)-2, len(brickFreqMatrix[0])-2, len(brickFreqMatrix[0][0])-2)/2
    for i in range(100):
        j = round(j-0.01, 2)
        gotOne = False
        for x in range(len(brickFreqMatrix)):
            for y in range(len(brickFreqMatrix[0])):
                for z in range(len(brickFreqMatrix[0][0])):
                    if brickFreqMatrix[x][y][z] != -1:
                        continue
                    idxsToCheck = [(x+1, y, z),
                                   (x-1, y, z),
                                   (x, y+1, z),
                                   (x, y-1, z),
                                   (x, y, z+1),
                                   (x, y, z-1)]
                    for idx in idxsToCheck:
                        try:
                            curVal = brickFreqMatrix[idx[0]][idx[1]][idx[2]]
                        except IndexError:
                            continue
                        if curVal == round(j + 0.01,2):
                            brickFreqMatrix[x][y][z] = j
                            if faceIdxMatrix: setNF(cm.matShellDepth, j, idx, (x,y,z), faceIdxMatrix)
                            gotOne = True
                            break
        if not gotOne:
            break


def getThreshold(cm):
    """ returns threshold (draw bricks if returned val >= threshold) """
    return 1.01 - (cm.shellThickness / 100)

def createBricksDictEntry(name:str, val:float=0, draw:bool=False, co:tuple=(0, 0, 0), near_face:int=None, near_intersection:str=None, near_normal:tuple=None, rgba:tuple=None, mat_name:str=None, parent:str=None, size:list=None, attempted_merge:bool=False, top_exposed:bool=None, bot_exposed:bool=None, bType:str=None, flipped:bool=False, rotated:bool=False, created_from:str=None):
    """
    create an entry in the dictionary of brick locations

    Keyword Arguments:
    name              -- name of the brick object
    val               -- location of brick in model (0: outside of model, 0.00-1.00: number of bricks away from shell / 100, 1: on shell)
    draw              -- draw the brick in 3D space
    co                -- 1x1 brick centered at this location
    near_face         -- index of nearest face intersection with source mesh
    near_intersection -- coordinate location of nearest intersection with source mesh
    near_normal       -- normal of the nearest face intersection
    rgba              -- [red, green, blue, alpha] values of brick color
    mat_name          -- name of material attributed to bricks at this location
    parent      -- key into brick dictionary with information about the parent brick merged with this one
    size              -- 3D size of brick (e.g. standard 2x4 brick -> [2, 4, 3])
    attempted_merge   -- attempt has been made in makeBricks function to merge this brick with nearby bricks
    top_exposed       -- top of brick is visible to camera
    bot_exposed       -- bottom of brick is visible to camera
    type              -- type of brick
    flipped           -- brick is flipped over non-mirrored axis
    rotated           -- brick is rotated 90 degrees about the Z axis
    created_from      -- key of brick this brick was created from in drawAdjacent

    """
    return {"name":name,
            "val":val,
            "draw":draw,
            "co":co,
            "near_face":near_face,
            "near_intersection":near_intersection,
            "near_normal":near_normal,
            "rgba":rgba,
            "mat_name":mat_name,
            "parent":parent,
            "size":size,
            "attempted_merge":attempted_merge,
            "top_exposed":top_exposed,
            "bot_exposed":bot_exposed,
            "type":bType,
            "flipped":flipped,
            "rotated":rotated,
            "created_from":created_from,
           }

@timed_call('Time Elapsed')
def makeBricksDict(source, source_details, brickScale, origSource, cursorStatus=False):
    """ make dictionary with brick information at each coordinate of lattice surrounding source
    source         -- source object to construct lattice around
    source_details -- object details with subattributes for distance and midpoint of x, y, z axes
    brickScale     -- scale of bricks
    cursorStatus   -- update mouse cursor with status of matrix creation
    """
    scn, cm, n = getActiveContextInfo()
    # get lattice bmesh
    print("\ngenerating blueprint...")
    lScale = source_details.dist
    offset = source_details.mid
    if source.parent:
        offset = offset - source.parent.location
    # get coordinate list from intersections of edges with faces
    coordMatrix = generateLattice(brickScale, lScale, offset)
    if len(coordMatrix) == 0:
        coordMatrix.append(source_details.mid)
    # set calculationAxes
    calculationAxes = cm.calculationAxes if cm.brickShell != "INSIDE" else "XYZ"
    # set up faceIdxMatrix and brickFreqMatrix
    faceIdxMatrix = np.zeros((len(coordMatrix), len(coordMatrix[0]), len(coordMatrix[0][0]))).tolist()
    if cm.isSmoke:
        brickFreqMatrix, rgbaMatrix = getBrickMatrixSmoke(origSource, faceIdxMatrix, cm.brickShell, cursorStatus=cursorStatus)
    else:
        brickFreqMatrix = getBrickMatrix(source, faceIdxMatrix, coordMatrix, cm.brickShell, axes=calculationAxes, cursorStatus=cursorStatus)
        rgbaMatrix = None
    # initialize active keys
    cm.activeKeyX = -1
    cm.activeKeyY = -1
    cm.activeKeyZ = -1

    # create bricks dictionary with brickFreqMatrix values
    i = 0
    bricksDict = {}
    threshold = getThreshold(cm)
    # get uv_texture image and pixels for material calculation
    uv_images = getUVImages(source)
    for x in range(len(coordMatrix)):
        for y in range(len(coordMatrix[0])):
            for z in range(len(coordMatrix[0][0])):
                # skip brickFreqMatrix values set to None
                if brickFreqMatrix[x][y][z] is None:
                    continue

                # initialize variables
                bKey = "{x},{y},{z}".format(x=x, y=y, z=z)
                co = Vector(coordMatrix[x][y][z])
                i += 1

                # get material from nearest face intersection point
                nf = faceIdxMatrix[x][y][z]["idx"] if type(faceIdxMatrix[x][y][z]) == dict else None
                ni = faceIdxMatrix[x][y][z]["loc"] if type(faceIdxMatrix[x][y][z]) == dict else None
                nn = faceIdxMatrix[x][y][z]["normal"] if type(faceIdxMatrix[x][y][z]) == dict else None
                normal_direction = getNormalDirection(nn)
                rgba = rgbaMatrix[x][y][z] if rgbaMatrix else getUVPixelColor(scn, cm, source, nf, ni, uv_images)
                draw = brickFreqMatrix[x][y][z] >= threshold
                # store first key to active keys
                if cm.activeKeyX == -1 and draw:
                    keyVals = bKey.split(",")
                    cm.activeKeyX = int(keyVals[0])
                    cm.activeKeyY = int(keyVals[1])
                    cm.activeKeyZ = int(keyVals[2])
                # create bricksDict entry for current brick
                bricksDict[bKey] = createBricksDictEntry(
                    name= 'Bricker_%(n)s_brick__%(bKey)s' % locals(),
                    val= brickFreqMatrix[x][y][z],
                    draw= draw,
                    co= (co - source_details.mid).to_tuple(),
                    near_face= nf,
                    near_intersection= ni if ni is None else vecToStr(ni),
                    near_normal= normal_direction,
                    rgba= rgba,
                    mat_name= "",  # defined in 'updateMaterials' function
                    bType= "PLATE" if "PLATES" in cm.brickType else ("BRICK" if cm.brickType == "BRICKS" else cm.brickType),
                )
    cm.numBricksGenerated = i

    # return list of created Brick objects
    return bricksDict
