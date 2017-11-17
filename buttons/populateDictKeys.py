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

# system imports
import time

# Blender imports
import bpy
from mathutils import Vector, Euler
props = bpy.props

# Rebrickr imports
from ..functions import *
from ..lib.bricksDict import *

class RebrickrPopulateDictKeys(bpy.types.Operator):
    """ Populate bricksDict keys (cm.BFMKeys) """                               # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "rebrickr.populate_dict_keys"                                   # unique identifier for buttons and menu items to reference.
    bl_label = "Populate Dict Keys"                                             # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns false) """
        scn = bpy.context.scene
        if scn.cmlist_index == -1:
            return False
        return True

    def execute(self, context):
        try:
            scn = bpy.context.scene
            cm = scn.cmlist[scn.cmlist_index]
            # if cm.animated:
            #     bricksDict,_ = getBricksDict("UPDATE_ANIM", cm=cm)
            #     keys = list(bricksDict.keys())
            #     keys.sort()
            #     # keys = sorted(keys, key=lambda x: [x[4], x[0], x[2]])
            #     animBFMFrame = cm.animBFMFrames.get(scn.frame_current)
            #     if animBFMFrame is None:
            #         cm.animBFMFrames.add().name = scn.frame_current
            #         animBFMFrame = cm.animBFMFrames[scn.frame_current]
            #     for key in keys:
            #         if key not in list(animBFMFrame.keys()):
            #             newKey = animBFMFrame.add().name = key
            # elif cm.modelCreated:
            bricksDict,_ = getBricksDict("UPDATE_MODEL", cm=cm)
            keys = list(bricksDict.keys())
            keys.sort()
            # keys = sorted(keys, key=lambda x: [x[4], x[0], x[2]])
            for key in keys:
                if key not in list(cm.BFMKeys.keys()):
                    newKey = cm.BFMKeys.add().name = key
        except:
            handle_exception()

        return{"FINISHED"}
