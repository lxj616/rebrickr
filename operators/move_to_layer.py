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

# System imports
# NONE!

# Blender imports
import bpy
from bpy.types import Operator

# Rebrickr imports
from ..functions.common import *


class move_to_layer_override(Operator):
    """Move to Layer"""
    bl_idname = "object.move_to_layer"
    bl_label = "Move to Layer"
    bl_options = {'REGISTER', 'INTERNAL'}

    ################################################
    # Blender Operator methods

    @classmethod
    def poll(self, context):
        # return context.active_object is not None
        return True

    def execute(self, context):
        try:
            self.runMove(context)
        except:
            handle_exception()
        return {'FINISHED'}

    def invoke(self, context, event):
        # Run confirmation popup for delete action
        confirmation_returned = context.window_manager.invoke_confirm(self, event)
        if confirmation_returned != {'FINISHED'}:
            return confirmation_returned
        else:
            try:
                self.runMove(context)
            except:
                handle_exception()
            return {'FINISHED'}

    ###################################################
    # class variables

    layers = CollectionProperty()

    ################################################
    # class methods

    def runMove(self, context):
        scn = context.scene
        for obj in bpy.context.selected_objects:
            obj.layers = self.layers
            if obj.name.startswith("Rebrickr_") and obj.name.index("_bricks_frame_") != -1:
                for cm in scn.cmlist:
                    if obj.name[8:obj.name.index("_bricks_frame_")] == cm.source_name:
                        n = cm.source_name
                        for curFrame in range(cm.lastStartFrame, cm.lastStopFrame + 1):
                            bricksCurF = bpy.data.objects.get("Rebrickr_%(n)s_bricks_frame_%(curFrame)s" % locals())
                            if bricksCurF.name != obj.name:
                                bricksCurF.layers = self.layers
