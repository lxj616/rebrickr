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
    assert loc is not None or key is not None
    if loc is not None:
        x,y,z = loc
    else:
        x,y,z = strToList(key)
    adjKeys = [listToStr([x+1,y,z]),
               listToStr([x-1,y,z]),
               listToStr([x,y+1,z]),
               listToStr([x,y-1,z]),
               listToStr([x,y,z+1]),
               listToStr([x,y,z-1])]
    adjBrickVals = []
    for key in adjKeys.copy():
        try:
            adjBrickVals.append(bricksDict[key]["val"])
        except KeyError:
            adjKeys.remove(key)
    return adjKeys, adjBrickVals

def setCurBrickVal(bricksDict, loc):
    _,adjBrickVals = getAdjKeysAndBrickVals(bricksDict, loc=loc)
    if 0 in adjBrickVals or len(adjBrickVals) == 0 or min(adjBrickVals) == 1:
        newVal = 1
    else:
        highestAdjVal = max(adjBrickVals)
        newVal = highestAdjVal - 0.01
    bricksDict[listToStr(loc)]["val"] = newVal
