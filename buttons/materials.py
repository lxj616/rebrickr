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
import bpy
import time
import bmesh
import os
import math
from ..functions import *
from .delete import legoizerDelete
from mathutils import Matrix, Vector, Euler
props = bpy.props

class legoizerApplyMaterial(bpy.types.Operator):
    """Apply specified material to all bricks created"""                        # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "scene.legoizer_apply_material"                                 # unique identifier for buttons and menu items to reference.
    bl_label = "Apply Material"                                         # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns false) """
        scn = context.scene
        if scn.cmlist_index == -1:
            return False
        cm = scn.cmlist[scn.cmlist_index]
        if not (cm.modelCreated or cm.animated):
            return False
        return True

    action = bpy.props.EnumProperty(
        items=(
            ("CUSTOM", "Custom", ""),
            ("INTERNAL", "Internal", ""),
        )
    )

    def execute(self, context):
        # get start time
        startTime = time.time()

        # set up variables
        scn = context.scene
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        LEGOizer_bricks_gn = "LEGOizer_%(n)s_bricks" % locals()
        bricks = list(bpy.data.groups[LEGOizer_bricks_gn].objects)
        if self.action == "CUSTOM":
            matName = cm.materialName
        elif self.action == "INTERNAL":
            matName = cm.internalMatName
        mat = bpy.data.materials.get(matName)
        if mat is None:
            self.report({"WARNING"}, "Specified material doesn't exist")

        for brick in bricks:
            # if materials exist, remove them
            if brick.data.materials:
                if self.action == "CUSTOM":
                    brick.data.materials.clear(1)
                    # Assign it to object
                    brick.data.materials.append(mat)
                elif self.action == "INTERNAL":
                    brick.data.materials.pop(0)
                    # Assign it to object
                    brick.data.materials.append(mat)
                    for i in range(len(brick.data.materials)-1):
                        brick.data.materials.append(brick.data.materials.pop(0))

        cm.materialIsDirty = False

        # STOPWATCH CHECK
        stopWatch("Total Time Elapsed", time.time()-startTime)
        return{"FINISHED"}
