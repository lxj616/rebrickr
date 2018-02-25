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
import copy

# Blender imports
import bpy
from bpy.types import Operator

# Rebrickr imports
from ..undo_stack import *
from ..functions import *
from ...brickify import *
from ...brickify import *
from ....lib.bricksDict.functions import getDictKey
from ....functions import *


class redrawBricks(Operator):
    """redraw selected bricks from bricksDict"""
    bl_idname = "rebrickr.redraw_bricks"
    bl_label = "Redraw Bricks"
    bl_options = {"REGISTER", "UNDO"}

    ################################################
    # Blender Operator methods

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns False) """
        scn = bpy.context.scene
        objs = bpy.context.selected_objects
        # check that at least 1 selected object is a brick
        for obj in objs:
            if obj.isBrick:
                return True
        return False

    def execute(self, context):
        try:
            scn = bpy.context.scene
            selected_objects = bpy.context.selected_objects
            active_obj = scn.objects.active
            initial_active_obj_name = active_obj.name if active_obj else ""

            # initialize objsD (key:cm_idx, val:list of brick objects)
            objsD = createObjsD(selected_objects)

            # iterate through keys in objsD
            for cm_idx in objsD.keys():
                cm = scn.cmlist[cm_idx]
                # get bricksDict from cache
                bricksDict, _ = getBricksDict(cm=cm)
                keysToUpdate = []

                # delete objects to be updated
                for obj in objsD[cm_idx]:
                    delete(obj)

                # add keys for updated objects to simple bricksDict for drawing
                keysToUpdate = [getDictKey(obj.name)[0] for obj in objsD[cm_idx]]

                # draw modified bricks
                drawUpdatedBricks(cm, bricksDict, keysToUpdate)

            # select original brick
            orig_obj = bpy.data.objects.get(initial_active_obj_name)
            if orig_obj: select(orig_obj, active=orig_obj, only=False)
        except:
            handle_exception()
        return {"FINISHED"}

    ################################################
    # initialization method

    def __init__(self):
        pass

    #############################################
