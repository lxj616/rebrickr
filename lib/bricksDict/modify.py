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
# NONE!

# Blender imports
import bpy

# Rebrickr imports
from ...functions.general import *
from .functions import *


def updateMaterials(bricksDict, source):
    """ sets all matNames in bricksDict based on nearest_face """
    scn, cm, _ = getActiveContextInfo()
    if cm.useUVMap and (len(source.data.uv_layers) > 0 or cm.uvImageName != ""):
        uv_images = getUVImages(source)
    else:
        uv_images = None
    rgba_vals = []
    # clear materials
    for mat in bpy.data.materials:
        if mat.name.startswith("Rebrickr_{}_mat_".format(cm.source_name)):
            bpy.data.materials.remove(mat)
    # get original matNames, and populate rgba_vals
    for key in bricksDict.keys():
        # skip irrelevant bricks
        nf = bricksDict[key]["nearest_face"]
        if not bricksDict[key]["draw"] or nf is None:
            continue
        # get RGBA value at nearest face intersection
        ni = bricksDict[key]["nearest_intersection"]
        rgba, matName = getBrickRGBA(source, nf, ni, uv_images)
        # get material with snapped RGBA value
        if rgba is None:
            matName = ""
        elif snapToBrickColors():
            matName = findNearestBrickColorName(rgba)
        elif cm.colorSnapAmount > 0:
            matName = createNewMaterial(cm.source_name, rgba, rgba_vals)
        rgba_vals.append(rgba)
        bricksDict[key]["mat_name"] = matName
    return bricksDict


def updateBrickSizes(cm, bricksDict, key, keys, loc, brickSizes, zStep, maxL, mergeVertical=False):
    """ update 'brickSizes' with available brick sizes surrounding bricksDict[key] """
    newMax1 = maxL[1]
    newMax2 = maxL[2]
    breakOuter1 = False
    breakOuter2 = False
    for i in range(0, maxL[0]):
        for j in range(0, maxL[1]):
            # break case 1
            if j >= newMax1: break
            # break case 2
            elif not canBeJoined(cm, bricksDict, loc, key, i, j) or listToStr([i + loc[0], j + loc[1], loc[2]]) not in keys:
                if j == 0: breakOuter2 = True
                else:      newMax1 = j
                break
            # else, check vertically
            for k in range(0, maxL[2], zStep):
                # if not 'Bricks and Plates', skip second two iters
                if not mergeVertical and k > 0: continue
                # break case 1
                elif k >= newMax2: break
                # break case 2
                elif not canBeJoined(cm, bricksDict, loc, key, i, j, k) or listToStr([i + loc[0], j + loc[1], loc[2] + k]) not in keys:
                    if k == 0: breakOuter1 = True
                    else:      newMax2 = k
                    break
                # bricks with 2/3 height can't exist
                elif k == 1: continue
                # else, append current brick size to brickSizes
                else:
                    newSize = [i+1, j+1, k+zStep]
                    if newSize not in brickSizes and [newSize[0],newSize[1]] in bpy.props.Rebrickr_legal_brick_sizes[newSize[2]]:
                        brickSizes.append(newSize)
            if breakOuter1: break
        breakOuter1 = False
        if breakOuter2: break


def attemptMerge(cm, bricksDict, key, keys, loc, brickSizes, zStep, randState, preferLargest=False, mergeVertical=True):
    """ attempt to merge bricksDict[key] with adjacent bricks """
    assert len(brickSizes) > 0

    if cm.brickType != "Custom":
        # iterate through adjacent locs to find available brick sizes
        updateBrickSizes(cm, bricksDict, key, keys, loc, brickSizes, zStep, [cm.maxWidth, cm.maxDepth, 3], mergeVertical and cm.brickType == "Bricks and Plates")
        updateBrickSizes(cm, bricksDict, key, keys, loc, brickSizes, zStep, [cm.maxDepth, cm.maxWidth, 3], mergeVertical and cm.brickType == "Bricks and Plates")
        # sort brick types from smallest to largest
        order = randState.randint(0,2)
        if preferLargest:
            brickSizes.sort(key=lambda x: (x[0] * x[1] * x[2]))
        else:
            brickSizes.sort(key=lambda x: (x[2], x[order], x[(order+1)%2]))

    # grab the biggest brick type and store to bricksDict
    brickSize = brickSizes[-1]
    bricksDict[key]["size"] = brickSize

    # Iterate through merged bricks to set brick parents
    startingLoc = sum(loc)
    for x in range(loc[0], brickSize[0] + loc[0]):
        for y in range(loc[1], brickSize[1] + loc[1]):
            for z in range(loc[2], brickSize[2] + loc[2], zStep):
                # get brick at x,y location
                k0 = listToStr([x,y,z])
                curBrick = bricksDict[k0]
                curBrick["attempted_merge"] = True
                 # checks that x,y,z refer to original brick
                if (x + y + z) == startingLoc:
                    # set original brick as parent_brick
                    curBrick["parent_brick"] = "self"
                else:
                    # point deleted brick to original brick
                    curBrick["parent_brick"] = key

    return brickSize


def getBrickExposure(cm, bricksDict, key=None, loc=None):
    """ return top and bottom exposure of brick at 'key' """
    assert key is not None or loc is not None
    # initialize vars
    topExposed = False
    botExposed = False
    zStep = getZStep(cm)
    # initialize parameters unspecified
    if loc is None:
        loc = strToList(key)
    elif key is None:
        key = listToStr(loc)


    # get size of brick and break conditions
    if key not in bricksDict: return None, None
    size = bricksDict[key]["size"]
    if size is None: return None, None

    # set z-indices
    idxZb = loc[2] - 1
    if cm.brickType == "Bricks and Plates" and size[2] == 3:
        idxZa = loc[2] + 3
    else:
        idxZa = loc[2] + 1

    # Iterate through brick locs in size to check top and bottom exposure
    for x in range(loc[0], size[0] + loc[0]):
        for y in range(loc[1], size[1] + loc[1]):
            for z in range(loc[2], size[2] + loc[2], zStep):
                # get brick at x,y,z location
                k0 = listToStr([x,y,z])
                curBrick = bricksDict[k0]
                # check if brick top or bottom is exposed
                if curBrick["val"] != 1 and not (cm.brickType == "Bricks and Plates" and size[2] == 3):
                    continue
                topExposed = checkExposure(bricksDict, x, y, idxZa, 1, ignoredTypes=["STANDARD", "TILE", "SLOPE", "STUD"])
                botExposed = checkExposure(bricksDict, x, y, idxZb, 1, ignoredTypes=["STANDARD", "TILE", "SLOPE_INVERTED"])

    return topExposed, botExposed


def checkExposure(bricksDict, x, y, z, direction:int=1, ignoredTypes=["STANDARD"]):
    isExposed = False
    try:
        valKeysChecked = []
        k0 = listToStr([x,y,z])
        val = bricksDict[k0]["val"]
        parent_key = k0 if bricksDict[k0]["parent_brick"] == "self" else bricksDict[k0]["parent_brick"]
        typ = bricksDict[parent_key]["type"]
        if val == 0 or typ not in ignoredTypes:
            isExposed = True
        # Check bricks on Z axis [above or below depending on 'direction'] this brick until shell (1) hit. If ouside (0) hit first, [top or bottom depending on 'direction'] is exposed
        elif val > 0 and val < 1:
            zz = z
            while val > 0 and val < 1:
                zz += direction
                k1 = listToStr([x,y,zz])
                # NOTE: if key 'k1' does not exist in bricksDict, we will be sent to 'except'
                val = bricksDict[k1]["val"]
                parent_key = k1 if bricksDict[k1]["parent_brick"] == "self" else bricksDict[k1]["parent_brick"]
                typ = bricksDict[parent_key]["type"]
                valKeysChecked.append(k1)
                if val == 0 or typ not in ignoredTypes:
                    isExposed = True
    except KeyError:
        isExposed = True
    # if outside (0) hit before shell (1) [above or below depending on 'direction'] exposed brick, set all inside (0 < x < 1) values in-between to ouside (0)
    if isExposed and len(valKeysChecked) > 0:
        for k in valKeysChecked:
            bricksDict[k]["val"] = 0
    return isExposed


def canBeJoined(cm, bricksDict, loc, key, i, j, k=0):
    curBrickD = bricksDict[key]
    key = listToStr([loc[0] + i, loc[1] + j, loc[2] + k])
    nextBrickD = bricksDict.get(key)
    spotAvail = brickAvail(cm, curBrickD, nextBrickD)
    return spotAvail


def brickAvail(cm, sourceBrick, brick):
    """ check brick is available to merge """
    if not brick:
        return False
    n = cm.source_name
    Rebrickr_internal_mn = "Rebrickr_%(n)s_internal" % locals()
    # This if statement ensures brick is present, brick isn't drawn already, and checks that brick materials match, or mergeInconsistentMats is True, or one of the mats is "" (internal)
    if brick["draw"] and not brick["attempted_merge"] and (sourceBrick["mat_name"] == brick["mat_name"] or sourceBrick["mat_name"] == "" or brick["mat_name"] == "" or cm.mergeInconsistentMats):
        return True
    else:
        return False
