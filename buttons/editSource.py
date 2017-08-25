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
        return True

    def modal(self, context, event):
        source = bpy.data.objects.get(self.source_name)
        if source is None or source.mode != "EDIT" or event.type in {"ESC"} or (event.type in {"TAB"} and event.value == "PRESS"):
            self.report({"INFO"}, "Edits Committed")
            for screen in bpy.data.screens:
                screen.scene = self.origScene
            return{"FINISHED"}
        return {"PASS_THROUGH"}

    def execute(self, context):
        # initialize variables
        scn = context.scene
        self.origScene = scn
        cm = scn.cmlist[scn.cmlist_index]
        self.source_name = cm.source_name
        cm.sourceIsDirty = True

        # get LEGOizer_storage scene
        sto_scn = bpy.data.scenes.get("LEGOizer_storage")
        if sto_scn is None:
            self.report({"WARNING"}, "'LEGOizer_storage' scene could not be found")
            return {"CANCELLED"}
        # get source object
        source = bpy.data.objects.get(self.source_name)
        if source is None:
            self.report({"WARNING"}, "Source object '" + self.source_name + "' could not be found")
            return {"CANCELLED"}

        # set active scene as LEGOizer_storage
        for screen in bpy.data.screens:
            screen.scene = sto_scn

        # make source visible and active selection
        scn.layers = source.layers
        source.hide = False
        select(source, active=source)

        # enter edit mode
        bpy.ops.object.mode_set(mode='EDIT')

        # run modal
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}
