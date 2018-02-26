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


class splitBricks(Operator):
    """Split selected bricks into 1x1 bricks"""
    bl_idname = "rebrickr.split_bricks"
    bl_label = "Split Brick(s)"
    bl_options = {"REGISTER", "UNDO"}

    ################################################
    # Blender Operator methods

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns False) """
        if not bpy.props.rebrickr_initialized:
            return False
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
        self.splitBricks()
        return{"FINISHED"}

    def invoke(self, context, event):
        """invoke props popup if conditions met"""
        scn = context.scene
        # iterate through cm_ids of selected objects
        for cm_id in self.objNamesD.keys():
            cm = getItemByID(scn.cmlist, cm_id)
            if "PLATES" not in cm.brickType:
                continue
            bricksDict = copy.deepcopy(self.bricksDicts[cm_id])
            # iterate through names of selected objects
            for obj_name in self.objNamesD[cm_id]:
                dictKey, dictLoc = getDictKey(obj_name)
                size = bricksDict[dictKey]["size"]
                if size[2] <= 1:
                    continue
                if size[0] + size[1] > 2:
                    return context.window_manager.invoke_props_popup(self, event)
                else:
                    self.vertical = True
                    self.splitBricks()
                    return {"FINISHED"}
        self.horizontal = True
        self.splitBricks()
        return {"FINISHED"}

    ################################################
    # initialization method

    def __init__(self):
        scn = bpy.context.scene
        self.undo_stack = UndoStack.get_instance()
        self.orig_undo_stack_length = self.undo_stack.getLength()
        self.vertical = False
        self.horizontal = False
        selected_objects = bpy.context.selected_objects
        self.objNamesD, self.bricksDicts = createObjNamesAndBricksDictsDs(selected_objects)

    ###################################################
    # class variables

    # variables
    objNamesD = {}
    bricksDicts = {}

    # properties
    vertical = bpy.props.BoolProperty(
        name="Vertical",
        description="Split brick(s) horizontally",
        default=False)
    horizontal = bpy.props.BoolProperty(
        name="Horizontal",
        description="Split brick(s) vertically",
        default=False)

    #############################################
    # class methods

    def splitBricks(self):
        try:
            self.undo_stack.matchPythonToBlenderState()
            if self.orig_undo_stack_length == self.undo_stack.getLength():
                self.undo_stack.undo_push('split')
            scn = bpy.context.scene
            objsToSelect = []
            # iterate through cm_ids of selected objects
            for cm_id in self.objNamesD.keys():
                cm = getItemByID(scn.cmlist, cm_id)
                self.undo_stack.iterateStates(cm)
                bricksDict = copy.deepcopy(self.bricksDicts[cm_id])
                keysToUpdate = []

                # iterate through names of selected objects
                for obj_name in self.objNamesD[cm_id]:
                    # get dict key details of current obj
                    dictKey, dictLoc = getDictKey(obj_name)
                    x0, y0, z0 = dictLoc
                    # get size of current brick (e.g. [2, 4, 1])
                    brickSize = bricksDict[dictKey]["size"]
                    bricksDict[dictKey]["type"] = "BRICK" if brickSize == 3 else "PLATE"
                    zStep = getZStep(cm)

                    # skip 1x1 bricks
                    if brickSize[0] + brickSize[1] + (brickSize[2] / zStep) == 3:
                        continue

                    if self.vertical or self.horizontal:
                        # delete the current object
                        delete(bpy.data.objects.get(obj_name))
                        # split the bricks in the matrix and set size of active brick's bricksDict entries to 1x1x[lastZSize]
                        splitKeys = Bricks.split(bricksDict, dictKey, loc=dictLoc, cm=cm, v=self.vertical, h=self.horizontal)
                        # append new splitKeys to keysToUpdate
                        keysToUpdate = keysToUpdate + [k for k in splitKeys if k not in keysToUpdate]

                # draw modified bricks
                drawUpdatedBricks(cm, bricksDict, keysToUpdate)

                # model is now customized
                cm.customized = True

                # add selected objects to objects to select at the end
                objsToSelect += bpy.context.selected_objects.copy()
            # select the new objects created
            select(objsToSelect)
        except:
            handle_exception()

    #############################################
