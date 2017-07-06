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
import math
from ..functions import *
from mathutils import Matrix, Vector
props = bpy.props

class legoizerLegoize(bpy.types.Operator):
    """Select objects layer by layer and shift by given values"""               # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "scene.legoizer_legoize"                                        # unique identifier for buttons and menu items to reference.
    bl_label = "Create Build Animation"                                         # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns false) """
        scn = context.scene
        if scn.cmlist_index == -1:
            return False
        cm = scn.cmlist[scn.cmlist_index]
        if bpy.data.objects[cm.source_name].type == 'MESH':
            return True
        return False

    action = bpy.props.EnumProperty(
        items=(
            ("CREATE", "Create", ""),
            ("UPDATE", "Update", ""),
        )
    )

    def getObjectToLegoize(self):
        scn = bpy.context.scene
        if self.action == "CREATE":
            if bpy.data.objects.find(scn.cmlist[scn.cmlist_index].source_name) == -1:
                objToLegoize = bpy.context.active_object
            else:
                objToLegoize = bpy.data.objects[scn.cmlist[scn.cmlist_index].source_name]
        else:
            cm = scn.cmlist[scn.cmlist_index]
            n = cm.source_name
            objToLegoize = bpy.data.groups["LEGOizer_%(n)s" % locals()].objects[0]
        return objToLegoize

    def unhide(self, context):
        # clean up 'LEGOizer_hidden' group
        if groupExists("LEGOizer_hidden"):
            hiddenGroup = bpy.data.groups["LEGOizer_hidden"]
            unhide(list(hiddenGroup.objects))
            select(list(hiddenGroup.objects), deselect=True)
            bpy.data.groups.remove(hiddenGroup, do_unlink=True)

    def modal(self, context, event):
        """ When pressed, 'legoize mode' (loose concept) is deactivated """
        if event.type in {"RET", "NUMPAD_ENTER"} and event.shift:
            self.report({"INFO"}, "changes committed")
            self.unhide(context)
            n = context.scene.cmlist[context.scene.cmlist_index].source_name
            sourceGroup = bpy.data.groups["LEGOizer_%(n)s" % locals()]
            sourceGroup.objects[0].draw_type = 'WIRE'
            sourceGroup.objects[0].hide_render = True

            return{"FINISHED"}

        if context.scene.cmlist_index == -1 or not context.scene.cmlist[context.scene.cmlist_index].changesToCommit:
            self.unhide(context)
            return{"FINISHED"}
        return {"PASS_THROUGH"}

    def isValid(self, LEGOizer_bricks, source):
        if self.action == "CREATE":
            # verify function can run
            if groupExists("LEGOizer_hidden"):
                self.report({"INFO"}, "Commit changes to last LEGOized model by pressing SHIFT-ENTER.")
            if groupExists(LEGOizer_bricks):
                self.report({"WARNING"}, "LEGOized Model already created. To create a new LEGOized model, first press 'Commit LEGOized Mesh'.")
                return False
            # verify source exists and is of type mesh
            if source == None:
                self.report({"WARNING"}, "Please select a mesh to LEGOize")
                return False
            if source.type != "MESH":
                self.report({"WARNING"}, "Only 'MESH' objects can be LEGOized. Please select another object (or press 'ALT-C to convert object to mesh).")
                return False

        if self.action == "UPDATE":
            # make sure 'LEGOizer_[source name]_bricks' group exists
            if not groupExists(LEGOizer_bricks):
                self.report({"WARNING"}, "LEGOized Model doesn't exist. Create one with the 'LEGOize Object' button.")
                return False

        return True

    def execute(self, context):
        # get start time
        startTime = time.time()

        # set up variables
        scn = context.scene
        cm = scn.cmlist[scn.cmlist_index]
        source = self.getObjectToLegoize()
        n = cm.source_name
        LEGOizer_bricks = "LEGOizer_%(n)s_bricks" % locals()

        if not self.isValid(LEGOizer_bricks, source):
             return {"CANCELLED"}

        if not groupExists("LEGOizer_%(n)s"):
            # create 'LEGOizer_[cm.source_name]' group with source object
            select(source)
            bpy.ops.group.create(name="LEGOizer_%(n)s" % locals())

        # get cross section
        source_details = bounds(source)
        dimensions = getBrickDimensions(cm.brickHeight, cm.gap)
        axis, lScale, CS_slices = getCrossSection(source, source_details, dimensions)

        # update refLogo
        if cm.logoDetail == "None":
            refLogo = None
        elif groupExists("LEGOizer_refLogo"):
            refLogo = bpy.data.groups["LEGOizer_refLogo"].objects[0]
        else:
            # import refLogo and add to group
            refLogo = importLogo()
            select(refLogo)
            bpy.ops.group.create(name="LEGOizer_refLogo")
            # make it so that the object is unnoticable
            refLogo.scale = (0,0,0)
            refLogo.hide = True
            refLogo.hide_select = True
            refLogo.hide_render = True

        if groupExists("LEGOizer_%(n)s_refBrick" % locals()) and len(bpy.data.groups["LEGOizer_%(n)s_refBrick" % locals()].objects) > 0:
                # get 1x1 refBrick from group
                refBrick = bpy.data.groups["LEGOizer_%(n)s_refBrick" % locals()].objects[0]
                # update that refBrick
                unhide(refBrick)
                make1x1(dimensions, refLogo, name=refBrick.name)
                hide(refBrick)
        else:
            # make 1x1 refBrick
            refBrick = make1x1(dimensions, refLogo, "%(n)s_brick1x1" % locals())
            # add that refBrick to new group
            bpy.context.scene.objects.link(refBrick)
            if groupExists("LEGOizer_%(n)s_refBrick" % locals()):
                bpy.data.groups["LEGOizer_%(n)s_refBrick" % locals()].objects.link(refBrick)
            else:
                select(refBrick)
                bpy.ops.group.create(name="LEGOizer_%(n)s_refBrick" % locals())

        if self.action == "CREATE":
            # hide all
            selectAll()
            bpy.ops.group.create(name="LEGOizer_hidden")
            hide(bpy.data.objects.values())

        # if resolution has changed
        if cm.brickHeight != cm.lastBrickHeight:
            if self.action == "UPDATE":
                bricks = list(bpy.data.groups[LEGOizer_bricks].objects)
                delete(bricks)
            R = (dimensions["width"]+dimensions["gap"], dimensions["width"]+dimensions["gap"], dimensions["height"]+dimensions["gap"])
            slicesDict = [{"slices":CS_slices, "axis":axis, "R":R, "lScale":lScale}]
            makeBricks(slicesDict, refBrick, source, source_details, cm.preHollow)

        # set final variables
        cm.lastBrickHeight = cm.brickHeight
        cm.lastLogoResolution = cm.logoResolution
        cm.lastLogoDetail = cm.logoDetail
        cm.changesToCommit = True

        # STOPWATCH CHECK
        stopWatch("Time Elapsed", time.time()-startTime)

        if self.action == "CREATE":
            context.window_manager.modal_handler_add(self)
            return{"RUNNING_MODAL"}
        else:
            return{"FINISHED"}
