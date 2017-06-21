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
from ..functions import *
props = bpy.props

class mergeBricks(bpy.types.Operator):
    """Reduces poly count by merging bricks"""                                  # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "scene.legoizer_merge"                                          # unique identifier for buttons and menu items to reference.
    bl_label = "Merge Bricks"                                                          # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}                                           # enable undo for the operator.

    def execute(self, context):
        # set up variables
        scn = context.scene

        # get start time
        startTime = time.time()

        # make sure 'LEGOizer_bricks' group exists
        if not groupExists("LEGOizer_bricks"):
            self.report({"WARNING"}, "LEGOized Model already created. To create a new LEGOized model, first press 'Commit LEGOized Mesh'.")
            return {"CANCELLED"}

        sourceGroup = bpy.data.groups["LEGOizer_source"]
        brickGroup = bpy.data.groups["LEGOizer_bricks"]

        # delete objects in brickGroup
        selectOnly(list(brickGroup.objects))
        bpy.ops.object.delete()

        # remove 'LEGOizer_*' groups
        bpy.data.groups.remove(sourceGroup, do_unlink=True)
        bpy.data.groups.remove(brickGroup, do_unlink=True)


        # STOPWATCH CHECK
        stopWatch("Time Elapsed", time.time()-startTime)

        return{"FINISHED"}
