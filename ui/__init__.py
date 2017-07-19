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

        if bversion() < '002.078.00':
            col = layout.column(align=True)
            col.label('ERROR: upgrade needed', icon='ERROR')
            col.label('LEGOizer requires Blender 2.78+')
            return

        rows = 3
        row = layout.row()
        row.template_list("UL_items", "", scn, "cmlist", scn, "cmlist_index", rows=rows)

        col = row.column(align=True)
        col.operator("cmlist.list_action", icon='ZOOMIN', text="").action = 'ADD'
        col.operator("cmlist.list_action", icon='ZOOMOUT', text="").action = 'REMOVE'
        col.separator()
        col.operator("cmlist.list_action", icon='TRIA_UP', text="").action = 'UP'
        col.operator("cmlist.list_action", icon='TRIA_DOWN', text="").action = 'DOWN'

        if scn.cmlist_index != -1:
            cm = scn.cmlist[scn.cmlist_index]
            n = cm.source_name
            LEGOizer_bricks = "LEGOizer_%(n)s_bricks" % locals()
            groupExistsBool = groupExists(LEGOizer_bricks) or groupExists("LEGOizer_%(n)s" % locals()) or groupExists("LEGOizer_%(n)s_refBricks" % locals())
            if not groupExistsBool:
                col = layout.column(align=True)
                col.label("Source Object:")
                split = col.split(align=True, percentage=0.85)
                col = split.column(align=True)
                col.prop_search(cm, "source_name", scn, "objects", text='')
                col = split.column(align=True)
                col.operator("cmlist.select_bricks", icon="BORDER_RECT", text="")
                col = layout.column(align=True)
                row = col.row(align=True)
                row.operator("scene.legoizer_legoize", text="LEGOize Object", icon="MOD_BUILD").action = "CREATE"
            else:
                col = layout.column(align=True)
                col.label("Source Object: " + cm.source_name)
                row = col.row(align=True)
                row.operator("scene.legoizer_delete", text="Delete LEGOized Model", icon="CANCEL")
                col = layout.column(align=True)
                # row = col.row(align=True)
                # row.operator("scene.legoizer_legoize", text="Update Model", icon="FILE_REFRESH").action = "UPDATE"
                split = col.split(align=True, percentage=.85)
                col = split.column(align=True)
                col.operator("scene.legoizer_legoize", text="Update Model", icon="FILE_REFRESH").action = "UPDATE"
                col = split.column(align=True)
                col.operator("cmlist.select_bricks", icon="BORDER_RECT", text="")

            # sub = row.row(align=True)
            # sub.scale_x = 0.1
            # sub.operator("cgcookie.eye_dropper", icon='EYEDROPPER').target_prop = 'source_name'

            col = layout.column(align=True)
            row = col.row(align=True)
            # remove 'LEGOizer_[source name]_bricks' group if empty
            # if groupExists(LEGOizer_bricks) and len(bpy.data.groups[LEGOizer_bricks].objects) == 0:
            #     legoizerDelete.cleanUp()
            #     bpy.data.groups.remove(bpy.data.groups[LEGOizer_bricks], do_unlink=True)
        else:
            layout.operator("cmlist.list_action", icon='ZOOMIN', text="New LEGO Model").action = 'ADD'

class ModelTransformationPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Model Transformation"
    bl_idname      = "VIEW3D_PT_tools_LEGOizer_model_transformation"
    bl_context     = "objectmode"
    bl_category    = "LEGOizer"
    bl_options     = {"DEFAULT_CLOSED"}
    COMPAT_ENGINES = {"CYCLES", "BLENDER_RENDER"}

    @classmethod
    def poll(self, context):
        scn = context.scene
        if scn.cmlist_index == -1:
            return False
        if bversion() < '002.078.00':
            return False
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        if not groupExists('LEGOizer_%(n)s' % locals()):
            return False
        return True

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        col = layout.column(align=True)
        row = col.row(align=True)
        parent = bpy.data.groups['LEGOizer_%(n)s_parent' % locals()].objects[0]
        row = layout.row()
        row.column().prop(parent, "location")
        if parent.rotation_mode == 'QUATERNION':
            row.column().prop(parent, "rotation_quaternion", text="Rotation")
        elif parent.rotation_mode == 'AXIS_ANGLE':
            row.column().prop(parent, "rotation_axis_angle", text="Rotation")
        else:
            row.column().prop(parent, "rotation_euler", text="Rotation")
        row.column().prop(parent, "scale")
        layout.prop(parent, "rotation_mode")

class ModelSettingsPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Model Settings"
    bl_idname      = "VIEW3D_PT_tools_LEGOizer_model_settings"
    bl_context     = "objectmode"
    bl_category    = "LEGOizer"
    COMPAT_ENGINES = {"CYCLES", "BLENDER_RENDER"}

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns false) """
        scn = context.scene
        if scn.cmlist_index == -1:
            return False
        if bversion() < '002.078.00':
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
        row.label("Brick Settings:")
        row = col.row(align=True)
        row.prop(cm, "maxBrickScale")
        row = col.row(align=True)
        row.prop(cm, "mergeSeed")
        col = layout.column(align=True)
        row = col.row(align=True)
        col = layout.column(align=True)
        row = col.row(align=True)
        row.label("Calculation Axes:")
        row = col.row(align=True)
        row.prop(cm, "calculationAxes", text="")

class DetailingPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Detailing"
    bl_idname      = "VIEW3D_PT_tools_LEGOizer_detailing"
    bl_context     = "objectmode"
    bl_category    = "LEGOizer"
    bl_options     = {"DEFAULT_CLOSED"}
    COMPAT_ENGINES = {"CYCLES", "BLENDER_RENDER"}

    @classmethod
    def poll(self, context):
        scn = context.scene
        if scn.cmlist_index == -1:
            return False
        if bversion() < '002.078.00':
            return False
        return True

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        cm = scn.cmlist[scn.cmlist_index]

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(cm, "smoothCylinders")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.label("Studs:")
        row = col.row(align=True)
        row.prop(cm, "studDetail", text="")
        if cm.studDetail != "None":
            row = col.row(align=True)
            row.prop(cm, "studVerts")
            col = layout.column(align=True)
        row = col.row(align=True)
        row.label("Logo:")
        row = col.row(align=True)
        row.prop(cm, "logoDetail", text="")
        if cm.logoDetail != "None":
            row = col.row(align=True)
            row.prop(cm, "logoResolution", text="Logo Resolution")
            col = layout.column(align=True)
        row = col.row(align=True)
        row.label("Underside Hidden:")
        row = col.row(align=True)
        row.prop(cm, "hiddenUndersideDetail", text="")
        row = col.row(align=True)
        row.label("Underside Exposed:")
        row = col.row(align=True)
        row.prop(cm, "exposedUndersideDetail", text="")


class BevelPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Bevel"
    bl_idname      = "VIEW3D_PT_tools_LEGOizer_bevel"
    bl_context     = "objectmode"
    bl_category    = "LEGOizer"
    COMPAT_ENGINES = {"CYCLES", "BLENDER_RENDER"}

    @classmethod
    def poll(self, context):
        scn = context.scene
        if scn.cmlist_index == -1:
            return False
        if bversion() < '002.078.00':
            return False
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        if not groupExists('LEGOizer_%(n)s_bricks' % locals()):
            return False
        return True

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name

        col = layout.column(align=True)
        row = col.row(align=True)
        try:
            testBrick = bpy.data.groups['LEGOizer_%(n)s_bricks' % locals()].objects[0]
            testBrick.modifiers[testBrick.name + '_bevel']
            row.prop(cm, "bevelWidth")
            if not cm.smoothCylinders:
                row = col.row(align=True)
                row.prop(cm, "bevelResolution")
            row = col.row(align=True)
            row.operator("scene.legoizer_bevel", text="Remove Bevel", icon="CANCEL").action = "REMOVE"
        except:
            row.operator("scene.legoizer_bevel", text="Bevel bricks", icon="MOD_BEVEL").action = "CREATE"
