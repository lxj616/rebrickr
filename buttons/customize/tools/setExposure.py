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


class setExposure(Operator):
    """Set exposure of bricks"""
    bl_idname = "rebrickr.set_exposure"
    bl_label = "Set Exposure"
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
                # get cmlist item referred to by object
                cm = getItemByID(scn.cmlist, obj.cmlist_id)
                if cm.lastBrickType != "CUSTOM":
                    return True
        return False

    def execute(self, context):
        try:
            scn = bpy.context.scene
            selected_objects = bpy.context.selected_objects
            active_obj = scn.objects.active
            initial_active_obj_name = active_obj.name if active_obj else ""

            # iterate through cm_idxs of selected objects
            for cm_idx in self.objNamesD.keys():
                cm = scn.cmlist[cm_idx]
                self.undo_stack.iterateStates(cm)
                bricksDict = copy.deepcopy(self.bricksDicts[cm_idx])
                keysToUpdate = []

                # iterate through names of selected objects
                for obj_name in self.objNamesD[cm_idx]:
                    # get dict key details of current obj
                    dictKey, dictLoc = getDictKey(obj_name)
                    # get size of current brick (e.g. [2, 4, 1])
                    objSize = bricksDict[dictKey]["size"]

                    # delete the current object
                    delete(bpy.data.objects.get(obj_name))

                    # set top as exposed
                    if self.side in ["TOP", "BOTH"]:
                        bricksDict[dictKey]["top_exposed"] = not bricksDict[dictKey]["top_exposed"]
                    # set bottom as exposed
                    if self.side in ["BOTTOM", "BOTH"]:
                        bricksDict[dictKey]["bot_exposed"] = not bricksDict[dictKey]["bot_exposed"]
                    # add curKey to simple bricksDict for drawing
                    keysToUpdate.append(dictKey)

                # draw modified bricks
                drawUpdatedBricks(cm, bricksDict, keysToUpdate)

                # model is now customized
                cm.customized = True
            # select original brick
            orig_obj = bpy.data.objects.get(initial_active_obj_name)
            if orig_obj:
                scn.objects.active = orig_obj
        except:
            handle_exception()
        return {"FINISHED"}

    ################################################
    # initialization method

    def __init__(self):
        scn = bpy.context.scene
        self.undo_stack = UndoStack.get_instance()
        self.undo_stack.undo_push('exposure')
        # initialize bricksDicts
        selected_objects = bpy.context.selected_objects
        self.objNamesD, self.bricksDicts = createObjNamesAndBricksDictDs(selected_objects)

    ###################################################
    # class variables

    # variables
    bricksDicts = {}
    objNamesD = {}

    # properties
    side = bpy.props.EnumProperty(
        items=(("TOP", "Top", ""),
               ("BOTTOM", "Bottom", ""),
               ("BOTH", "Both", ""),),
        default="TOP")

    #############################################
