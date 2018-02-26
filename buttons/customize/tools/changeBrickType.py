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
            scn = bpy.context.scene
            legalBrickSizes = bpy.props.Rebrickr_legal_brick_sizes
            # get original active and selected objects
            active_obj = scn.objects.active
            initial_active_obj_name = active_obj.name if active_obj else ""
            selected_objects = bpy.context.selected_objects
            objNamesToSelect = []
            bricksWereGenerated = False
            brickType = self.brickType

            # iterate through cm_idxs of selected objects
            for cm_idx in self.objNamesD.keys():
                cm = scn.cmlist[cm_idx]
                self.undo_stack.iterateStates(cm)
                # initialize vars
                bricksDict = copy.deepcopy(self.bricksDicts[cm_idx])
                keysToUpdate = []

                # iterate through names of selected objects
                for obj_name in self.objNamesD[cm_idx]:
                    # initialize vars
                    dictKey, dictLoc = getDictKey(obj_name)
                    x0, y0, z0 = dictLoc
                    # get size of current brick (e.g. [2, 4, 1])
                    brickSize = bricksDict[dictKey]["size"]
                    brickType = bricksDict[dictKey]["type"]

                    # skip bricks that are already of type self.brickType
                    if (brickType == self.brickType and
                        bricksDict[dictKey]["flipped"] == self.flipBrick and
                        bricksDict[dictKey]["rotated"] == self.rotateBrick):
                        # return {"CANCELLED"}
                        self.report({"INFO"}, "brick {brickName} is already of type {brickType}".format(brickName=bricksDict[dictKey]["name"], brickType=self.brickType))
                        continue
                    # # skip bricks that can't be turned into the chosen brick type
                    # elif brickSize[:2] not in legalBrickSizes[3 if self.brickType in getBrickTypes(height=3) else 1][self.brickType]:
                    #     continue

                    # verify locations above are not obstructed
                    if self.brickType in getBrickTypes(height=3) and brickSize[2] == 1:
                        aboveKeys = [listToStr([x0 + x, y0 + y, z0 + z]) for z in range(1, 3) for y in range(brickSize[1]) for x in range(brickSize[0])]
                        obstructed = False
                        for curKey in aboveKeys:
                            if curKey in bricksDict and bricksDict[curKey]["draw"]:
                                self.report({"INFO"}, "Could not change to type {brickType}; some locations are occupied".format(brickType=self.brickType))
                                obstructed = True
                                break
                        if obstructed: continue

                    # print helpful message to user in blender interface
                    self.report({"INFO"}, "turn active {brickSize} brick into {targetType}".format(brickSize=str(brickSize)[1:-1], targetType=self.brickType))

                    # set type of parent_brick to self.brickType
                    bricksDict[dictKey]["type"] = self.brickType
                    bricksDict[dictKey]["flipped"] = self.flipBrick
                    bricksDict[dictKey]["rotated"] = self.rotateBrick

                    # update height of brick if necessary, and update dictionary accordingly
                    if "PLATES" in cm.brickType:
                        dimensions = Bricks.get_dimensions(cm.brickHeight, getZStep(cm), cm.gap)
                        brickSize = updateBrickSizeAndDict(dimensions, cm, bricksDict, brickSize, dictKey, dictLoc, curHeight=brickSize[2], targetType=self.brickType)

                    # check if brick spans 3 matrix locations
                    bAndPBrick = "PLATES" in cm.brickType and brickSize[2] == 3

                    # verify exposure
                    brickLocs = [[x0 + x, y0 + y, z0] for y in range(brickSize[1]) for x in range(brickSize[0])]
                    for curLoc in brickLocs:
                        # run verifyBrickExposure
                        bricksDict = verifyBrickExposureAboveAndBelow(curLoc, bricksDict, decriment=2 if bAndPBrick else 0)
                        # add bricks to keysToUpdate
                        keysToUpdate += [getParentKey(bricksDict, listToStr([x0 + x, y0 + y, z0 + z])) for z in [-1, 0, 3 if bAndPBrick else 1] for y in range(brickSize[1]) for x in range(brickSize[0])]
                    objNamesToSelect += [bricksDict[listToStr(loc)]["name"] for loc in brickLocs]

                # uniquify keysToUpdate and remove null keys
                keysToUpdate = uniquify1(keysToUpdate)
                keysToUpdate = [x for x in keysToUpdate if x != None]
                # if something was updated, set bricksWereGenerated
                bricksWereGenerated = bricksWereGenerated or len(keysToUpdate) > 0

                # delete objects to be updated
                for k1 in keysToUpdate:
                    obj0 = bpy.data.objects.get(bricksDict[k1]["name"])
                    if obj0 is not None:
                        delete(obj0)
                # draw updated brick
                drawUpdatedBricks(cm, bricksDict, keysToUpdate, selectCreated=False)
                # model is now customized
                cm.customized = True
            # select original bricks
            orig_obj = bpy.data.objects.get(initial_active_obj_name)
            objsToSelect = [bpy.data.objects.get(n) for n in objNamesToSelect if bpy.data.objects.get(n) is not None]
            select(objsToSelect, active=orig_obj if orig_obj else None, only=False)
            self.brickType = brickType if not bricksWereGenerated else self.brickType
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
            selected_objects = bpy.context.selected_objects
            # get cmlist item referred to by object
            cm = getItemByID(scn.cmlist, obj.cmlist_id)
            # get bricksDict from cache
            bricksDict, _ = getBricksDict(cm=cm)
            dictKey, dictLoc = getDictKey(obj.name)
            # initialize properties
            curBrickType = bricksDict[dictKey]["type"]
            curBrickSize = bricksDict[dictKey]["size"]
            self.brickType = curBrickType if curBrickType is not None else ("BRICK" if curBrickSize[2] == 3 else "PLATE")
            self.flipBrick = bricksDict[dictKey]["flipped"]
            self.rotateBrick = bricksDict[dictKey]["rotated"]
            self.objNamesD, self.bricksDicts = createObjNamesAndBricksDictDs(selected_objects)
        except:
            handle_exception()

    ###################################################
    # class variables

    # vars
    bricksDicts = {}
    bricksDict = {}
    objNamesD = {}

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
