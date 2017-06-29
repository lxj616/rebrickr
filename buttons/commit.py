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

class legoizerCommit(bpy.types.Operator):
    """Commit Edits on LEGOized Mesh """                                        # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "scene.legoizer_commit"                                         # unique identifier for buttons and menu items to reference.
    bl_label = "Commit Edits to LEGO Sculpt"                                    # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        # get start time
        startTime = time.time()

        # set up variables
        scn = context.scene

        # make sure 'LEGOizer_bricks' group exists
        if not groupExists("LEGOizer_bricks"):
            self.report({"WARNING"}, "LEGOized Model doesn't exist. Create one with the 'LEGOize Object' button.")
            return{"CANCELLED"}

        # clean up 'LEGOizer_hidden' group
        hiddenGroup = bpy.data.groups["LEGOizer_hidden"]
        unhide(list(hiddenGroup.objects))
        select(list(hiddenGroup.objects), deselect=True)
        bpy.data.groups.remove(hiddenGroup, do_unlink=True)

        # clean up 'LEGOizer_bricks' group
        brickGroup = bpy.data.groups["LEGOizer_bricks"]
        bpy.data.groups.remove(brickGroup, do_unlink=True)

        # clean up 'LEGOizer_source' group
        sourceGroup = bpy.data.groups["LEGOizer_source"]
        sourceGroup.objects[0].draw_type = 'WIRE'
        bpy.data.groups.remove(sourceGroup, do_unlink=True)

        # clean up 'LEGOizer_refBrick' group
        refBrickGroup = bpy.data.groups["LEGOizer_refBrick"]
        refBrick = refBrickGroup.objects[0]
        delete(refBrick)
        bpy.data.groups.remove(refBrickGroup, do_unlink=True)

        # clean up 'LEGOizer_refLogo' group
        if groupExists("LEGOizer_refLogo"):
            refLogoGroup = bpy.data.groups["LEGOizer_refLogo"]
            refLogo = refLogoGroup.objects[0]
            delete(refLogo)
            bpy.data.groups.remove(refLogoGroup, do_unlink=True)

        # STOPWATCH CHECK
        stopWatch("Time Elapsed", time.time()-startTime)

        return{"FINISHED"}
