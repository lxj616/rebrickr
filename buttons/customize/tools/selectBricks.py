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
from ..functions import *
from ...brickify import *
from ...brickify import *
from ....lib.bricksDict.functions import getDictKey
from ....functions import *


class selectBricksByType(Operator):
    """Select bricks of specified type"""
    bl_idname = "rebrickr.select_bricks_by_type"
    bl_label = "Select Bricks by Type"
    bl_options = {"REGISTER", "UNDO"}

    ################################################
    # Blender Operator methods

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns False) """
        return bpy.props.rebrickr_initialized

    def execute(self, context):
        try:
            scn, cm, _ = getActiveContextInfo()
            selectedSomething = selectBricks(self.objNamesD, self.bricksDicts, brickType=self.brickType, allModels=self.allModels, only=self.only, includeInternals=self.includeInternals)
            # if no brickType bricks exist, remove from cm.brickTypesUsed
            if not selectedSomething and self.brickType != "NONE" and (self.allModels or len(scn.cmlist) == 1):
                # turn brickTypesUsed into list of sizes
                bTU = cm.brickTypesUsed.split("|")
                bTU.remove(self.brickType)
                # convert bTU back to string of sizes split by '|'
                cm.brickTypesUsed = listToStr(bTU, separate_by="|")
        except:
            handle_exception()
        return{"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_popup(self, event)

    ################################################
    # initialization method

    def __init__(self):
        objs = bpy.data.objects
        self.objNamesD, self.bricksDicts = createObjNamesAndBricksDictDs(objs)
        self.brickType = "NONE"

    ###################################################
    # class variables

    # vars
    objNamesD = {}
    bricksDicts = {}

    # get items for brickType prop
    def get_items(self, context):
        items = getUsedTypes()
        return items

    # define props for popup
    brickType = bpy.props.EnumProperty(
        name="By Type",
        description="Select all bricks of specified type",
        items=get_items)
    only = bpy.props.BoolProperty(
        name="Only",
        description="Select only bricks of given type/size",
        default=False)
    allModels = bpy.props.BoolProperty(
        name="All Models",
        description="Select bricks of given type/size from all models in file",
        default=False)
    includeInternals = bpy.props.BoolProperty(
        name="Include Internals",
        description="Include bricks inside shell in selection",
        default=False)


class selectBricksBySize(Operator):
    """Select bricks of specified size"""
    bl_idname = "rebrickr.select_bricks_by_size"
    bl_label = "Select Bricks by Size"
    bl_options = {"REGISTER", "UNDO"}

    ################################################
    # Blender Operator methods

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns False) """
        return bpy.props.rebrickr_initialized

    def execute(self, context):
        try:
            scn, cm, _ = getActiveContextInfo()
            selectedSomething = selectBricks(self.objNamesD, self.bricksDicts, brickSize=self.brickSize, allModels=self.allModels, only=self.only, includeInternals=self.includeInternals)
            # if no brickSize bricks exist, remove from cm.brickSizesUsed
            if not selectedSomething and self.brickSize != "NONE" and (self.allModels or len(scn.cmlist) == 1):
                # turn brickSizesUsed into list of sizes
                bSU = cm.brickSizesUsed.split("|")
                bSU.remove(self.brickSize)
                # convert bSU back to string of sizes split by '|'
                cm.brickSizesUsed = listToStr(bSU, separate_by="|")
        except:
            handle_exception()
        return{"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_popup(self, event)

    ################################################
    # initialization method

    def __init__(self):
        objs = bpy.data.objects
        self.objNamesD, self.bricksDicts = createObjNamesAndBricksDictDs(objs)
        self.brickSize = "NONE"

    ###################################################
    # class variables

    # vars
    objNamesD = {}
    bricksDicts = {}

    # get items for brickSize prop
    def get_items(self, context):
        items = getUsedSizes()
        return items

    brickSize = bpy.props.EnumProperty(
        name="By Size",
        description="Select all bricks of specified size (X, Y, Z)",
        items=get_items)
    only = bpy.props.BoolProperty(
        name="Only",
        description="Select only bricks of given type/size",
        default=False)
    allModels = bpy.props.BoolProperty(
        name="All Models",
        description="Select bricks of given type/size from all models in file",
        default=False)
    includeInternals = bpy.props.BoolProperty(
        name="Include Internals",
        description="Include bricks inside shell in selection",
        default=False)


def selectBricks(objNamesD, bricksDicts, brickSize="NONE", brickType="NONE", allModels=False, only=False, includeInternals=False):
    scn = bpy.context.scene
    selectedSomething = False
    # split all bricks in objNamesD[cm_idx]
    for cm_idx in objNamesD.keys():
        if not (cm_idx == scn.cmlist_index or allModels):
            continue
        cm = scn.cmlist[cm_idx]
        bricksDict = bricksDicts[cm_idx]

        for obj_name in objNamesD[cm_idx]:
            # get dict key details of current obj
            dictKey, dictLoc = getDictKey(obj_name)
            siz = bricksDict[dictKey]["size"]
            sizeStr = listToStr(sorted(siz[:2]) + [siz[2]])
            typ = bricksDict[dictKey]["type"]
            onShell = bricksDict[dictKey]["val"] == 1
            # get current brick object
            curObj = bpy.data.objects.get(obj_name)
            # if curObj is None:
            #     continue
            # select brick
            if (sizeStr == brickSize or typ == brickType) and (includeInternals or onShell):
                selectedSomething = True
                curObj.select = True
            elif only:
                curObj.select = False
    return selectedSomething
