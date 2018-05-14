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
import time
import os

# Blender imports
import bpy

# Addon imports
from ..functions import *
from ..ui.cmlist_actions import *


class bakeModel(bpy.types.Operator):
    """Convert model from Bricker model to standard Blender object (source object will be lost)"""
    bl_idname = "bricker.bake_model"
    bl_label = "Bake Model"
    bl_options = {"REGISTER", "UNDO"}

    ################################################
    # Blender Operator methods

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns false) """
        scn = context.scene
        try:
            cm = scn.cmlist[scn.cmlist_index]
        except IndexError:
            return False
        n = cm.source_name
        if cm.modelCreated:
            return True
        return False

    def execute(self, context):
        scn, cm, n = getActiveContextInfo()
        # delete parent/source/dup
        objsToDelete = [bpy.data.objects.get("Bricker_%(n)s_parent" % locals()),
                        bpy.data.objects.get(n),
                        bpy.data.objects.get("%(n)s_duplicate" % locals())]
        for obj in objsToDelete:
            bpy.data.objects.remove(obj, do_unlink=True)
        # set isBrick/isBrickifiedObject to False
        bricks = getBricks()
        select(bricks, only=True)
        if cm.lastSplitModel:
            for brick in bricks:
                brick.isBrick = False
                brick.name = brick.name[8:]
        else:
            bricks[0].isBrickifiedObject = False
            bricks[0].name = "%(n)s_bricks" % locals()
        # delete brick group
        Bricker_bricks_gn = "Bricker_%(n)s_bricks" % locals()
        brickGroup = bpy.data.groups.get(Bricker_bricks_gn)
        if brickGroup is not None:
            bpy.data.groups.remove(brickGroup, do_unlink=True)
        # remove current cmlist index
        cm.modelCreated = False
        cmlist_actions.removeItem(self, scn.cmlist_index)
        scn.cmlist_index = -1
        return{"FINISHED"}
