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

class legoizerDelete(bpy.types.Operator):
    """ Delete LEGOized model """                                               # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "scene.legoizer_delete"                                         # unique identifier for buttons and menu items to reference.
    bl_label = "Delete LEGOized model from Blender"                             # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns false) """
        scn = context.scene
        if scn.cmlist_index == -1:
            return False
        n = scn.cmlist[scn.cmlist_index].source_name
        if not groupExists("LEGOizer_%(n)s_bricks" % locals()):
            return False
        return True

    def execute(self, context):
        # get start time
        startTime = time.time()

        # set up variables
        scn = context.scene

        # clean up LEGOizer_bricks group
        n = scn.cmlist[scn.cmlist_index].source_name
        LEGOizer_bricks = "LEGOizer_%(n)s_bricks" % locals()
        brickGroup = bpy.data.groups[LEGOizer_bricks]
        delete(list(brickGroup.objects))
        bpy.data.groups.remove(brickGroup, do_unlink=True)

        # clean up 'LEGOizer_[source name]' group
        sourceGroup = bpy.data.groups["LEGOizer_%(n)s" % locals()]
        sourceGroup.objects[0].draw_type = 'SOLID'
        sourceGroup.objects[0].hide_render = False
        bpy.data.groups.remove(sourceGroup, do_unlink=True)

        # clean up 'LEGOizer_refBrick' group
        refBrickGroup = bpy.data.groups["LEGOizer_%(n)s_refBrick" % locals()]
        refBrick = refBrickGroup.objects[0]
        delete(refBrick)
        bpy.data.groups.remove(refBrickGroup, do_unlink=True)

        # # clean up 'LEGOizer_refLogo' group
        # if groupExists("LEGOizer_refLogo"):
        #     refLogoGroup = bpy.data.groups["LEGOizer_refLogo"]
        #     refLogo = refLogoGroup.objects[0]
        #     delete(refLogo)
        #     bpy.data.groups.remove(refLogoGroup, do_unlink=True)

        scn.cmlist[scn.cmlist_index].changesToCommit = False

        # STOPWATCH CHECK
        stopWatch("Time Elapsed", time.time()-startTime)

        return{"FINISHED"}
