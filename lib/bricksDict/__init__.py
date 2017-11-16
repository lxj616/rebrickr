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

def getBricksDict(action, source=None, source_details=None, dimensions=None, R=None, updateCursor=None, curFrame=None, cm=None):
    scn = bpy.context.scene
    if cm is None:
        cm = scn.cmlist[scn.cmlist_index]
    useCaching = bpy.context.user_preferences.addons[bpy.props.rebrickr_module_name].preferences.useCaching
    loadedFromCache = False
    # current_source_hash = json.dumps(hash_object(source))
    if useCaching and not cm.matrixIsDirty and cm.BFMCache != "" and not cm.sourceIsDirty and (action != "UPDATE_ANIM" or not cm.animIsDirty):#current_source_hash == cm.source_hash:
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

def cacheBricksDict(action, cm, bricksDict):
    if action in ["CREATE", "UPDATE_MODEL"]:
        # cm.source_hash = current_source_hash
        cm.BFMCache = json.dumps(bricksDict)
    elif action in ["ANIMATE", "UPDATE_ANIM"]:
        if cm.BFMCache == "":
            BFMCache = {}
        else:
            BFMCache = json.loads(cm.BFMCache)
        BFMCache[curFrame] = bricksDict
        cm.BFMCache = json.dumps(BFMCache)
