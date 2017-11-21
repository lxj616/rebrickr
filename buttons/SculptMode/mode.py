'''
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
'''

# System imports
# NONE!

# Blender imports
import bpy
from bpy.types import Operator

# Rebrickr imports
from .undo_stack import *
from .ui import *
from ...functions import *


class SculptMode(Operator):
    bl_category    = "Rebrickr"
    bl_idname      = "rebrickr.sculpt_mode"
    bl_label       = "Sculpt Mode"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    ################################################
    # Blender Operator methods

    @classmethod
    def poll(self, context):
        return True

    def modal(self, context, event):
        # quit sculpt mode
        if event.type in {"ESC"} and event.value == "PRESS":
            print("modal quit")
            self.cancel(context)
            return{"CANCELLED"}

        tag_redraw_areas() # TODO: don't run tag_redraw here. should be done somewhere in Rebrickr_UI class
        ret = self.ui.window_manager.modal(context, event)
        if ret and 'hover' in ret:
            # self.rfwidget.clear()
            if self.ui.exit:
                self.cancel(context)
                return {'CANCELLED'}
            return {'PASS_THROUGH'}

        # TODO: generalize these event handlers to take keymap into account
        # handle pan/zoom/orient view
        if event.type in ['TRACKPADPAN', 'TRACKPADZOOM']:
            return {"PASS_THROUGH"}
        # handle selection
        if event.type in ['RIGHTMOUSE'] and event.value == 'PRESS':
            self.undo_stack.undo_push('select')
            return {"PASS_THROUGH"}
        # handle undo
        if self.pressed('undo', event):
            self.undo_stack.undo_pop()
            return {"PASS_THROUGH"}
        # handle redo
        if self.pressed('redo', event):
            self.undo_stack.redo_pop()
            return {"PASS_THROUGH"}
        # handle toggle fullscreen
        if event.type == 'F' and event.oskey:
            self.ui.toggle_maximize_area()
            return {"PASS_THROUGH"}
        # handle mouse move
        if event.type in ['MOUSEMOVE']:
            return {"PASS_THROUGH"}

        return {"RUNNING_MODAL"}

    def execute(self, context):
        self.ui.start()
        # run modal
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def cancel(self, context):
        self.ui.end()
        pass

    ################################################
    # initialization method

    def __init__(self):
        self.undo_stack = UndoStack.get_instance()
        self.ui = Rebrickr_UI.get_instance()

    ################################################
    # event handling functions

    def in_context_region(self, context, event):
        e_x = event.mouse_region_x  # left/right
        e_y = event.mouse_region_y  # up/down
        r_w = context.region.width  # left/right
        r_h = context.region.height # up/down
        return e_x > 0 and e_x < r_w and e_y > 0 and e_y < r_h

    def pressed(self, action, event):
        # initialize kms
        wm = bpy.context.window_manager
        screen_kms = wm.keyconfigs['Blender'].keymaps['Screen']

        # get km based on action
        if action.upper() == "UNDO":
            km = screen_kms.keymap_items['ed.undo']
        elif action.upper() == "REDO":
            km = screen_kms.keymap_items['ed.redo']
        else:
            km = None

        # check if event equivalent to action km
        if (km is not None and
            km.alt == event.alt and
            km.ctrl == event.ctrl and
            km.oskey == event.oskey and
            km.shift == event.shift and
            km.value == event.value and
            km.type == event.type):
            return True
        else:
            return False
