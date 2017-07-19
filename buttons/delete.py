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
from mathutils import Euler
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
        if groupExists("LEGOizer_%(n)s_bricks" % locals()) or groupExists("LEGOizer_%(n)s" % locals()) or groupExists("LEGOizer_%(n)s_refBricks" % locals()):
            return True
        return False

    @classmethod
    def cleanUp(cls):
        # set up variables
        scn = bpy.context.scene
        n = scn.cmlist[scn.cmlist_index].source_name
        LEGOizer_bricks_gn = "LEGOizer_%(n)s_bricks" % locals()
        LEGOizer_parent_gn = "LEGOizer_%(n)s_parent" % locals()
        LEGOizer_refBricks_gn = "LEGOizer_%(n)s_refBricks" % locals()
        LEGOizer_source_gn = "LEGOizer_%(n)s" % locals()

        # clean up 'LEGOizer_[source name]' group
        if groupExists(LEGOizer_source_gn):
            sourceGroup = bpy.data.groups[LEGOizer_source_gn]
            if len(sourceGroup.objects) > 0:
                source = sourceGroup.objects[0]
                source.location = source["previous_location"]
                scn.objects.link(source)
                select(source, active=source)
            bpy.data.groups.remove(sourceGroup, do_unlink=True)

        # clean up LEGOizer_parent group
        if groupExists(LEGOizer_parent_gn):
            pGroup = bpy.data.groups[LEGOizer_parent_gn]
            try:
                parent = bpy.data.groups[LEGOizer_parent_gn].objects[0]
                delete(parent)
            except:
                pass
            bpy.data.groups.remove(pGroup, do_unlink=True)

        # clean up LEGOizer_bricks group
        if groupExists(LEGOizer_bricks_gn):
            brickGroup = bpy.data.groups[LEGOizer_bricks_gn]
            bgObjects = list(brickGroup.objects)
            if len(bgObjects) > 0:
                delete(bgObjects)
            bpy.data.groups.remove(brickGroup, do_unlink=True)
            bpy.context.area.tag_redraw()

        # clean up 'LEGOizer_refBrick' group
        if groupExists(LEGOizer_refBricks_gn):
            refBrickGroup = bpy.data.groups[LEGOizer_refBricks_gn]
            if len(refBrickGroup.objects) > 0:
                refBrick = refBrickGroup.objects[0]
                delete(refBrick)
            bpy.data.groups.remove(refBrickGroup, do_unlink=True)

        # # clean up 'LEGOizer_refLogo' group
        # if groupExists("LEGOizer_refLogo"):
        #     refLogoGroup = bpy.data.groups["LEGOizer_refLogo"]
        #     refLogo = refLogoGroup.objects[0]
        #     delete(refLogo)
        #     bpy.data.groups.remove(refLogoGroup, do_unlink=True)

    def execute(self, context):
        # # get start time
        # startTime = time.time()

        self.cleanUp()

        # # STOPWATCH CHECK
        # stopWatch("Time Elapsed (DELETE)", time.time()-startTime)

        return{"FINISHED"}
