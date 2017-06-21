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
from bpy.types import Panel
from bpy.props import *
from ..functions import *
props = bpy.props

class ActionsPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Actions"
    bl_idname      = "VIEW3D_PT_tools_LEGOizer_actions"
    bl_context     = "objectmode"
    bl_category    = "LEGOizer"
    COMPAT_ENGINES = {"CYCLES", "BLENDER_RENDER"}

    def draw(self, context):
        layout = self.layout
        scn = context.scene

        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("scene.legoizer_legoize", text="LEGOize Active Mesh", icon="EDIT")
        row = col.row(align=True)
        row.operator("scene.legoizer_merge", text="Finalize LEGOized Mesh", icon="EDIT")


class SettingsPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Settings"
    bl_idname      = "VIEW3D_PT_tools_LEGOizer_settings"
    bl_context     = "objectmode"
    bl_category    = "LEGOizer"
    COMPAT_ENGINES = {"CYCLES", "BLENDER_RENDER"}

    def draw(self, context):
        layout = self.layout
        scn = context.scene

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(scn, "preHollow")
        if scn.preHollow:
            row = col.row(align=True)
            row.prop(scn, "shellThickness")



class AdvancedPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Advanced"
    bl_idname      = "VIEW3D_PT_tools_LEGOizer_advanced"
    bl_context     = "objectmode"
    bl_category    = "LEGOizer"
    bl_options     = {"DEFAULT_CLOSED"}
    COMPAT_ENGINES = {"CYCLES", "BLENDER_RENDER"}

    def draw(self, context):
        layout = self.layout
        scn = context.scene

        col = layout.column(align=True)
        row = col.row(align=True)
