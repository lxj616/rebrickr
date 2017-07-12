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
from .committed_models_list import *
from ..buttons.delete import legoizerDelete
from ..functions import *
from ..lib import common_utilities
from ..lib.common_utilities import bversion
props = bpy.props

class LegoModelsPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "LEGO Models"
    bl_idname      = "VIEW3D_PT_tools_LEGOizer_lego_models"
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

        rows = 3
        row = layout.row()
        row.template_list("UL_items", "", scn, "cmlist", scn, "cmlist_index", rows=rows)

        col = row.column(align=True)
        col.operator("cmlist.list_action", icon='ZOOMIN', text="").action = 'ADD'
        col.operator("cmlist.list_action", icon='ZOOMOUT', text="").action = 'REMOVE'
        col.separator()
        col.operator("cmlist.select_bricks", icon="UV_SYNC_SELECT", text="")
        # col.operator("cmlist.list_action", icon='')
        # col.operator("cmlist.list_action", icon='TRIA_UP', text="").action = 'UP'
        # col.operator("cmlist.list_action", icon='TRIA_DOWN', text="").action = 'DOWN'

        # row = layout.row()
        # col = row.column(align=True)
        # col.operator("cmlist.print_list", icon="WORDWRAP_ON")
        # col.operator("cmlist.select_item", icon="UV_SYNC_SELECT")
        # col.operator("cmlist.clear_list", icon="X")
        if scn.cmlist_index != -1:
            cm = scn.cmlist[scn.cmlist_index]
            n = cm.source_name
            LEGOizer_bricks = "LEGOizer_%(n)s_bricks" % locals()
            groupExistsBool = groupExists(LEGOizer_bricks) or groupExists("LEGOizer_%(n)s" % locals()) or groupExists("LEGOizer_%(n)s_refBricks" % locals())
            col = layout.column(align=True)
            col.label("Source Object:")
            row = col.row(align=True)
            if not groupExistsBool:
                row.prop_search(cm, "source_name", scn, "objects", text='')
            else:
                row.operator("scene.legoizer_delete", text="Delete LEGOized Model", icon="CANCEL")

            # sub = row.row(align=True)
            # sub.scale_x = 0.1
            # sub.operator("cgcookie.eye_dropper", icon='EYEDROPPER').target_prop = 'source_name'

            col = layout.column(align=True)
            row = col.row(align=True)
            # remove 'LEGOizer_[source name]_bricks' group if empty
            if groupExists(LEGOizer_bricks) and len(bpy.data.groups[LEGOizer_bricks].objects) == 0:
                legoizerDelete.cleanUp()
                bpy.data.groups.remove(bpy.data.groups[LEGOizer_bricks], do_unlink=True)
        else:
            layout.operator("cmlist.list_action", icon='ZOOMIN', text="New LEGO Model").action = 'ADD'


class SettingsPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Settings"
    bl_idname      = "VIEW3D_PT_tools_LEGOizer_settings"
    bl_context     = "objectmode"
    bl_category    = "LEGOizer"
    COMPAT_ENGINES = {"CYCLES", "BLENDER_RENDER"}

    @classmethod
    def poll(self, context):
        scn = context.scene
        if scn.cmlist_index == -1:
            return False
        return True

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        cm = scn.cmlist[scn.cmlist_index]

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(cm, "brickHeight")
        row = col.row(align=True)
        row.prop(cm, "gap")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(cm, "preHollow")
        if cm.preHollow:
            row = col.row(align=True)
            row.prop(cm, "shellThickness")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.label("Logo Detail:")
        row = col.row(align=True)
        row.prop(cm, "logoDetail", text="")
        if cm.logoDetail != "None":
            row = col.row(align=True)
            row.prop(cm, "logoResolution", text="Logo Resolution")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.label("Underside Detail:")
        row = col.row(align=True)
        row.prop(cm, "hiddenUndersideDetail", text="Hidden")
        row = col.row(align=True)
        row.prop(cm, "exposedUndersideDetail", text="Exposed")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(cm, "studVerts")
        col = layout.column(align=True)
        row = col.row(align=True)
        n = cm.source_name
        LEGOizer_bricks = "LEGOizer_%(n)s_bricks" % locals()
        groupExistsBool = groupExists(LEGOizer_bricks) or groupExists("LEGOizer_%(n)s" % locals()) or groupExists("LEGOizer_%(n)s_refBricks" % locals())
        if not groupExistsBool:
            row.operator("scene.legoizer_legoize", text="LEGOize Object", icon="MOD_BUILD").action = "CREATE"
        else:
            row.operator("scene.legoizer_legoize", text="Update Model", icon="FILE_REFRESH").action = "UPDATE"
        row = col.row(align=True)
        row.operator("scene.legoizer_merge", text="Merge Bricks", icon="MOD_REMESH")
        row = col.row(align=True)
        row.operator("scene.legoizer_commit", text="Commit Model", icon="FILE_TICK")


class AdvancedPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Advanced"
    bl_idname      = "VIEW3D_PT_tools_LEGOizer_advanced"
    bl_context     = "objectmode"
    bl_category    = "LEGOizer"
    bl_options     = {"DEFAULT_CLOSED"}
    COMPAT_ENGINES = {"CYCLES", "BLENDER_RENDER"}

    @classmethod
    def poll(self, context):
        scn = context.scene
        if scn.cmlist_index == -1:
            return False
        return True

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        cm = scn.cmlist[scn.cmlist_index]

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(cm, "calculationAxes", text="")
