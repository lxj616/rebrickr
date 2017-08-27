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
from mathutils import Vector
from ..functions import *
props = bpy.props

class legoizerEditSource(bpy.types.Operator):
    """ Edit Source Object Mesh """                                             # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "scene.legoizer_edit_source"                                             # unique identifier for buttons and menu items to reference.
    bl_label = "Edit Source Object Mesh"                                        # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns false) """
        scn = context.scene
        if scn.cmlist_index == -1:
            return False
        cm = scn.cmlist[scn.cmlist_index]
        if not cm.modelCreated:
            return False
        if scn.name == "LEGOizer_storage (DO NOT RENAME)":
            return False
        return True

    def modal(self, context, event):
        scn = bpy.context.scene
        source = bpy.data.objects.get(self.source_name)
        if source is None or bpy.context.scene.name != "LEGOizer_storage (DO NOT RENAME)" or source.mode != "EDIT" or event.type in {"ESC"} or (event.type in {"TAB"} and event.value == "PRESS"):
            self.report({"INFO"}, "Edits Committed")
            if self.lastSourceLocation is not None:
                source.location = self.lastSourceLocation
                source.rotation_euler = self.lastSourceRotation
                source.scale = self.lastSourceScale
            for screen in bpy.data.screens:
                screen.scene = self.origScene
            bpy.context.window_manager["editingSourceInStorage"] = False
            redraw_areas("VIEW_3D")
            scn.update()
            return {"FINISHED"}

        return {"PASS_THROUGH"}

    def execute(self, context):
        # initialize variables
        scn = context.scene
        self.origScene = scn
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        bpy.context.window_manager["editingSourceInStorage"] = True
        self.source_name = cm.source_name + " (DO NOT RENAME)"
        self.lastSourceLocation = None
        LEGOizer_bricks_gn = "LEGOizer_" + cm.source_name + "_bricks"
        cm.sourceIsDirty = True

        # get LEGOizer_storage (DO NOT RENAME) scene
        sto_scn = bpy.data.scenes.get("LEGOizer_storage (DO NOT RENAME)")
        if sto_scn is None:
            self.report({"WARNING"}, "'LEGOizer_storage (DO NOT RENAME)' scene could not be found")
            return {"CANCELLED"}
        # get source object
        source = bpy.data.objects.get(self.source_name)
        if source is None:
            self.report({"WARNING"}, "Source object '" + self.source_name + "' could not be found")
            return {"CANCELLED"}

        # set active scene as LEGOizer_storage (DO NOT RENAME)
        for screen in bpy.data.screens:
            screen.scene = sto_scn

        # make source visible and active selection
        sto_scn.layers = source.layers
        for obj in sto_scn.objects:
            obj.hide = True
        source.hide = False
        bGroup = bpy.data.groups.get(LEGOizer_bricks_gn)
        if bGroup is not None and len(bGroup.objects) > 0:
            obj = bGroup.objects[0]
            objParent = bpy.data.objects.get("LEGOizer_%(n)s_parent" % locals())
            if objParent is not None:
                objParentLoc = objParent.location
                objParentRot = objParent.rotation_euler
                objParentScale = objParent.scale
            else:
                objParentLoc = Vector((0,0,0))
                objParentRot = Vector((0,0,0))
                objParentScale = Vector((1,1,1))
            self.lastSourceLocation = source.location.to_tuple()
            self.lastSourceRotation = tuple(source.rotation_euler)
            self.lastSourceScale = source.scale.to_tuple()
            source.location = objParentLoc + obj.location
            source.rotation_euler = (source.rotation_euler[0] + obj.rotation_euler[0] + objParentRot[0], source.rotation_euler[1] + obj.rotation_euler[1] + objParentRot[1], source.rotation_euler[2] + obj.rotation_euler[2] + objParentRot[2])
            source.scale = (source.scale[0] * obj.scale[0] * objParentScale[0], source.scale[1] * obj.scale[1] * objParentScale[1], source.scale[2] * obj.scale[2] * objParentScale[2])
        select(source, active=source)

        # enter edit mode
        bpy.ops.object.mode_set(mode='EDIT')

        # run modal
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def cancel(self, context):
        if self.lastSourceLocation is not None:
            source.location = self.lastSourceLocation
            source.rotation_euler = self.lastSourceRotation
            source.scale = self.lastSourceScale
        for screen in bpy.data.screens:
            screen.scene = self.origScene
