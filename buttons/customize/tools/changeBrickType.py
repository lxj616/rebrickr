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
from ....lib.Brick.legal_brick_sizes import *
from ....functions import *


class changeBrickType(Operator):
    """change brick type of active brick"""
    bl_idname = "rebrickr.change_brick_type"
    bl_label = "Change Brick Type"
    bl_options = {"REGISTER", "UNDO"}

    ################################################
    # Blender Operator methods

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns False) """
        scn = bpy.context.scene
        active_obj = scn.objects.active
        # check active object is not None
        if active_obj is None:
            return False
        # check that active_object is brick
        if not active_obj.isBrick:
            return False
        # get cmlist item referred to by object
        cm = getItemByID(scn.cmlist, active_obj.cmlist_id)
        return True

    def execute(self, context):
        try:
            self.undo_stack.matchPythonToBlenderState()
            if self.orig_undo_stack_length == self.undo_stack.getLength():
                self.undo_stack.undo_push('change_type')
            scn, cm, _ = getActiveContextInfo(self.cm_idx)
            self.undo_stack.iterateStates(cm)
            obj = scn.objects.active
            initial_active_obj_name = obj.name if obj else ""

            # get dict key details of current obj
            dictKey, dictLoc = getDictKey(obj.name)
            x0,y0,z0 = dictLoc
            # get size of current brick (e.g. [2, 4, 1])
            brickSize = self.bricksDict[dictKey]["size"]

            # skip bricks that are already of type self.brickType
            if (self.bricksDict[dictKey]["type"] == self.brickType and
                self.bricksDict[dictKey]["flipped"] == self.flipBrick and
                self.bricksDict[dictKey]["rotated"] == self.rotateBrick):
                return {"CANCELLED"}

            # verify locations above are not obstructed
            if self.brickType in getBrickTypes(height=3) and brickSize[2] == 1:
                for x in range(brickSize[0]):
                    for y in range(brickSize[1]):
                        for z in range(1, 3):
                            curKey = listToStr([x0 + x, y0 + y, z0 + z])
                            if curKey in self.bricksDict and self.bricksDict[curKey]["draw"]:
                                self.report({"INFO"}, "Could not change to type {brickType}; some locations are occupied".format(brickType=self.brickType))
                                self.brickType = self.bricksDict[dictKey]["type"]
                                return {"CANCELLED"}

            # print helpful message to user in blender interface
            self.report({"INFO"}, "turn active {brickSize} brick into {targetType}".format(brickSize=str(brickSize)[1:-1], targetType=self.brickType))

            # set type of parent_brick to self.brickType
            self.bricksDict[dictKey]["type"] = self.brickType
            self.bricksDict[dictKey]["flipped"] = self.flipBrick
            self.bricksDict[dictKey]["rotated"] = self.rotateBrick

            # update height of brick if necessary, and update dictionary accordingly
            if cm.brickType == "BRICKS AND PLATES":
                dimensions = Bricks.get_dimensions(cm.brickHeight, getZStep(cm), cm.gap)
                brickSize = updateBrickSizeAndDict(dimensions, cm, self.bricksDict, brickSize, dictKey, dictLoc, curHeight=brickSize[2], targetType=self.brickType)

            # check if brick spans 3 matrix locations
            bAndPBrick = cm.brickType == "BRICKS AND PLATES" and brickSize[2] == 3

            # verify exposure
            for x in range(brickSize[0]):
                for y in range(brickSize[1]):
                    curLoc = list(Vector(dictLoc) + Vector((x, y, 0)))
                    self.bricksDict = verifyBrickExposureAboveAndBelow(curLoc, self.bricksDict, decriment=2 if bAndPBrick else 0)
                    # add bricks to keysToUpdate
                    keysToUpdate = [getParentKey(self.bricksDict, listToStr([x0 + x, y0 + y, z0 + z])) for z in [-1, 0, 3 if bAndPBrick else 1]]

            # uniquify keysToUpdate and remove null keys
            keysToUpdate = uniquify1(keysToUpdate)
            keysToUpdate = [x for x in keysToUpdate if x != None]

            # delete objects to be updated
            for k1 in keysToUpdate:
                obj0 = bpy.data.objects.get(self.bricksDict[k1]["name"])
                if obj0 is not None:
                    delete(obj0)
            # draw updated brick
            drawUpdatedBricks(cm, self.bricksDict, keysToUpdate, selectCreated=False)
            # select original brick
            orig_obj = bpy.data.objects.get(initial_active_obj_name)
            if orig_obj: select(orig_obj, active=orig_obj, only=False)
            # model is now customized
            cm.customized = True
        except:
            handle_exception()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_popup(self, event)

    ################################################
    # initialization method

    def __init__(self):
        try:
            self.undo_stack = UndoStack.get_instance()
            self.orig_undo_stack_length = self.undo_stack.getLength()
            scn = bpy.context.scene
            obj = scn.objects.active
            # get cmlist item referred to by object
            cm = getItemByID(scn.cmlist, obj.cmlist_id)
            # get bricksDict from cache
            self.bricksDict, _ = getBricksDict(cm=cm)
            dictKey, dictLoc = getDictKey(obj.name)
            # initialize properties
            self.cm_idx = cm.idx
            curBrickType = self.bricksDict[dictKey]["type"]
            curBrickSize = self.bricksDict[dictKey]["size"]
            self.brickType = curBrickType if curBrickType is not None else ("BRICK" if curBrickSize[2] == 3 else "PLATE")
            self.flipBrick = self.bricksDict[dictKey]["flipped"]
            self.rotateBrick = self.bricksDict[dictKey]["rotated"]
        except:
            handle_exception()

    ###################################################
    # class variables

    # vars
    bricksDict = {}
    cm_idx = -1

    # get items for brickType prop
    def get_items(self, context):
        items = getAvailableTypes()
        return items


    # properties
    brickType = bpy.props.EnumProperty(
        name="Brick Type",
        description="Choose what type of brick should be drawn at this location",
        items=get_items,
        default=None)
    flipBrick = bpy.props.BoolProperty(
        name="Flip Brick Orientation",
        description="Flip the brick about the non-mirrored axis",
        default=False)
    rotateBrick = bpy.props.BoolProperty(
        name="Rotate 90 Degrees",
        description="Rotate the brick about the Z axis (brick width & depth must be equivalent)",
        default=False)

    #############################################
