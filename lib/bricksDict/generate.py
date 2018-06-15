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
            if nextIntersection is None:
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

    # run more checks
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
        return -1, None, True
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

    return intersections, nextIntersection, edgeIntersects

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
    dist = coordMatrix[1][1][1] - coordMatrix[0][0][0]
    highEfficiency = cm.insidenessRayCastDir in ["HIGH EFFICIENCY", "XYZ"] and not cm.verifyExposure

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
                nextIntersection = None
                i = 0
                for x in range(len(brickFreqMatrix)):
                    # skip current loc if casting ray is unnecessary (sets outside vals to last found val)
                    if i == 2 and highEfficiency and nextIntersection is not None and coordMatrix[x][y][z].x + dist.x + miniDist.x < nextIntersection.x:
                        brickFreqMatrix[x][y][z] = val
                        continue
                    intersections, nextIntersection, edgeIntersects = updateBFMatrix(scn, cm, x, y, z, coordMatrix, faceIdxMatrix, brickFreqMatrix, brickShell, source, x+1, y, z, miniDist)
                    i = 0 if edgeIntersects else (2 if i == 1 else 1)
                    val = brickFreqMatrix[x][y][z]
                    if intersections == 0:
                        break

    percent1 = percent0
    if "y" in axes:
        miniDist = Vector((0.0, 0.00015, 0.0))
        for z in range(len(brickFreqMatrix[0][0])):
            # print status to terminal
            percent1 = printStatus(percent0, z, len(brickFreqMatrix[0][0]), percent1)
            for x in range(len(brickFreqMatrix)):
                nextIntersection = None
                i = 0
                for y in range(len(brickFreqMatrix[0])):
                    # skip current loc if casting ray is unnecessary (sets outside vals to last found val)
                    if i == 2 and highEfficiency and nextIntersection is not None and coordMatrix[x][y][z].y + dist.y + miniDist.y < nextIntersection.y:
                        if brickFreqMatrix[x][y][z] == 0:
                            brickFreqMatrix[x][y][z] = val
                        if brickFreqMatrix[x][y][z] == val:
                            continue
                    intersections, nextIntersection, edgeIntersects = updateBFMatrix(scn, cm, x, y, z, coordMatrix, faceIdxMatrix, brickFreqMatrix, brickShell, source, x, y+1, z, miniDist)
                    i = 0 if edgeIntersects else (2 if i == 1 else 1)
                    val = brickFreqMatrix[x][y][z]
                    if intersections == 0:
                        break

    percent2 = percent1
    if "z" in axes:
        miniDist = Vector((0.0, 0.0, 0.00015))
        for x in range(len(brickFreqMatrix)):
            # print status to terminal
            percent2 = printStatus(percent1, x, len(brickFreqMatrix), percent2)
            for y in range(len(brickFreqMatrix[0])):
                nextIntersection = None
                i = 0
                for z in range(len(brickFreqMatrix[0][0])):
                    # skip current loc if casting ray is unnecessary (sets outside vals to last found val)
                    if i == 2 and highEfficiency and nextIntersection is not None and coordMatrix[x][y][z].z + dist.z + miniDist.z < nextIntersection.z:
                        if brickFreqMatrix[x][y][z] == 0:
                            brickFreqMatrix[x][y][z] = val
                        if brickFreqMatrix[x][y][z] == val:
                            continue
                    # cast rays and update brickFreqMatrix
                    intersections, nextIntersection, edgeIntersects = updateBFMatrix(scn, cm, x, y, z, coordMatrix, faceIdxMatrix, brickFreqMatrix, brickShell, source, x, y, z+1, miniDist)
                    i = 0 if edgeIntersects else (2 if i == 1 else 1)
                    val = brickFreqMatrix[x][y][z]
                    if intersections == 0:
                        break

    # mark inside freqs as internal (-1) and outside next to outsides for removal
    adjustBFM(brickFreqMatrix, axes=axes)

    # print status to terminal
    updateProgressBars(True, cursorStatus, 1, 0, "Shell", end=True)

    # update internals of brickFreqMatrix
    updateInternals(brickFreqMatrix, cm=cm, faceIdxMatrix=faceIdxMatrix)

    return brickFreqMatrix


def getBrickMatrixSmoke(source, faceIdxMatrix, brickShell, source_details, cursorStatus=False):
    scn, cm, _ = getActiveContextInfo()
    density_grid, flame_grid, color_grid, domain_res, max_res, adapt = getSmokeInfo(source)
    brickFreqMatrix = deepcopy(faceIdxMatrix)
    colorMatrix = deepcopy(faceIdxMatrix)
    old_percent = 0
    brightness = Vector([(cm.smokeBrightness - 1) / 5]*3)
    s = cm.smokeSaturation
    sr = (1 - s) * (0.3086 or 0.2125)
    sg = (1 - s) * (0.6094 or 0.7154)
    sb = (1 - s) * (0.0820 or 0.0721)
    sat_mat = Matrix([[sr + s, sr, sr], [sg, sg + s, sg], [sb, sb, sb + s]])
    step = cm.smokeStep

    # get starting and ending idx
    if adapt:
        source_details_adapt = bounds(source)
        adapt_min = source_details_adapt.min
        adapt_max = source_details_adapt.max
        full_min = source_details.min
        full_max = source_details.max
        full_dist = full_max - full_min
        if 0 in full_dist:
            return brickFreqMatrix, colorMatrix
        start_percent = vec_div(adapt_min - full_min, full_dist)
        end_percent   = vec_div(adapt_max - full_min, full_dist)
        s_idx = [len(faceIdxMatrix) * start_percent.x, len(faceIdxMatrix[0]) * start_percent.y, len(faceIdxMatrix[0][0]) * start_percent.z]
        e_idx = [len(faceIdxMatrix) * end_percent.x,   len(faceIdxMatrix[0]) * end_percent.y,   len(faceIdxMatrix[0][0]) * end_percent.z]
    else:
        s_idx = [0, 0, 0]
        e_idx = [len(faceIdxMatrix), len(faceIdxMatrix[0]), len(faceIdxMatrix[0][0])]

    # get number of iterations from s_idx to e_idx for x, y, z
    d = Vector((int(e_idx[0]) - int(s_idx[0]), int(e_idx[1]) - int(s_idx[1]), int(e_idx[2]) - int(s_idx[2])))
    d = Vector((int(e_idx[0]) - int(s_idx[0]), int(e_idx[1]) - int(s_idx[1]), int(e_idx[2]) - int(s_idx[2])))
    # verify bounding box is larger than 0 in all directions
    if 0 in d:
        return brickFreqMatrix, colorMatrix
    # get x/y/z distances
    xn0 = domain_res[0] / d.x
    yn0 = domain_res[1] / d.y
    zn0 = domain_res[2] / d.z
    denom = d.x * d.y * d.z

    # set up brickFreqMatrix values
    for x in range(int(s_idx[0]), int(e_idx[0])):
        for y in range(int(s_idx[1]), int(e_idx[1])):
            for z in range(int(s_idx[2]), int(e_idx[2])):
                # print status to terminal
                old_percent = updateProgressBars(True, cursorStatus, (x * y * z) / denom, old_percent, "Shell")
                d_acc = 0
                f_acc = 0
                cs_acc = Vector((0, 0, 0))
                cf_acc = Vector((0, 0, 0))
                # get indices for
                x0 = x - int(s_idx[0])
                y0 = y - int(s_idx[1])
                z0 = z - int(s_idx[2])
                xn = [int(xn0 * x0), int(xn0 * (x0 + 1))]
                yn = [int(yn0 * y0), int(yn0 * (y0 + 1))]
                zn = [int(zn0 * z0), int(zn0 * (z0 + 1))]
                xn[1] += 1 if xn[1] - xn[0] == 0 else 0
                yn[1] += 1 if yn[1] - yn[0] == 0 else 0
                zn[1] += 1 if zn[1] - zn[0] == 0 else 0
                xn[1] = xn[1] + 1 if xn[1] == xn[0] and xn[0] < domain_res[0] else xn[1]
                yn[1] = yn[1] + 1 if yn[1] == yn[0] and yn[0] < domain_res[1] else yn[1]
                zn[1] = zn[1] + 1 if zn[1] == zn[0] and zn[0] < domain_res[2] else zn[1]
                ave_denom = 0
                for x1 in range(xn[0], xn[1], step):
                    for y1 in range(yn[0], yn[1], step):
                        for z1 in range(zn[0], zn[1], step):
                            cur_idx = (z1 * domain_res[1] + y1) * domain_res[0] + x1
                            d = density_grid[cur_idx]
                            f = flame_grid[cur_idx]
                            d_acc += d
                            f_acc += f
                            cs_acc += d * Vector((color_grid[cur_idx * 4], color_grid[cur_idx * 4 + 1], color_grid[cur_idx * 4 + 2]))
                            cf_acc += Vector(f * cm.flameIntensity * (cm.flameColor * f))
                            ave_denom += 1
                d_ave = d_acc / ave_denom
                f_ave = f_acc / ave_denom
                alpha = d_ave + f_ave
                cs_ave = cs_acc / (ave_denom * (d_ave if d_ave != 0 else 1))
                cf_ave = cf_acc / (ave_denom * (f_ave if f_ave != 0 else 1))
                c_ave = (cs_ave + cf_ave)
                # add brightness
                c_ave += brightness
                # add saturation
                c_ave = c_ave * sat_mat
                brickFreqMatrix[x][y][z] = 0 if alpha < (1 - cm.smokeDensity) else 1
                colorMatrix[x][y][z] = list(c_ave) + [alpha]

    # mark inside freqs as internal (-1) and outside next to outsides for removal
    adjustBFM(brickFreqMatrix, False)

    # end progress bar
    updateProgressBars(True, cursorStatus, 1, 0, "Shell", end=True)

    # update internals of brickFreqMatrix
    updateInternals(brickFreqMatrix, cm)

    return brickFreqMatrix, colorMatrix


def adjustBFM(brickFreqMatrix, axes=""):
    """ adjust brickFreqMatrix values """
    xL = len(brickFreqMatrix)
    yL = len(brickFreqMatrix[0])
    zL = len(brickFreqMatrix[0][0])
    for x in range(xL):
        for y in range(yL):
            for z in range(zL):
                # if current location is inside (-1) and adjacent location is out of bounds, current location is shell (1)
                if (brickFreqMatrix[x][y][z] == -1 and
                    (("z" not in axes and
                      (z in [0, zL-1] or
                       brickFreqMatrix[x][y][z+1] == 0 or
                       brickFreqMatrix[x][y][z-1] == 0)) or
                     ("y" not in axes and
                      (y in [0, yL-1] or
                       brickFreqMatrix[x][y+1][z] == 0 or
                       brickFreqMatrix[x][y-1][z] == 0)) or
                     ("x" not in axes and
                      (x in [0, xL-1] or
                       brickFreqMatrix[x+1][y][z] == 0 or
                       brickFreqMatrix[x-1][y][z] == 0))
                  )):
                    brickFreqMatrix[x][y][z] = 1
                    # TODO: set faceIdxMatrix value to nearest shell value using some sort of built in nearest poly to point function
                # continue if curLoc is boundary loc
                if (x in [0, xL-1] or y in [0, yL-1] or z in [0, zL-1]):
                    continue
                # # If inside location (-1) intersects outside location (0), make it ouside (0)
                # if (brickFreqMatrix[x][y][z] == -1 and
                #     (brickFreqMatrix[x+1][y][z] == 0 or
                #      brickFreqMatrix[x-1][y][z] == 0 or
                #      brickFreqMatrix[x][y+1][z] == 0 or
                #      brickFreqMatrix[x][y-1][z] == 0 or
                #      brickFreqMatrix[x][y][z+1] == 0 or
                #      brickFreqMatrix[x][y][z-1] == 0)):
                #     brickFreqMatrix[x][y][z] = 0
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
    for x in range(xL):
        for y in range(yL):
            for z in range(zL):
                if (brickFreqMatrix[x][y][z] == 0 and
                    (x == xL - 1 or brickFreqMatrix[x+1][y][z] in [0, None]) and
                    (x == 0 or      brickFreqMatrix[x-1][y][z] in [0, None]) and
                    (y == yL - 1 or brickFreqMatrix[x][y+1][z] in [0, None]) and
                    (y == 0 or      brickFreqMatrix[x][y-1][z] in [0, None]) and
                    (z == zL - 1 or brickFreqMatrix[x][y][z+1] in [0, None]) and
                    (z == 0 or      brickFreqMatrix[x][y][z-1] in [0, None])):
                    brickFreqMatrix[x][y][z] = None


def updateInternals(brickFreqMatrix, cm=None, faceIdxMatrix=None):
    """ set up brickFreqMatrix values for bricks inside shell (-1) """
    j = 1
    # NOTE: Following two lines calculate partial brickFreqMatrix (insideness only calculated as deep as necessary)
    # denom = min([(cm.shellThickness-1), max(len(brickFreqMatrix)-2, len(brickFreqMatrix[0])-2, len(brickFreqMatrix[0][0])-2)])/2
    # for idx in range(cm.shellThickness-1):
    # NOTE: Following two lines calculate full brickFreqMatrix
    denom = max(len(brickFreqMatrix)-2, len(brickFreqMatrix[0])-2, len(brickFreqMatrix[0][0])-2)/2
    old_percent = 0
    old_percent = updateProgressBars(True, False, 0, -1, "Internal")
    for i in range(50):
        j0 = j
        j = round(j-0.01, 2)
        gotOne = False
        for x in range(len(brickFreqMatrix)):
            # print status to terminal
            old_percent = updateProgressBars(True, False, ((i + x / len(brickFreqMatrix)) ** 0.6) / 7.07107, old_percent, "Internal")
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
                        if curVal == j0:
                            brickFreqMatrix[x][y][z] = j
                            if faceIdxMatrix: faceIdxMatrix[x][y][z] = faceIdxMatrix[idx[0]][idx[1]][idx[2]]
                            gotOne = True
                            break
        if not gotOne:
            break
    # end progress bar
    updateProgressBars(True, False, 1, 0, "Internal", end=True)


def getThreshold(cm):
    """ returns threshold (draw bricks if returned val >= threshold) """
    return 1.01 - (cm.shellThickness / 100)

def createBricksDictEntry(name:str, val:float=0, draw:bool=False, co:tuple=(0, 0, 0), near_face:int=None, near_intersection:str=None, near_normal:tuple=None, rgba:tuple=None, mat_name:str="", custom_mat_name:bool=False, parent:str=None, size:list=None, attempted_merge:bool=False, top_exposed:bool=None, bot_exposed:bool=None, obscures:list=[False]*6, bType:str=None, flipped:bool=False, rotated:bool=False, created_from:str=None):
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
    custom_mat_name   -- mat_name was set with 'Change Material' customization tool
    parent            -- key into brick dictionary with information about the parent brick merged with this one
    size              -- 3D size of brick (e.g. standard 2x4 brick -> [2, 4, 3])
    attempted_merge   -- attempt has been made in makeBricks function to merge this brick with nearby bricks
    top_exposed       -- top of brick is visible to camera
    bot_exposed       -- bottom of brick is visible to camera
    obscures          -- obscures neighboring locations [+z, -z, +x, -x, +y, -y]
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
            "custom_mat_name":custom_mat_name,
            "parent":parent,
            "size":size,
            "attempted_merge":attempted_merge,
            "top_exposed":top_exposed,
            "bot_exposed":bot_exposed,
            "obscures":obscures,
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
        brickFreqMatrix, smokeColors = getBrickMatrixSmoke(origSource, faceIdxMatrix, cm.brickShell, source_details, cursorStatus=cursorStatus)
    else:
        brickFreqMatrix = getBrickMatrix(source, faceIdxMatrix, coordMatrix, cm.brickShell, axes=calculationAxes, cursorStatus=cursorStatus)
        smokeColors = None

    # initialize active keys
    cm.activeKey = (-1, -1, -1)

    # create bricks dictionary with brickFreqMatrix values
    i = 0
    bricksDict = {}
    threshold = getThreshold(cm)
    brickType = cm.brickType  # prevents cm.brickType update function from running over and over in for loop
    noOffset = vec_round(offset, precision=5) == Vector((0, 0, 0))
    # get uv_texture image and pixels for material calculation
    ct = time.time()
    uv_images = getUVImages(source)
    for x in range(len(coordMatrix)):
        for y in range(len(coordMatrix[0])):
            for z in range(len(coordMatrix[0][0])):
                # skip brickFreqMatrix values set to None
                if brickFreqMatrix[x][y][z] is None:
                    continue

                # initialize variables
                bKey = "{x},{y},{z}".format(x=x, y=y, z=z)
                co = coordMatrix[x][y][z].to_tuple() if noOffset else (Vector(coordMatrix[x][y][z]) - source_details.mid).to_tuple()
                i += 1

                # get material from nearest face intersection point
                nf = faceIdxMatrix[x][y][z]["idx"] if type(faceIdxMatrix[x][y][z]) == dict else None
                ni = faceIdxMatrix[x][y][z]["loc"].to_tuple() if type(faceIdxMatrix[x][y][z]) == dict else None
                nn = faceIdxMatrix[x][y][z]["normal"] if type(faceIdxMatrix[x][y][z]) == dict else None
                norm_dir = getNormalDirection(nn)
                bType = "PLATE" if brickType == "BRICKS AND PLATES" else (brickType[:-1] if brickType.endswith("S") else ("CUSTOM 1" if brickType == "CUSTOM" else brickType))
                flipped, rotated = getFlipRot("" if norm_dir is None else norm_dir[1:])
                rgba = smokeColors[x][y][z] if smokeColors else getUVPixelColor(scn, cm, source, nf, ni, uv_images)
                draw = brickFreqMatrix[x][y][z] >= threshold
                # ct = stopWatch(1, time.time()-ct, precision=7)
                # create bricksDict entry for current brick
                bricksDict[bKey] = createBricksDictEntry(
                    name= 'Bricker_%(n)s_brick__%(bKey)s' % locals(),
                    val= brickFreqMatrix[x][y][z],
                    draw= draw,
                    co= co,
                    near_face= nf,
                    near_intersection= ni,
                    near_normal= norm_dir,
                    rgba= rgba,
                    # mat_name= "",  # defined in 'updateMaterials' function
                    # obscures= [brickFreqMatrix[x][y][z] != 0]*6,
                    bType= bType,
                    flipped= flipped,
                    rotated= rotated,
                )
                # ct = stopWatch(2, time.time()-ct, precision=7)
    ct = stopWatch(3, time.time()-ct, precision=7)
    cm.numBricksGenerated = i

    # return list of created Brick objects
    return bricksDict
