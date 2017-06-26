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
from ..lib import common_utilities
from ..lib.common_utilities import bversion
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

        # if bversion() < '002.076.00':
        #     col = layout.column(align=True)
        #     col.label('ERROR: upgrade needed', icon='ERROR')
        #     col.label('LEGOizer requires Blender 2.76+')
        #     return

        col = layout.column(align=True)
        col.label("Source Object:")

        if context.mode == 'OBJECT':
            row = col.row(align=True)
            scene = context.scene
            row.prop_search(scn, "source_object", scene, "objects", text='')

            # sub = row.row(align=True)
            # sub.scale_x = 0.1
            # sub.operator("cgcookie.eye_dropper", icon='EYEDROPPER').target_prop = 'source_object'

        col = layout.column(align=True)
        row = col.row(align=True)
        groupExistsBool = groupExists("LEGOizer_bricks")
        # remove 'LEGOizer_bricks' group if empty
        if groupExistsBool and len(bpy.data.groups["LEGOizer_bricks"].objects) == 0:
            bpy.data.groups.remove(bpy.data.groups["LEGOizer_bricks"], do_unlink=True)
        row.active = not groupExistsBool
        row.operator("scene.legoizer_legoize", text="LEGOize Object", icon="MOD_BUILD")


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
        row.prop(scn, "resolution")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(scn, "preHollow")
        if scn.preHollow:
            row = col.row(align=True)
            row.prop(scn, "shellThickness")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(scn, "logoDetail", text="Logo")
        if scn.logoDetail != "None":
            col = layout.column(align=True)
            row = col.row(align=True)
            row.prop(scn, "logoResolution", text="Logo Resolution")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(scn, "undersideDetail", text="Underside")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(scn, "studVerts")
        groupExistsBool = groupExists("LEGOizer_bricks")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.active = groupExistsBool
        row.operator("scene.legoizer_update", text="Update Model", icon="FILE_REFRESH")
        row = col.row(align=True)
        row.active = groupExistsBool
        row.operator("scene.legoizer_merge", text="Merge Bricks", icon="MOD_REMESH")
        row = col.row(align=True)
        row.active = groupExistsBool
        row.operator("scene.legoizer_commit", text="Commit Model", icon="MOD_DECIM")



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
