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

# Rebrickr imports
# from .actions import *
from .undo_stack import *
from .ui import *
from ...functions import *


# System imports
# NONE!

# Blender imports
import bpy

# Rebrickr imports
# NONE!

class UI_Functions():
    bl_category    = "Rebrickr"
    bl_idname      = "rebrickr.ui_functions"
    bl_label       = "Rebrickr UI Functions"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    def __init__(self):
        self.hiddenObjs = []

    ################################################
    # Functions for Rebrickr_UI

    def hideIrrelevantObjs(self):
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        for obj in scn.objects:
            if not obj.hide and obj.cmlist_id != cm.id:
                self.hiddenObjs.append(obj)
                hide(obj)
    def restoreHiddenObjs(self):
        unhide(self.hiddenObjs)
        self.hiddenObjs = []

    def toggle_tool_help(self):
        if self.window_help.visible:
            self.window_help.visible = False
        else:
            self.ui_helplabel.set_markdown(self.tool.helptext())
            self.window_help.visible = True
