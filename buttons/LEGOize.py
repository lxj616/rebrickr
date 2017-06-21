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

class legoize(bpy.types.Operator):
    """Select objects layer by layer and shift by given values"""               # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "scene.legoizer_legoize"                                        # unique identifier for buttons and menu items to reference.
    bl_label = "Create Build Animation"                                         # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        # get start time
        startTime = time.time()

        # set up variables
        scn = context.scene

        # make sure 'LEGOizer_bricks' group doesn't exist
        if groupExists("LEGOizer_bricks"):
            self.report({"WARNING"}, "LEGOized Model already created. To create a new LEGOized model, first press 'Commit LEGOized Mesh'.")
            return {"CANCELLED"}

        # get object to LEGOize
        if bpy.data.objects.find(scn.source_object) == -1:
            self.objToLegoize = context.active_object
        else:
            self.objToLegoize = bpy.data.objects[scn.source_object]

        if self.objToLegoize == None:
            self.report({"WARNING"}, "Please select a mesh to LEGOize")
            return{"CANCELLED"}

        selectOnly(self.objToLegoize)
        bpy.ops.group.create(name="LEGOizer_source")

        crossSectionDict = slices(self.objToLegoize, False, scn.resolution)
        CS_slices = crossSectionDict["slices"] # list of bmesh slices

        # set brick dimensions
        brick_scale = crossSectionDict["sliceHeight"]/9.6
        brick_height = brick_scale*9.6
        brick_width = brick_scale*8
        stud_height = brick_scale*1.8
        stud_diameter = brick_scale*4.8
        stud_radius = stud_diameter/2

        # deselect all
        deselectAll()

        # for each layer, assemble bricks
        for bm in CS_slices:
            drawBMesh(bm)
            continue

        # add assembled bricks to new group
        self.groupName = "LEGOizer_bricks"
        if not groupExists(self.groupName):
            bpy.ops.group.create(name=self.groupName)
        else:
            self.report({"ERROR"}, "Could not create group; it already exists!")
            return{"CANCELLED"}


        # STOPWATCH CHECK
        stopWatch("Time Elapsed", time.time()-startTime)

        return{"FINISHED"}
