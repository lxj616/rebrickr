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
from mathutils import Matrix, Vector
props = bpy.props

class legoizerLegoize(bpy.types.Operator):
    """Select objects layer by layer and shift by given values"""               # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "scene.legoizer_legoize"                                        # unique identifier for buttons and menu items to reference.
    bl_label = "Create Build Animation"                                         # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    def getObjectToLegoize(self):
        scn = bpy.context.scene
        if bpy.data.objects.find(scn.source_object) == -1:
            objToLegoize = bpy.context.active_object
        else:
            objToLegoize = bpy.data.objects[scn.source_object]
        return objToLegoize

    def execute(self, context):
        # get start time
        startTime = time.time()

        # set up variables
        scn = context.scene
        scn.lastResolution = scn.resolution
        scn.lastLogoResolution = scn.logoResolution
        scn.lastLogoDetail = scn.logoDetail

        # make sure 'LEGOizer_bricks' group doesn't exist
        if groupExists("LEGOizer_bricks"):
            self.report({"WARNING"}, "LEGOized Model already created. To create a new LEGOized model, first press 'Commit LEGOized Mesh'.")
            return {"CANCELLED"}

        # get object to LEGOize
        source = self.getObjectToLegoize()
        if source == None:
            self.report({"WARNING"}, "Please select a mesh to LEGOize")
            return{"CANCELLED"}
        if source.type != "MESH":
            self.report({"WARNING"}, "Only 'MESH' objects can be LEGOized. Please select another object (or press 'ALT-C to convert object to mesh).")
            return{"CANCELLED"}

        # create 'LEGOizer_source' group with source object
        select(source)
        bpy.ops.group.create(name="LEGOizer_source")

        # get cross section
        crossSectionDict = slices(source, False, scn.resolution)
        CS_slices = crossSectionDict["slices"] # list of bmesh slices

        refLogo = None
        if scn.logoDetail != "None":
            # import refLogo and add to group
            refLogo = importLogo()
            select(refLogo)
            bpy.ops.group.create(name="LEGOizer_refLogo")
            hide(refLogo)

        # make 1x1 refBrick
        dimensions = getBrickDimensions(crossSectionDict["sliceHeight"])
        refBrick = make1x1(dimensions, refLogo)
        # add refBrick to group
        bpy.context.scene.objects.link(refBrick)
        select(refBrick)
        bpy.ops.group.create(name="LEGOizer_refBrick")

        # hide all
        selectAll()
        bpy.ops.group.create(name="LEGOizer_hidden")
        hidden = hide(bpy.data.objects.values())

        # make bricks
        makeBricks(CS_slices, refBrick, dimensions, source)

        # STOPWATCH CHECK
        stopWatch("Time Elapsed", time.time()-startTime)

        return{"FINISHED"}
