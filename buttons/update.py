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

class legoizerUpdate(bpy.types.Operator):
    """Select objects layer by layer and shift by given values"""               # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "scene.legoizer_update"                                        # unique identifier for buttons and menu items to reference.
    bl_label = "Create Build Animation"                                         # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns false) """
        scn = context.scene
        if scn.cmlist_index == -1:
            return False
        n = scn.cmlist[scn.cmlist_index].source_object
        if not groupExists("LEGOizer_%(n)s_bricks" % locals()):
            return False
        return True

    def execute(self, context):
        # get start time
        startTime = time.time()

        # set up variables
        scn = context.scene

        # make sure 'LEGOizer_[source name]_bricks' group exists
        n = scn.cmlist[scn.cmlist_index].source_object
        LEGOizer_bricks = "LEGOizer_%(n)s_bricks" % locals()
        if not groupExists(LEGOizer_bricks):
            self.report({"WARNING"}, "LEGOized Model doesn't exist. Create one with the 'LEGOize Object' button.")
            return {"CANCELLED"}

        # get relevant bricks from groups
        refBrick = bpy.data.groups["LEGOizer_%(n)s_refBrick" % locals()].objects[0]
        n = scn.cmlist[scn.cmlist_index].source_object
        source = bpy.data.groups["LEGOizer_%(n)s" % locals()].objects[0]
        bricks = list(bpy.data.groups[LEGOizer_bricks].objects)

        # get cross section
        crossSectionDict = slices(source, False, scn.resolution)
        CS_slices = crossSectionDict["slices"] # list of bmesh slices

        # update refLogo
        refLogo = None
        if scn.logoDetail != "None" and (scn.lastLogoDetail != scn.logoDetail or scn.lastLogoResolution != scn.logoResolution):
            if groupExists("LEGOizer_refLogo"):
                refLogoGroup = bpy.data.groups["LEGOizer_refLogo"]
                delete(refLogoGroup.objects[0])
                bpy.data.groups.remove(group=refLogoGroup, do_unlink=True)
            # import refLogo and add to group
            refLogo = importLogo()
            select(refLogo)
            bpy.ops.group.create(name="LEGOizer_refLogo")
            hide(refLogo)

        # update refBrick
        unhide(refBrick)
        dimensions = getBrickDimensions(crossSectionDict["sliceHeight"])
        make1x1(dimensions, refLogo, name=refBrick.name)
        hide(refBrick)

        # if resolution has changed
        if scn.resolution != scn.lastResolution:
            delete(bricks)
            makeBricks(CS_slices, refBrick, dimensions, source)

        scn.lastResolution = scn.resolution

        scn.cmlist[scn.cmlist_index].changesToCommit = True

        # STOPWATCH CHECK
        stopWatch("Time Elapsed", time.time()-startTime)

        return{"FINISHED"}
