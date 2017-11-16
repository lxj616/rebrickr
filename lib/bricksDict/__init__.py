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
# from ...functions import *
from ...functions.wrappers import timed_call
from ...functions.__init__ import getAction

def getBricksDict(action, source=None, source_details=None, dimensions=None, R=None, updateCursor=None, curFrame=None, cm=None):
    scn = bpy.context.scene
    if cm is None:
        cm = scn.cmlist[scn.cmlist_index]
    useCaching = bpy.context.user_preferences.addons[bpy.props.rebrickr_module_name].preferences.useCaching
    loadedFromCache = False
    # current_source_hash = json.dumps(hash_object(source))
    if useCaching and not cm.matrixIsDirty and (cm.BFMCache != "" or rebrickr_bfm_cache[0] == cm.id) and not cm.sourceIsDirty and (action != "UPDATE_ANIM" or not cm.animIsDirty):#current_source_hash == cm.source_hash:
        if rebrickr_bfm_cache[0] == cm.id:
            bricksDict = rebrickr_bfm_cache[1]
            print("Accessing light cache")
        else:
            print("Accessing deep cache")
            if action == "UPDATE_MODEL":
                bricksDict = json.loads(cm.BFMCache)
            elif action == "UPDATE_ANIM":
                bricksDict = json.loads(cm.BFMCache)[str(curFrame)]
        loadedFromCache = useCaching
    else:
        bricksDict = makeBricksDict(source, source_details, dimensions, R, cursorStatus=updateCursor)
        # after array is stored to cache, update materials
        if len(source.material_slots) > 0:
            bricksDict = addMaterialsToBricksDict(bricksDict, source)
    return bricksDict, loadedFromCache

def lightToDeepCache(rebrickr_bfm_cache):
    # make sure there is something to store to deep cache
    if rebrickr_bfm_cache[0] is None or rebrickr_bfm_cache[1] is None:
        return False
    scn = bpy.context.scene
    # get cmlist item referred to by object
    cm = getItemByID(scn.cmlist, rebrickr_bfm_cache[0])
    # save last cache to cm.BFMCache
    cm.BFMCache = json.dumps(rebrickr_bfm_cache[1])
    return True

def deepToLightCache(rebrickr_bfm_cache, cm=None, cmlist_id=None):
    assert cm is not None or cmlist_id is not None
    if cm is None:
        # get cmlist item according to cmlist_id
        scn = bpy.context.scene
        cm = getItemByID(scn.cmlist, cmlist_id)
    # make sure there is something to store to light cache
    if cm.BFMCache != "":
        bricksDict = json.loads(cm.BFMCache)
        rebrickr_bfm_cache[0] = cm.id
        rebrickr_bfm_cache[1] = bricksDict
        return True
    # there was nothing to store to light cache
    else:
        return False

def cacheBricksDict(action, cm, bricksDict):
    scn = bpy.context.scene
    if action in ["CREATE", "UPDATE_MODEL"]:
        if rebrickr_bfm_cache[0] not in [cm.id, None]:
            lightToDeepCache(rebrickr_bfm_cache)
        rebrickr_bfm_cache[0] = cm.id
        rebrickr_bfm_cache[1] = bricksDict
    elif action in ["ANIMATE", "UPDATE_ANIM"]:
        if rebrickr_bfm_cache[0] not in [cm.id, None]:
            lightToDeepCache(rebrickr_bfm_cache)
        if type(rebrickr_bfm_cache[1]) != dict:
            rebrickr_bfm_cache[1] = {}
        rebrickr_bfm_cache[1][curFrame] = bricksDict
