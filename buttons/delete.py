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

    modelType = bpy.props.EnumProperty(
        items=(
            ("MODEL", "Model", ""),
            ("ANIMATION", "Animation", ""),
        ),
        default="MODEL"
    )

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns false) """
        scn = context.scene
        if scn.cmlist_index == -1:
            return False
        # n = scn.cmlist[scn.cmlist_index].source_name
        # if groupExists("LEGOizer_%(n)s_bricks" % locals()) or groupExists("LEGOizer_%(n)s" % locals()) or groupExists("LEGOizer_%(n)s_refBricks" % locals()):
        #     return True
        return True

    @classmethod
    def cleanUp(cls, modelType, skipSource=False, skipDupes=False, skipParents=False):
        # set up variables
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        source = bpy.data.objects[cm.source_name]
        LEGOizer_bricks_gn = "LEGOizer_%(n)s_bricks" % locals()
        LEGOizer_parent_on = "LEGOizer_%(n)s_parent" % locals()
        LEGOizer_refBricks_gn = "LEGOizer_%(n)s_refBricks" % locals()
        LEGOizer_source_dupes_gn = "LEGOizer_%(n)s_dupes" % locals()

        # clean up 'LEGOizer_[source name]' group
        if not skipSource:
            try:
                source.location = source["previous_location"]
            except:
                pass
            if not source in list(scn.objects):
                safeLink(source)
            select(source, active=source)
            cm.modelHeight = -1
            # reset source parent to original parent object
            old_parent = bpy.data.objects.get(source["old_parent"])
            if old_parent is not None:
                select([source, old_parent], active=old_parent)
                try:
                    origFrame = scn.frame_current
                    scn.frame_set(source["frame_parent_cleared"])
                    bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
                    scn.frame_set(origFrame)
                except:
                    pass
            # if modifiers were ignored/disabled from view, enable in view
            if source["ignored_mods"] is not None:
                for mn in source["ignored_mods"]:
                    source.modifiers[mn].show_viewport = True

        # clean up 'LEGOizer_[source name]_dupes' group
        if groupExists(LEGOizer_source_dupes_gn) and not skipDupes:
            dGroup = bpy.data.groups[LEGOizer_source_dupes_gn]
            dObjects = list(dGroup.objects)
            if len(dObjects) > 0:
                delete(dObjects)
            bpy.data.groups.remove(dGroup, do_unlink=True)

        if not skipParents:
            # clean up LEGOizer_parent object
            pGroup = bpy.data.groups.get(LEGOizer_parent_on)
            if pGroup:
                for parent in pGroup.objects:
                    m = parent.data
                    bpy.data.objects.remove(parent, True)
                    bpy.data.meshes.remove(m, True)

        if modelType == "MODEL":
            # clean up LEGOizer_bricks group
            cm.modelCreated = False
            if groupExists(LEGOizer_bricks_gn):
                brickGroup = bpy.data.groups[LEGOizer_bricks_gn]
                bgObjects = list(brickGroup.objects)
                for obj in bgObjects:
                    m = obj.data
                    bpy.data.objects.remove(obj, True)
                    bpy.data.meshes.remove(m, True)
                bpy.data.groups.remove(brickGroup, do_unlink=True)
                redraw_areas("VIEW_3D")
        elif modelType == "ANIMATION":
            # clean up LEGOizer_bricks group
            cm.animated = False
            for i in range(cm.lastStartFrame, cm.lastStopFrame + 1):
                LEGOizer_bricks_cur_frame_gn = LEGOizer_bricks_gn + "_frame_" + str(i)
                print(LEGOizer_bricks_cur_frame_gn)
                if groupExists(LEGOizer_bricks_cur_frame_gn):
                    brickGroup = bpy.data.groups[LEGOizer_bricks_cur_frame_gn]
                    bgObjects = list(brickGroup.objects)
                    if len(bgObjects) > 0:
                        delete(bgObjects)
                    bpy.data.groups.remove(brickGroup, do_unlink=True)
            redraw_areas("VIEW_3D")

        # # clean up 'LEGOizer_refBrick' group
        # if groupExists(LEGOizer_refBricks_gn) and not skipRefBrick:
        #     refBrickGroup = bpy.data.groups[LEGOizer_refBricks_gn]
        #     if len(refBrickGroup.objects) > 0:
        #         refBrick = refBrickGroup.objects[0]
        #         delete(refBrick)
        #     bpy.data.groups.remove(refBrickGroup, do_unlink=True)

        return source

    def execute(self, context):
        # # get start time
        # startTime = time.time()

        source = self.cleanUp(self.modelType)

        select(source, active=source)
        context.scene.update()

        # # STOPWATCH CHECK
        # stopWatch("Time Elapsed (DELETE)", time.time()-startTime)

        return{"FINISHED"}
