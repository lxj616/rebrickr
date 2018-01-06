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
from .functions import *
from ..caches import rebrickr_bfm_cache
from ...functions import *

def getBricksDict(action, source=None, source_details=None, dimensions=None, R=None, updateCursor=True, curFrame=None, cm=None, restrictContext=False):
    scn = bpy.context.scene
    if cm is None:
        cm = scn.cmlist[scn.cmlist_index]
    loadedFromCache = False
    # if bricksDict can be pulled from cache
    if not cm.matrixIsDirty and not (cm.BFMCache == "" and rebrickr_bfm_cache.get(cm.id) is None) and not (cm.animIsDirty and action == "UPDATE_ANIM"):
        # try getting bricksDict from light cache
        bricksDict = rebrickr_bfm_cache.get(cm.id)
        if bricksDict is None:
            # get bricksDict from deep cache
            bricksDict = json.loads(cm.BFMCache)
        #     print("accessing deep cache")
        # else:
        #     print("accessing light cache")
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
