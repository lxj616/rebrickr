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
        cm = scn.cmlist[scn.cmlist_index]
        if bpy.data.objects[cm.source_name].type == 'MESH':
            return True
        return False

    def getObjectToLegoize(self):
        scn = bpy.context.scene
        if bpy.data.objects.find(scn.cmlist[scn.cmlist_index].source_name) == -1:
            objToLegoize = bpy.context.active_object
        else:
            objToLegoize = bpy.data.objects[scn.cmlist[scn.cmlist_index].source_name]
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

    def execute(self, context):
        # get start time
        startTime = time.time()

        # check if another model has to be committed
        if groupExists("LEGOizer_hidden"):
            self.report({"INFO"}, "Commit changes to last LEGOized model by pressing SHIFT-ENTER.")

        # set up variables
        scn = context.scene
        cm = scn.cmlist[scn.cmlist_index]
        cm.lastBrickHeight = cm.brickHeight
        cm.lastLogoResolution = cm.logoResolution
        cm.lastLogoDetail = cm.logoDetail

        # make sure 'LEGOizer_[source name]_bricks' group doesn't exist
        n = cm.source_name
        if groupExists("LEGOizer_%(n)s_bricks" % locals()):
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

        # create 'LEGOizer_[source.name]' group with source object
        select(source)
        n = source.name
        bpy.ops.group.create(name="LEGOizer_%(n)s" % locals())

        # get cross section
        source_details = bounds(source)
        dimensions = getBrickDimensions(cm.brickHeight, cm.gap)
        sizes = [source_details.x.distance, source_details.y.distance, source_details.z.distance]
        m = sizes.index(min(sizes))
        if m == 0:
            axis = "x"
            lScale = (0, source_details.y.distance, source_details.z.distance)
            numSlices = math.ceil(source_details.x.distance/(dimensions["width"] + dimensions["gap"]))
            CS_slices = slices(source, numSlices, (dimensions["width"] + dimensions["gap"]), axis=axis, drawSlices=False) # get list of horizontal bmesh slices
        if m == 1:
            axis = "y"
            lScale = (source_details.x.distance, 0, source_details.z.distance)
            numSlices = math.ceil(source_details.y.distance/(dimensions["width"] + dimensions["gap"]))
            CS_slices = slices(source, numSlices, (dimensions["width"] + dimensions["gap"]), axis=axis, drawSlices=False) # get list of horizontal bmesh slices
        if m == 2:
            axis = "z"
            lScale = (source_details.x.distance, source_details.y.distance, 0)
            numSlices = math.ceil(source_details.z.distance/(dimensions["height"] + dimensions["gap"]))
            CS_slices = slices(source, numSlices, (dimensions["height"] + dimensions["gap"]), axis=axis, drawSlices=False) # get list of horizontal bmesh slices

        if groupExists("LEGOizer_refLogo"):
            refLogo = bpy.data.groups["LEGOizer_refLogo"].objects[0]
        else:
            refLogo = None
            if cm.logoDetail != "None":
                # import refLogo and add to group
                refLogo = importLogo()
                select(refLogo)
                bpy.ops.group.create(name="LEGOizer_refLogo")
                hide(refLogo)

        # make 1x1 refBrick
        refBrick = make1x1(dimensions, refLogo, "%(n)s_brick1x1" % locals())
        # add refBrick to group
        bpy.context.scene.objects.link(refBrick)
        select(refBrick)
        bpy.ops.group.create(name="LEGOizer_%(n)s_refBrick" % locals())

        # hide all
        selectAll()
        bpy.ops.group.create(name="LEGOizer_hidden")
        hidden = hide(bpy.data.objects.values())

        # make bricks
        R = (dimensions["width"]+dimensions["gap"], dimensions["width"]+dimensions["gap"], dimensions["height"]+dimensions["gap"])
        slicesDict = [{"slices":CS_slices, "axis":axis, "R":R, "lScale":lScale}]
        makeBricks(slicesDict, refBrick, source_details)

        # STOPWATCH CHECK
        stopWatch("Time Elapsed", time.time()-startTime)

        scn.cmlist[scn.cmlist_index].changesToCommit = True

        context.window_manager.modal_handler_add(self)
        return{"RUNNING_MODAL"}
