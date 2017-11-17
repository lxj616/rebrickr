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
import json

# Blender imports
import bpy

# Rebrickr imports
from .generate import *
from .modify import *
from ..caches import rebrickr_bfm_cache
from ...functions import *

def getDetailsAndBounds(source, skipDimensions=False):
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    # get dimensions and bounds
    source_details = bounds(source)
    if not skipDimensions:
        if cm.brickType == "Plates" or cm.brickType == "Bricks and Plates":
            zScale = 0.333
        elif cm.brickType in ["Bricks", "Custom"]:
            zScale = 1
        dimensions = Bricks.get_dimensions(cm.brickHeight, zScale, cm.gap)
        return source_details, dimensions
    else:
        return source_details


def getArgumentsForBricksDict(cm, source=None, source_details=None, dimensions=None):
    if source is None:
        source = bpy.data.objects.get(cm.source_name)
        if source is None: source = bpy.data.objects.get(cm.source_name + " (DO NOT RENAME)")
    if source_details is None or dimensions is None:
        source_details, dimensions = getDetailsAndBounds(source)
    if cm.brickType == "Custom":
        scn = bpy.context.scene
        customObj = bpy.data.objects[cm.customObjectName]
        oldLayers = list(scn.layers) # store scene layers for later reset
        scn.layers = customObj.layers # set scene layers to customObj layers
        select(customObj, active=customObj)
        bpy.ops.object.duplicate()
        customObj0 = scn.objects.active
        select(customObj0, active=customObj0)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        customObj_details = bounds(customObj0)
        customData = customObj0.data
        bpy.data.objects.remove(customObj0, True)
        scale = cm.brickHeight/customObj_details.z.distance
        R = ((scale * customObj_details.x.distance + dimensions["gap"]) * cm.distOffsetX,
             (scale * customObj_details.y.distance + dimensions["gap"]) * cm.distOffsetY,
             (scale * customObj_details.z.distance + dimensions["gap"]) * cm.distOffsetZ)
        scn.layers = oldLayers
    else:
        customData = None
        customObj_details = None
        R = (dimensions["width"] + dimensions["gap"],
             dimensions["width"] + dimensions["gap"],
             dimensions["height"]+ dimensions["gap"])
    return source, source_details, dimensions, R, customData, customObj_details

def getBricksDict(action, source=None, source_details=None, dimensions=None, R=None, updateCursor=True, curFrame=None, cm=None, restrictContext=False):
    scn = bpy.context.scene
    if cm is None:
        cm = scn.cmlist[scn.cmlist_index]
    loadedFromCache = False
    # if bricksDict can be pulled from cache
    if not cm.matrixIsDirty and (cm.BFMCache != "" or rebrickr_bfm_cache.get(cm.id) is not None) and not cm.sourceIsDirty and (action != "UPDATE_ANIM" or not cm.animIsDirty):
        # try getting bricksDict from light cache
        bricksDict = rebrickr_bfm_cache.get(cm.id)
        if bricksDict is None:
            # get bricksDict from deep cache
            print("Accessing deep cache")
            bricksDict = json.loads(cm.BFMCache)
        else:
            print("Accessing light cache")
        loadedFromCache = True
        # if animated, index into that dict
        if action == "UPDATE_ANIM":
            if curFrame is None:
                curFrame = scn.frame_current
            bricksDict = bricksDict[str(curFrame)]
    # if context restricted, return nothing
    elif restrictContext:
        return None, False
    # else, new bricksDict must be created
    else:
        # get arguments for makeBricksDict function call
        if source is None or source_details is None or dimensions is None or R is None:
            source, source_details, dimensions, R,_,_ = getArgumentsForBricksDict(cm)
        # create new bricksDict
        bricksDict = makeBricksDict(source, source_details, dimensions, R,  cursorStatus=updateCursor)
        # add materials to bricksDict
        if len(source.material_slots) > 0:
            bricksDict = addMaterialsToBricksDict(bricksDict, source)
    return bricksDict, loadedFromCache

def lightToDeepCache(rebrickr_bfm_cache):
    scn = bpy.context.scene
    numPushedIDs = 0
    for cmlist_id in rebrickr_bfm_cache.keys():
        # get cmlist item referred to by object
        cm = getItemByID(scn.cmlist, cmlist_id)
        if cm is not None:
            # save last cache to cm.BFMCache
            cm.BFMCache = json.dumps(rebrickr_bfm_cache[cmlist_id])
            numPushedIDs += 1
    if numPushedIDs > 0:
        print("pushed {numKeys} dicts from light cache to deep cache".format(numKeys=numPushedIDs))

def deepToLightCache(rebrickr_bfm_cache):
    scn = bpy.context.scene
    numpulledIDs = 0
    for cm in scn.cmlist:
        # make sure there is something to store to light cache
        if cm.BFMCache != "":
            bricksDict = json.loads(cm.BFMCache)
            rebrickr_bfm_cache[cm.id] = bricksDict
            numpulledIDs += 1
    if numpulledIDs > 0:
        print("pulled {numKeys} dicts from deep cache to light cache".format(numKeys=numpulledIDs))

def cacheBricksDict(action, cm, bricksDict, curFrame=None):
    scn = bpy.context.scene
    if action in ["CREATE", "UPDATE_MODEL"]:
        rebrickr_bfm_cache[cm.id] = bricksDict
    elif action in ["ANIMATE", "UPDATE_ANIM"]:
        if (cm.id not in rebrickr_bfm_cache.keys() or
           type(rebrickr_bfm_cache[cm.id]) != dict):
            rebrickr_bfm_cache[cm.id] = {}
        rebrickr_bfm_cache[cm.id][str(curFrame)] = bricksDict
