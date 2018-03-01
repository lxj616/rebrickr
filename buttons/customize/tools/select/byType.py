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

# Bricker imports
from ...functions import *
from ....brickify import *
from ....brickify import *
from .....lib.bricksDict.functions import getDictKey
from .....functions import *


class selectBricksByType(Operator):
    """Select bricks of specified type"""
    bl_idname = "bricker.select_bricks_by_type"
    bl_label = "Select Bricks by Type"
    bl_options = {"REGISTER", "UNDO"}

    ################################################
    # Blender Operator methods

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns False) """
        return bpy.props.bricker_initialized

    def execute(self, context):
        try:
            selectBricks(self.objNamesD, self.bricksDicts, brickType=self.brickType, allModels=self.allModels, only=self.only, includeInternals=self.includeInternals)
        except:
            handle_exception()
        return{"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_popup(self, event)

    ################################################
    # initialization method

    def __init__(self):
        objs = bpy.data.objects
        self.objNamesD, self.bricksDicts = createObjNamesAndBricksDictsDs(objs)
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

    ###################################################
