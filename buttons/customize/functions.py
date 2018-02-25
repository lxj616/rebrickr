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
from ...lib.Brick.legal_brick_sizes import *
from .undo_stack import *


def drawUpdatedBricks(cm, bricksDict, keysToUpdate, selectCreated=True):
    if len(keysToUpdate) == 0: return
    if not isUnique(keysToUpdate): raise ValueError("keysToUpdate cannot contain duplicate values")
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


def setCurBrickVal(bricksDict, loc, action="ADD"):
    _, adjBrickVals = getAdjKeysAndBrickVals(bricksDict, loc=loc)
    if action == "ADD" and (0 in adjBrickVals or len(adjBrickVals) == 0 or min(adjBrickVals) == 1):
        newVal = 1
    elif action == "REMOVE" and 0 in adjBrickVals:
        newVal = 0
    elif action == "REMOVE":
        newVal = max(adjBrickVals)
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


def getUsedSizes():
    scn = bpy.context.scene
    items = [("NONE", "None", "")]
    for cm in scn.cmlist:
        sortBy = lambda k: (strToList(k)[2], strToList(k)[0], strToList(k)[1])
        items += [(s, s, "") for s in sorted(cm.brickSizesUsed.split("|"), reverse=True, key=sortBy) if (s, s, "") not in items]
    return items


def getUsedTypes():
    scn = bpy.context.scene
    items = [("NONE", "None", "")]
    for cm in scn.cmlist:
        items += [(t.upper(), t.title(), "") for t in sorted(cm.brickTypesUsed.split("|")) if (t.upper(), t.title(), "") not in items]
    return items


def getAvailableTypes():
    scn, cm, _ = getActiveContextInfo()
    obj = scn.objects.active
    if obj is None: return [("NULL", "Null", "")]
    dictKey, dictLoc = getDictKey(obj.name)
    bricksDict, _ = getBricksDict(cm=cm)
    objSize = bricksDict[dictKey]["size"]
    legalBS = bpy.props.Rebrickr_legal_brick_sizes
    if objSize[2] not in [1, 3]: raise Exception("Custom Error Message: objSize not in [1, 3]")
    # build items
    items = []
    if cm.brickType == "CUSTOM":
        items.append(("CUSTOM", "Custom", ""))
    if objSize[2] == 3 or "BRICKS" in cm.brickType:
        items += [(typ.upper(), typ.title().replace("_", " "), "") for typ in legalBS[3] if objSize[:2] in legalBS[3][typ]]
    if objSize[2] == 1 or "PLATES" in cm.brickType:
        items += [(typ.upper(), typ.title().replace("_", " "), "") for typ in legalBS[1] if objSize[:2] in legalBS[1][typ]]
    items.sort(key=lambda k: k[0])
    return items

def updateBrickSizeAndDict(dimensions, cm, bricksDict, brickSize, key, loc, curHeight=None, curType=None, targetHeight=None, targetType=None):
    brickD = bricksDict[key]
    assert targetHeight is not None or targetType is not None
    if targetHeight is None:
        targetHeight = 1 if targetType in getBrickTypes(height=1) else 3
    assert curHeight is not None or curType is not None
    if curHeight is None:
        curHeight = 1 if curType in getBrickTypes(height=1) else 3
    # adjust brick size if changing type from 3 tall to 1 tall
    if curHeight == 3 and targetHeight == 1:
        brickSize[2] = 1
        for x in range(brickSize[0]):
            for y in range(brickSize[1]):
                for z in range(1, curHeight):
                    newKey = listToStr([loc[0] + x, loc[1] + y, loc[2] + z])
                    bricksDict[newKey]["parent_brick"] = None
                    bricksDict[newKey]["draw"] = False
                    setCurBrickVal(bricksDict, strToList(newKey), action="REMOVE")
    # adjust brick size if changing type from 1 tall to 3 tall
    elif curHeight == 1 and targetHeight == 3:
        brickSize[2] = 3
        full_d = Vector((dimensions["width"], dimensions["width"], dimensions["height"]))
        # update bricks dict entries above current brick
        for x in range(brickSize[0]):
            for y in range(brickSize[1]):
                for z in range(1, targetHeight):
                    newKey = listToStr([loc[0] + x, loc[1] + y, loc[2] + z])
                    # create new bricksDict entry if it doesn't exist
                    if newKey not in bricksDict:
                        bricksDict = createAddlBricksDictEntry(cm, bricksDict, key, newKey, full_d, x, y, z)
                    # update bricksDict entry to point to new brick
                    bricksDict[newKey]["parent_brick"] = key
                    bricksDict[newKey]["draw"] = True
                    bricksDict[newKey]["mat_name"] = brickD["mat_name"] if bricksDict[newKey]["mat_name"] == "" else bricksDict[newKey]["mat_name"]
                    bricksDict[newKey]["nearest_face"] = brickD["nearest_face"] if bricksDict[newKey]["nearest_face"] is None else bricksDict[newKey]["nearest_face"]
                    bricksDict[newKey]["nearest_intersection"] = brickD["nearest_intersection"] if bricksDict[newKey]["nearest_intersection"] is None else bricksDict[newKey]["nearest_intersection"]
                    if bricksDict[newKey]["val"] == 0:
                        setCurBrickVal(bricksDict, strToList(newKey))
    return brickSize


def createAddlBricksDictEntry(cm, bricksDict, source_key, key, full_d, x, y, z):
    brickD = bricksDict[source_key]
    cm.numBricksGenerated += 1
    j = cm.numBricksGenerated
    n = cm.source_name
    newName = "Rebrickr_%(n)s_brick_%(j)s__%(key)s" % locals()
    newCO = list(Vector(brickD["co"]) + vector_mult(Vector((x, y, z)), full_d))
    bricksDict[key] = createBricksDictEntry(
        name=                 newName,
        co=                   newCO,
        nearest_face=         brickD["nearest_face"],
        nearest_intersection= brickD["nearest_intersection"],
        mat_name=             brickD["mat_name"],
    )
    return bricksDict

def createObjNamesAndBricksDictDs(objs):
    objNamesD = {}
    bricksDicts = {}
    # initialize objsD (key:cm_idx, val:list of brick objects)
    objsD = createObjsD(objs)
    for cm_idx in objsD.keys():
        objNamesD[cm_idx] = [obj.name for obj in objsD[cm_idx]]
    # initialize bricksDicts
    scn = bpy.context.scene
    for cm_idx in objsD.keys():
        cm = scn.cmlist[cm_idx]
        # get bricksDict from cache
        bricksDict, _ = getBricksDict(cm=cm)
        # add to bricksDicts
        bricksDicts[cm_idx] = bricksDict
    return objNamesD, bricksDicts
