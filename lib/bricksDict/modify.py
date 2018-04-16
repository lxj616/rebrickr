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

# Addon imports
from .functions import *
from ..Brick.legal_brick_sizes import *
from ...functions import *


def updateMaterials(bricksDict, source, origSource, curFrame=None):
    """ sets all matNames in bricksDict based on near_face """
    scn, cm, _ = getActiveContextInfo()
    if cm.useUVMap and (len(source.data.uv_layers) > 0 or cm.uvImageName != ""):
        uv_images = getUVImages(source)
    else:
        uv_images = None
    rgba_vals = []
    # clear materials
    mat_name_start = "Bricker_{n}{f}".format(n=cm.source_name, f="f_%(curFrame)s" % locals() if curFrame else "")
    for mat in bpy.data.materials:
        if mat.name.startswith(mat_name_start):
            bpy.data.materials.remove(mat)
    # get original matNames, and populate rgba_vals
    for key in bricksDict.keys():
        # skip irrelevant bricks
        nf = bricksDict[key]["near_face"]
        if not bricksDict[key]["draw"] or (nf is None and not cm.isSmoke):
            continue
        # get RGBA value at nearest face intersection
        if cm.isSmoke:
            rgba = bricksDict[key]["rgba"]
        else:
            ni = strToList(bricksDict[key]["near_intersection"], item_type=float)
            rgba, matName = getBrickRGBA(scn, cm, source, nf, ni, uv_images)
        # get material with snapped RGBA value
        matObj = getMatObject(cm, typ="ABS")
        if rgba is None:
            matName = ""
        elif cm.colorSnap == "ABS" and len(matObj.data.materials) > 0:
            matName = findNearestBrickColorName(rgba, matObj=matObj)
        elif cm.colorSnap == "RGB" or (cm.useUVMap and len(source.data.uv_layers) > 0) or cm.isSmoke:
            matName = createNewMaterial(cm.source_name, rgba, rgba_vals, cm.includeTransparency, curFrame)
        if rgba is not None:
            rgba_vals.append(rgba)
        bricksDict[key]["mat_name"] = matName
    return bricksDict


def updateBrickSizes(cm, bricksDict, key, availableKeys, loc, brickSizes, zStep, maxL, height3Only=False, mergeVertical=False, tallType="BRICK", shortType="PLATE"):
    """ update 'brickSizes' with available brick sizes surrounding bricksDict[key] """
    newMax1 = maxL[1]
    newMax2 = maxL[2]
    breakOuter1 = False
    breakOuter2 = False
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
                # if not mergeVertical, skip second two iters
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
                    if not (newSize[2] == 1 and height3Only) and (not cm.legalBricksOnly or legalBrickSize(s=newSize, t=tallType if newSize[2] == 3 else shortType)):
                        brickSizes.append(newSize)
            if breakOuter1: break
        breakOuter1 = False
        if breakOuter2: break


def attemptMerge(cm, bricksDict, key, availableKeys, defaultSize, zStep, randState, preferLargest=False, mergeVertical=True, targetType=None, height3Only=False):
    """ attempt to merge bricksDict[key] with adjacent bricks """
    # get loc from key
    loc = strToList(key)
    brickSizes = [defaultSize]
    tallType = getTallType(cm, bricksDict[key], targetType)
    shortType = getShortType(cm, bricksDict[key], targetType)

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
    keysInBrick = getKeysInBrick(cm, brickSize, key, loc, zStep)
    for k in keysInBrick:
        bricksDict[k]["attempted_merge"] = True
        bricksDict[k]["parent"] = "self" if k == key else key
        # set brick type if necessary
        if flatBrickType(cm):
            bricksDict[k]["type"] = shortType if brickSize[2] == 1 else tallType
    # set exposure of current [merged] brick
    topExposed, botExposed = getBrickExposure(cm, bricksDict, key)
    bricksDict[key]["top_exposed"] = topExposed
    bricksDict[key]["bot_exposed"] = botExposed
    # set flipped and rotated
    setFlippedAndRotated(bricksDict, key, keysInBrick)
    if bricksDict[key]["type"] == "SLOPE" and cm.brickType == "SLOPES":
        setBrickTypeForSlope(bricksDict, key, keysInBrick)

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
    idxZa = loc[2] + (size[2] if flatBrickType(cm) else 1)

    # Iterate through brick locs in size to check top and bottom exposure
    keysInBrick = getKeysInBrick(cm, size, key, loc, zStep)
    for k in keysInBrick:
        x, y, _ = strToList(k)
        # don't check keys where keys above are in current brick
        if bricksDict[k]["val"] != 1 and not (flatBrickType(cm) and size[2] == 3):
            continue
        # check if brick top or bottom is exposed
        k0 = "{x},{y},{z}".format(x=x, y=y, z=idxZa)
        curTopExposed = checkExposure(bricksDict, k0, 1, obscuringTypes=getTypesObscuringBelow())
        if curTopExposed: topExposed = True
        k1 = "{x},{y},{z}".format(x=x, y=y, z=idxZb)
        curBotExposed = checkExposure(bricksDict, k1, -1, obscuringTypes=getTypesObscuringAbove())
        if curBotExposed: botExposed = True

    return topExposed, botExposed


def checkExposure(bricksDict, key, direction:int=1, obscuringTypes=[]):
    try:
        val = bricksDict[key]["val"]
    except KeyError:
        return True
    parent_key = getParentKey(bricksDict, key)
    typ = bricksDict[parent_key]["type"]
    return val == 0 or typ not in obscuringTypes


def getNumAlignedEdges(cm, bricksDict, size, key, loc, zStep=None):
    numAlignedEdges = 0
    locs = getLocsInBrick(cm, size, key, loc, 1)
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


def getMostCommonDir(i_s, i_e, norms):
    return most_common([n[i_s:i_e] for n in norms])

def setBrickTypeForSlope(bricksDict, key, keysInBrick):
    norms = [bricksDict[k]["near_normal"] for k in keysInBrick if bricksDict[k]["near_normal"] is not None]
    dir0 = getMostCommonDir(0, 1, norms) if len(norms) != 0 else ""
    if (dir0 == "^" and legalBrickSize(s=bricksDict[key]["size"], t="SLOPE") and bricksDict[key]["top_exposed"]):
        typ = "SLOPE"
    elif (dir0 == "v" and legalBrickSize(s=bricksDict[key]["size"], t="SLOPE_INVERTED") and bricksDict[key]["bot_exposed"]):
        typ = "SLOPE_INVERTED"
    else:
        print(1)
        typ = "BRICK"
    bricksDict[key]["type"] = typ


def setFlippedAndRotated(bricksDict, key, keysInBrick):
    norms = [bricksDict[k]["near_normal"] for k in keysInBrick if bricksDict[k]["near_normal"] is not None]

    dir1 = getMostCommonDir(1, 3, norms) if len(norms) != 0 else ""
    flip, rot = getFlipRot(dir1)

    # set flipped and rotated
    bricksDict[key]["flipped"] = flip
    bricksDict[key]["rotated"] = rot
