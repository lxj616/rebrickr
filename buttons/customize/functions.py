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
from bpy.types import Operator

# Rebrickr imports
from ...functions import *
from ..brickify import *
from ..brickify import *
from ...lib.bricksDict.functions import getDictKey
from .undo_stack import *


def drawUpdatedBricks(cm, bricksDict, keysToUpdate, selectCreated=True):
    if len(keysToUpdate) == 0: return
    print("redrawing...")
    # get arguments for createNewBricks
    n = cm.source_name
    source = bpy.data.objects.get(n + " (DO NOT RENAME)")
    source_details, dimensions = getDetailsAndBounds(source)
    Rebrickr_parent_on = "Rebrickr_%(n)s_parent" % locals()
    parent = bpy.data.objects.get(Rebrickr_parent_on)
    refLogo = RebrickrBrickify.getLogo(cm)
    action = "UPDATE_MODEL"
    # actually draw the bricks
    RebrickrBrickify.createNewBricks(source, parent, source_details, dimensions, refLogo, action, cm=cm, bricksDict=bricksDict, keys=keysToUpdate, replaceExistingGroup=False, selectCreated=selectCreated, printStatus=False, redraw=True)


def createObjsD(objs):
    scn = bpy.context.scene
    # initialize objsD
    objsD = {}
    # fill objsD with selected_objects
    for obj in objs:
        if obj.isBrick:
            # get cmlist item referred to by object
            cm = getItemByID(scn.cmlist, obj.cmlist_id)
            # add object to objsD
            if cm.idx not in objsD:
                objsD[cm.idx] = [obj]
            else:
                objsD[cm.idx].append(obj)
    return objsD


def getAdjKeysAndBrickVals(bricksDict, loc=None, key=None):
    assert loc or key
    if loc:
        x, y, z = loc
    else:
        x, y, z = strToList(key)
    adjKeys = [listToStr([x+1, y, z]),
               listToStr([x-1, y, z]),
               listToStr([x, y+1, z]),
               listToStr([x, y-1, z]),
               listToStr([x, y, z+1]),
               listToStr([x, y, z-1])]
    adjBrickVals = []
    for key in adjKeys.copy():
        try:
            adjBrickVals.append(bricksDict[key]["val"])
        except KeyError:
            adjKeys.remove(key)
    return adjKeys, adjBrickVals


def setCurBrickVal(bricksDict, loc):
    _, adjBrickVals = getAdjKeysAndBrickVals(bricksDict, loc=loc)
    if 0 in adjBrickVals or len(adjBrickVals) == 0 or min(adjBrickVals) == 1:
        newVal = 1
    else:
        highestAdjVal = max(adjBrickVals)
        newVal = highestAdjVal - 0.01
    bricksDict[listToStr(loc)]["val"] = newVal


def verifyBrickExposureAboveAndBelow(origLoc, bricksDict, decriment=0, zNeg=False, zPos=False):
    scn, cm, _ = getActiveContextInfo()
    dictLocs = []
    if not zNeg:
        dictLocs.append([origLoc[0], origLoc[1], origLoc[2] + decriment + 1])
    if not zPos:
        dictLocs.append([origLoc[0], origLoc[1], origLoc[2] - 1])
    # double check exposure of bricks above/below new adjacent brick
    for dictLoc in dictLocs:
        k = listToStr(dictLoc)
        if k not in bricksDict:
            continue
        parent_key = k if bricksDict[k]["parent_brick"] == "self" else bricksDict[k]["parent_brick"]
        if parent_key is not None:
            topExposed, botExposed = getBrickExposure(cm, bricksDict, k, loc=dictLoc)
            bricksDict[parent_key]["top_exposed"] = topExposed
            bricksDict[parent_key]["bot_exposed"] = botExposed
    return bricksDict


def getAvailableTypes():
    scn, cm, _ = getActiveContextInfo()
    obj = scn.objects.active
    if obj is None: return [("NULL", "Null", "")]
    dictKey, dictLoc = getDictKey(obj.name)
    bricksDict, _ = getBricksDict(cm=cm)
    objSize = bricksDict[dictKey]["size"]
    items = []
    if objSize[2] not in [1, 3]: raise Exception("Custom Error Message: objSize not in [1, 3]")
    # build items
    if cm.brickType == "CUSTOM":
        items.append(("CUSTOM", "Custom", ""))
    if objSize[2] == 3:
        items.append(("BRICK", "Brick", ""))
        if "PLATES" in cm.brickType:
            items.append(("PLATE", "Plate", ""))
    elif objSize[2] == 1:
        items.append(("PLATE", "Plate", ""))
        if "BRICKS" in cm.brickType and "BRICK" not in items:
            items.append(("BRICK", "Brick", ""))
    # add more available brick types
    # NOTE: update the following functions when including brand new type in code:
    # get1HighTypes, get3HighTypes, getTypesObscuringAbove, getTypesObscuringBelow
    if objSize[2] == 3 or "BRICKS" in cm.brickType:
        if (objSize[2] == 3 and (sum(objSize[:2]) in range(3,8))):
            items.append(("SLOPE", "Slope", ""))
        # if sum(objSize[:2]) in range(3,6):
        #     items.append(("SLOPE_INVERTED", "Slope Inverted", ""))
        if sum(objSize[:2]) == 2:
            items.append(("CYLINDER", "Cylinder", ""))
            items.append(("CONE", "Cone", ""))
        #     items.append(("BRICK_STUD_ON_ONE_SIDE", "Brick Stud on One Side", ""))
        #     items.append(("BRICK_INSET_STUD_ON_ONE_SIDE", "Brick Stud on One Side", ""))
        #     items.append(("BRICK_STUD_ON_TWO_SIDES", "Brick Stud on Two Sides", ""))
        #     items.append(("BRICK_STUD_ON_ALL_SIDES", "Brick Stud on All Sides", ""))
        # if sum(objSize[:2]) == 3:
        #     items.append(("TILE_WITH_HANDLE", "Tile with Handle", ""))
        #     items.append(("BRICK_PATTERN", "Brick Pattern", ""))
        # if objSize[0] == 2 and objSize[1] == 2:
        #     items.append(("DOME", "Dome", ""))
        #     items.append(("DOME_INVERTED", "Dome Inverted", ""))
    # Plates
    if objSize[2] == 1 or "PLATES" in cm.brickType:
        if sum(objSize[:2]) == 2:
            items.append(("STUD", "Stud", ""))
            items.append(("STUD_HOLLOW", "Stud (hollow)", ""))
            # items.append(("ROUNDED_TILE", "Rounded Tile", ""))
    #     if sum(objSize[:2]) in [2, 3]:
    #         items.append(("SHORT_SLOPE", "Short Slope", ""))
    #     if objSize[:2] in bpy.props.Rebrickr_legal_brick_sizes[0.9]:
    #         items.append(("TILE", "Tile", ""))
    #     if sum(objSize[:2]) == 3:
    #         items.append(("TILE_GRILL", "Tile Grill", ""))
    #     if objSize[0] == 2 and objSize[1] == 2:
    #         items.append(("TILE_ROUNDED", "Tile Rounded", ""))
    #         items.append(("PLATE_ROUNDED", "Plate Rounded", ""))
    #         items.append(("DOME", "Dome", ""))
    #     if ((objSize[0] == 2 and objSize[1] in [3,4]) or
    #        (objSize[1] == 2 and objSize[0] in [3,4]) or
    #        (objSize[0] == 3 and objSize[1] in [6,8,12]) or
    #        (objSize[1] == 3 and objSize[0] in [6,8,12]) or
    #        (objSize[0] == 4 and objSize[1] == 4) or
    #        (objSize[0] == 6 and objSize[1] == 12) or
    #        (objSize[1] == 6 and objSize[0] == 12) or
    #        (objSize[0] == 7 and objSize[1] == 12) or
    #        (objSize[1] == 7 and objSize[0] == 12)):
    #         items.append(("WING", "Wing", ""))
    # 1x2 brick pattern Brick

    return items
