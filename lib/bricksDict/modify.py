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

# Bricker imports
from .functions import *
from ..Brick.legal_brick_sizes import *
from ...functions.general import *
from ...functions.wrappers import *


def updateMaterials(bricksDict, source):
    """ sets all matNames in bricksDict based on near_face """
    scn, cm, _ = getActiveContextInfo()
    if cm.useUVMap and (len(source.data.uv_layers) > 0 or cm.uvImageName != ""):
        uv_images = getUVImages(source)
    else:
        uv_images = None
    rgba_vals = []
    # clear materials
    for mat in bpy.data.materials:
        if mat.name.startswith("Bricker_{}_mat_".format(cm.source_name)):
            bpy.data.materials.remove(mat)
    # get original matNames, and populate rgba_vals
    for key in bricksDict.keys():
        # skip irrelevant bricks
        nf = bricksDict[key]["near_face"]
        if not bricksDict[key]["draw"] or nf is None:
            continue
        # get RGBA value at nearest face intersection
        ni = bricksDict[key]["near_intersection"]
        rgba, matName = getBrickRGBA(source, nf, ni, uv_images)
        # get material with snapped RGBA value
        if rgba is None:
            matName = ""
        elif cm.colorSnap == "ABS" and brick_materials_loaded():
            matName = findNearestBrickColorName(rgba)
        elif cm.colorSnap == "RGB" or (cm.useUVMap and len(source.data.uv_layers) > 0):
            matName = createNewMaterial(cm.source_name, rgba, rgba_vals)
        if rgba is not None:
            rgba_vals.append(rgba)
        bricksDict[key]["mat_name"] = matName
    return bricksDict


# @timed_call('updateSizes', precision=5)
def updateBrickSizes(cm, bricksDict, key, availableKeys, loc, brickSizes, zStep, maxL, height3Only=False, mergeVertical=False, tallType="BRICK", shortType="PLATE"):
    """ update 'brickSizes' with available brick sizes surrounding bricksDict[key] """
    newMax1 = maxL[1]
    newMax2 = maxL[2]
    breakOuter1 = False
    breakOuter2 = False
    # return
    for i in range(maxL[0]):
        for j in range(maxL[1]):
            # break case 1
            if j >= newMax1: break
            # break case 2
            key1 = listToStr([loc[0] + i, loc[1] + j, loc[2]])
            if not brickAvail(cm, bricksDict[key], bricksDict.get(key1)) or key1 not in availableKeys:
                if j == 0: breakOuter2 = True
                else:      newMax1 = j
                break
            # else, check vertically
            for k in range(0, maxL[2], zStep):
                # if "PLATES" not in cm.brickType, skip second two iters
                if not mergeVertical and k > 0: continue
                # break case 1
                elif k >= newMax2: break
                # break case 2
                key2 = listToStr([loc[0] + i, loc[1] + j, loc[2] + k])
                if not brickAvail(cm, bricksDict[key], bricksDict.get(key2)) or key2 not in availableKeys:
                    if k == 0: breakOuter1 = True
                    else:      newMax2 = k
                    break
                # bricks with 2/3 height can't exist
                elif k == 1: continue
                # else, append current brick size to brickSizes
                else:
                    newSize = [i+1, j+1, k+zStep]
                    if newSize in brickSizes:
                        continue
                    if not (newSize[2] == 1 and height3Only) and newSize[:2] in bpy.props.Bricker_legal_brick_sizes[newSize[2]][tallType if newSize[2] == 3 else shortType]:
                        brickSizes.append(newSize)
            if breakOuter1: break
        breakOuter1 = False
        if breakOuter2: break


def attemptMerge(cm, bricksDict, key, availableKeys, defaultSize, zStep, randState, preferLargest=False, mergeVertical=True, shortType="PLATE", tallType="BRICK", height3Only=False):
    """ attempt to merge bricksDict[key] with adjacent bricks """
    # get loc from key
    loc = strToList(key)
    brickSizes = [defaultSize]

    if cm.brickType != "CUSTOM":
        # check width-depth and depth-width
        for i in [1, -1] if cm.maxWidth != cm.maxDepth else [1]:
            # iterate through adjacent locs to find available brick sizes
            updateBrickSizes(cm, bricksDict, key, availableKeys, loc, brickSizes, zStep, [cm.maxWidth, cm.maxDepth][::i] + [3], height3Only, mergeVertical and "PLATES" in cm.brickType, tallType=tallType, shortType=shortType)
        # sort brick types from smallest to largest
        order = randState.randint(0,2)
        brickSizes.sort(key=lambda x: (x[0] * x[1] * x[2]) if preferLargest else (x[2], x[order], x[(order+1)%2]))

    # grab the biggest brick size and store to bricksDict
    brickSize = brickSizes[-1]
    bricksDict[key]["size"] = brickSize

    # set attributes for merged brick keys
    keysInBrick = getKeysInBrick(brickSize, key, loc, zStep)
    for k in keysInBrick:
        bricksDict[k]["attempted_merge"] = True
        bricksDict[k]["parent"] = "self" if k == key else key
        # set brick type if necessary
        if "PLATES" in cm.brickType:
            bricksDict[k]["type"] = shortType if brickSize[2] == 1 else tallType

    return brickSize


def getBrickExposure(cm, bricksDict, key=None, loc=None):
    """ return top and bottom exposure of brick at 'key' """
    assert key is not None or loc is not None
    # initialize vars
    topExposed = False
    botExposed = False
    zStep = getZStep(cm)
    # initialize parameters unspecified
    loc = loc or strToList(key)
    key = key or listToStr(loc)

    # get size of brick and break conditions
    if key not in bricksDict: return None, None
    size = bricksDict[key]["size"]
    if size is None: return None, None

    # set z-indices
    idxZb = loc[2] - 1
    idxZa = loc[2] + (size[2] if "PLATES" in cm.brickType else 1)

    # Iterate through brick locs in size to check top and bottom exposure
    keysInBrick = getKeysInBrick(size, key, loc, zStep)
    for k in keysInBrick:
        x, y, z = strToList(k)
        # check if brick top or bottom is exposed
        if bricksDict[k]["val"] != 1 and not ("PLATES" in cm.brickType and size[2] == 3):
            continue
        returnVal0 = checkExposure(bricksDict, x, y, idxZa, 1, ignoredTypes=getTypesObscuringBelow())
        if returnVal0: topExposed = True
        returnVal1 = checkExposure(bricksDict, x, y, idxZb, 1, ignoredTypes=getTypesObscuringAbove())
        if returnVal1: botExposed = True

    return topExposed, botExposed


def checkExposure(bricksDict, x, y, z, direction:int=1, ignoredTypes=[]):
    isExposed = False
    try:
        valKeysChecked = []
        k0 = listToStr([x,y,z])
        val = bricksDict[k0]["val"]
        parent_key = getParentKey(bricksDict, k0)
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
                parent_key = getParentKey(bricksDict, k1)
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


def getNumAlignedEdges(bricksDict, size, key, loc, zStep=None):
    numAlignedEdges = 0
    locs = getLocsInBrick(size, key, loc, 1)
    gotOne = False

    for l in locs:
        l[2] -= 1
        k = listToStr(l)
        if k not in bricksDict:
            continue
        p_brick = bricksDict[k]["parent"]
        if p_brick == "self":
            p_brick = k
        if p_brick is None:
            continue
        gotOne = True
        p_brick_sz = bricksDict[p_brick]["size"]
        # -X side
        if l[0] == loc[0] and strToList(p_brick)[0] == l[0]:
            numAlignedEdges += 1
        # -Y side
        if l[1] == loc[1] and strToList(p_brick)[1] == l[1]:
            numAlignedEdges += 1
        # +X side
        if l[0] == loc[0] + size[0] - 1 and strToList(p_brick)[0] + p_brick_sz[0] - 1 == l[0]:
            numAlignedEdges += 1
        # +Y side
        if l[1] == loc[1] + size[1] - 1 and strToList(p_brick)[1] + p_brick_sz[1] - 1 == l[1]:
            numAlignedEdges += 1

    if not gotOne:
        numAlignedEdges = size[0] * size[1] * 4

    return numAlignedEdges


def brickAvail(cm, sourceBrick, brick):
    """ check brick is available to merge """
    if brick is None:
        return False
    # returns True if brick is present, brick isn't drawn already, and brick materials match or mergeInconsistentMats is True, or one of the mats is "" (internal)
    return brick["draw"] and not brick["attempted_merge"] and (sourceBrick["mat_name"] == brick["mat_name"] or sourceBrick["mat_name"] == "" or brick["mat_name"] == "" or cm.mergeInconsistentMats or cm.materialType == "NONE")
