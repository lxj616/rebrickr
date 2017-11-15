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
from addon_utils import check, paths, enable
from bpy.types import Panel
from bpy.props import *
props = bpy.props

# Rebrickr imports
from .committed_models_list import *
from .app_handlers import *
from .buttons import *
from ..buttons.delete import RebrickrDelete
from ..functions import *

# updater import
from .. import addon_updater_ops

class RebrickrBrickModPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Brick Mods"
    bl_idname      = "VIEW3D_PT_tools_Rebrickr_brick_mods"
    # bl_context     = "objectmode"
    bl_category    = "Rebrickr"
    bl_options     = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(self, context):
        scn = context.scene
        useCaching = bpy.context.user_preferences.addons[bpy.props.rebrickr_module_name].preferences.useCaching
        if not useCaching:
            return False
        if scn.cmlist_index == -1:
            return False
        cm = scn.cmlist[scn.cmlist_index]
        if cm.matrixIsDirty:
            return False
        return True

    def draw(self, context):
        layout = self.layout
        scn = context.scene

        col1 = layout.column(align=True)
        col1.label("Toggle Exposure:")
        split = col1.split(align=True, percentage=0.5)
        # set top exposed
        col = split.column(align=True)
        col.operator("rebrickr.set_exposure", text="Top").side = "TOP"
        # set bottom exposed
        col = split.column(align=True)
        col.operator("rebrickr.set_exposure", text="Bottom").side = "BOTTOM"

        col1 = layout.column(align=True)
        col1.label("Brick Operations:")
        split = col1.split(align=True, percentage=0.5)
        # split brick into 1x1s
        col = split.column(align=True)
        col.operator("rebrickr.split_bricks", text="Split")
        # merge selected bricks
        col = split.column(align=True)
        col.operator("rebrickr.merge_bricks", text="Merge")
        # Add identical brick on +/- x/y/z
        row = col1.row(align=True)
        row.operator("rebrickr.draw_adjacent", text="Draw Adjacent Bricks")
        # change brick type
        row = col1.row(align=True)
        row.operator("rebrickr.change_brick_type", text="Change Type")

        # next level:
        # enter brick sculpt mode
        # add brick at selected vertex
