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
from .cmlist import *
from .app_handlers import *
from ..lib.bricksDict import *
from ..lib.abs_plastic_materials import getAbsPlasticMaterials
from ..buttons.delete import RebrickrDelete
from ..buttons.revertSettings import *
from ..buttons.cache import *
from ..functions import *

# updater import
from .. import addon_updater_ops


def settingsCanBeDrawn():
    scn = bpy.context.scene
    if scn.cmlist_index == -1:
        return False
    if bversion() < '002.078.00':
        return False
    if not bpy.props.rebrickr_initialized:
        return False
    return True


class BasicMenu(bpy.types.Menu):
    bl_idname      = "Rebrickr_specials_menu"
    bl_label       = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("cmlist.copy_to_others", icon="COPY_ID", text="Copy Settings to Others")
        layout.operator("cmlist.copy_settings", icon="COPYDOWN", text="Copy Settings")
        layout.operator("cmlist.paste_settings", icon="PASTEDOWN", text="Paste Settings")


class BrickModelsPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Brick Models"
    bl_idname      = "VIEW3D_PT_tools_Rebrickr_brick_models"
    bl_context     = "objectmode"
    bl_category    = "Rebrickr"

    @classmethod
    def poll(self, context):
        return True

    def draw(self, context):
        layout = self.layout
        scn = context.scene

        # draw auto-updater update box
        addon_updater_ops.update_notice_box_ui(self, context)

        # if blender version is before 2.78, ask user to upgrade Blender
        if bversion() < '002.078.00':
            col = layout.column(align=True)
            col.label('ERROR: upgrade needed', icon='ERROR')
            col.label('Rebrickr requires Blender 2.78+')
            return

        # draw UI list and list actions
        if len(scn.cmlist) < 2:
            rows = 2
        else:
            rows = 4
        row = layout.row()
        row.template_list("Rebrickr_UL_items", "", scn, "cmlist", scn, "cmlist_index", rows=rows)

        col = row.column(align=True)
        col.operator("cmlist.list_action", icon='ZOOMIN', text="").action = 'ADD'
        col.operator("cmlist.list_action", icon='ZOOMOUT', text="").action = 'REMOVE'
        col.menu("Rebrickr_specials_menu", icon='DOWNARROW_HLT', text="")
        if len(scn.cmlist) > 1:
            col.separator()
            col.operator("cmlist.list_action", icon='TRIA_UP', text="").action = 'UP'
            col.operator("cmlist.list_action", icon='TRIA_DOWN', text="").action = 'DOWN'

        # draw menu options below UI list
        if scn.cmlist_index != -1:
            cm = scn.cmlist[scn.cmlist_index]
            n = cm.source_name
            # first, draw source object text
            source_name = " %(n)s" % locals() if cm.animated or cm.modelCreated else ""
            col1 = layout.column(align=True)
            col1.label("Source Object:%(source_name)s" % locals())
            if not (cm.animated or cm.modelCreated):
                split = col1.split(align=True, percentage=0.85)
                col = split.column(align=True)
                col.prop_search(cm, "source_name", scn, "objects", text='')
                col = split.column(align=True)
                col.operator("rebrickr.eye_dropper", icon="EYEDROPPER", text="").target_prop = 'source_name'
                # col.operator("cmlist.set_to_active", icon="EDIT", text="")
                col1 = layout.column(align=True)

            # initialize obj variable
            if cm.modelCreated or cm.animated:
                obj = bpy.data.objects.get(cm.source_name + " (DO NOT RENAME)")
            else:
                obj = bpy.data.objects.get(cm.source_name)

            # if undo stack not initialized, draw initialize button
            if not bpy.props.rebrickr_initialized:
                row = col1.row(align=True)
                row.operator("rebrickr.customize_model", text="Initialize Rebrickr", icon="MODIFIER")
            # if use animation is selected, draw animation options
            elif cm.useAnimation:
                if cm.animated:
                    row = col1.row(align=True)
                    row.operator("rebrickr.delete", text="Delete Brick Animation", icon="CANCEL")
                    col = layout.column(align=True)
                    row = col.row(align=True)
                    row.operator("rebrickr.brickify", text="Update Animation", icon="FILE_REFRESH")
                    if cm.version[:3] == "1_0":
                        col = layout.column(align=True)
                        col.scale_y = 0.7
                        col.label("Model was created with")
                        col.label("Rebrickr v1.0. Please")
                        col.label("run 'Update Model' so")
                        col.label("it is compatible with")
                        col.label("your current version.")
                else:
                    row = col1.row(align=True)
                    if obj:
                        row.active = obj.type == 'MESH'
                    else:
                        row.active = False
                    row.operator("rebrickr.brickify", text="Brickify Animation", icon="MOD_REMESH")
            # if use animation is not selected, draw modeling options
            else:
                if not cm.animated and not cm.modelCreated:
                    row = col1.row(align=True)
                    if obj:
                        row.active = obj.type == 'MESH'
                    else:
                        row.active = False
                    row.operator("rebrickr.brickify", text="Brickify Object", icon="MOD_REMESH")
                else:
                    row = col1.row(align=True)
                    row.operator("rebrickr.delete", text="Delete Brickified Model", icon="CANCEL")
                    col = layout.column(align=True)
                    col.operator("rebrickr.brickify", text="Update Model", icon="FILE_REFRESH")
                    if cm.version[:3] == "1_0":
                        col = layout.column(align=True)
                        col.scale_y = 0.7
                        col.label("Model was created with")
                        col.label("Rebrickr v1.0. Please")
                        col.label("run 'Update Model' so")
                        col.label("it is compatible with")
                        col.label("your current version.")
                    elif matrixReallyIsDirty(cm) and cm.customized:
                        row = col.row(align=True)
                        row.label("Customizations will be lost")
                        row = col.row(align=True)
                        row.operator("rebrickr.revert_matrix_settings", text="Revert Settings", icon="LOOP_BACK")

            col = layout.column(align=True)
            row = col.row(align=True)
        else:
            layout.operator("cmlist.list_action", icon='ZOOMIN', text="New Brick Model").action = 'ADD'

        if bpy.data.texts.find('Rebrickr_log') >= 0:
            split = layout.split(align=True, percentage=0.9)
            col = split.column(align=True)
            row = col.row(align=True)
            row.operator("rebrickr.report_error", text="Report Error", icon="URL")
            col = split.column(align=True)
            row = col.row(align=True)
            row.operator("rebrickr.close_report_error", text="", icon="PANEL_CLOSE")


def is_baked(mod):
    return mod.point_cache.is_baked is not False


class AnimationPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Animation"
    bl_idname      = "VIEW3D_PT_tools_Rebrickr_animation"
    bl_context     = "objectmode"
    bl_category    = "Rebrickr"
    bl_options     = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(self, context):
        if not settingsCanBeDrawn():
            return False
        scn, cm, _ = getActiveContextInfo()
        if cm.modelCreated:
            return False
        # groupExistsBool = groupExists(Rebrickr_bricks) or groupExists("Rebrickr_%(n)s" % locals()) or groupExists("Rebrickr_%(n)s_refBricks" % locals())
        # if groupExistsBool:
        #     return False
        # cm = scn.cmlist[scn.cmlist_index]
        # n = cm.source_name
        # if not groupExists('Rebrickr_%(n)s' % locals()):
        #     return False
        return True

    def draw(self, context):
        layout = self.layout
        scn, cm, _ = getActiveContextInfo()

        if not cm.animated:
            col = layout.column(align=True)
            col.prop(cm, "useAnimation")
        if cm.useAnimation:
            col1 = layout.column(align=True)
            col1.active = cm.animated or cm.useAnimation
            col1.scale_y = 0.85
            row = col1.row(align=True)
            split = row.split(align=True, percentage=0.5)
            col = split.column(align=True)
            col.prop(cm, "startFrame")
            col = split.column(align=True)
            col.prop(cm, "stopFrame")
            source = bpy.data.objects.get(cm.source_name)
            self.appliedMods = False
            if source is not None:
                for mod in source.modifiers:
                    if mod.type in ["CLOTH", "SOFT_BODY"] and mod.show_viewport:
                        self.appliedMods = True
                        t = mod.type
                        if mod.point_cache.frame_end < cm.stopFrame:
                            s = str(max([mod.point_cache.frame_end+1, cm.startFrame]))
                            e = str(cm.stopFrame)
                        elif mod.point_cache.frame_start > cm.startFrame:
                            s = str(cm.startFrame)
                            e = str(min([mod.point_cache.frame_start-1, cm.stopFrame]))
                        else:
                            s = "0"
                            e = "-1"
                        totalSkipped = int(e) - int(s) + 1
                        if totalSkipped > 0:
                            row = col1.row(align=True)
                            row.label("Frames %(s)s-%(e)s outside of %(t)s simulation" % locals())
                        numF = (int(e))-(int(s))+1
                        numF = (cm.stopFrame - cm.startFrame + 1) - totalSkipped
                        if numF == 1:
                            numTimes = "once"
                        elif numF == 2:
                            numTimes = "twice"
                        else:
                            numTimes = "%(numF)s times" % locals()
                        row = col1.row(align=True)
                        row.label("%(t)s simulation will bake %(numTimes)s" % locals())
                        # calculate number of frames to bake
                        totalFramesToBake = 0
                        for i in range(cm.startFrame, cm.stopFrame + 1):
                            totalFramesToBake += i - mod.point_cache.frame_start + 1
                        row = col1.row(align=True)
                        row.label("Num frames to bake: %(totalFramesToBake)s" % locals())
            if (cm.stopFrame - cm.startFrame > 10 and not cm.animated) or self.appliedMods:
                col = layout.column(align=True)
                col.scale_y = 0.7
                col.label("WARNING: May take a while.")
                col.separator()
                col.label("Watch the progress in")
                col.label("the command line.")
                col.separator()


class ModelTransformPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Model Transform"
    bl_idname      = "VIEW3D_PT_tools_Rebrickr_model_transform"
    bl_context     = "objectmode"
    bl_category    = "Rebrickr"

    @classmethod
    def poll(self, context):
        if not settingsCanBeDrawn():
            return False
        scn, cm, _ = getActiveContextInfo()
        if cm.modelCreated or cm.animated:
            return True
        return False

    def draw(self, context):
        layout = self.layout
        scn, cm, n = getActiveContextInfo()

        col = layout.column(align=True)
        row = col.row(align=True)

        row.prop(cm, "applyToSourceObject")
        if cm.animated or (cm.lastSplitModel and cm.modelCreated):
            row = col.row(align=True)
            row.prop(cm, "exposeParent")
        row = col.row(align=True)
        parent = bpy.data.objects['Rebrickr_%(n)s_parent' % locals()]
        row = layout.row()
        row.column().prop(parent, "location")
        if parent.rotation_mode == 'QUATERNION':
            row.column().prop(parent, "rotation_quaternion", text="Rotation")
        elif parent.rotation_mode == 'AXIS_ANGLE':
            row.column().prop(parent, "rotation_axis_angle", text="Rotation")
        else:
            row.column().prop(parent, "rotation_euler", text="Rotation")
        # row.column().prop(parent, "scale")
        layout.prop(parent, "rotation_mode")
        layout.prop(cm, "transformScale")


class ModelSettingsPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Model Settings"
    bl_idname      = "VIEW3D_PT_tools_Rebrickr_model_settings"
    bl_context     = "objectmode"
    bl_category    = "Rebrickr"

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns false) """
        if not settingsCanBeDrawn():
            return False
        return True

    def draw(self, context):
        layout = self.layout
        scn, cm, _ = getActiveContextInfo()

        col = layout.column(align=True)
        # set up model dimensions variables sX, sY, and sZ
        if cm.modelScaleX == -1 or cm.modelScaleY == -1 or cm.modelScaleZ == -1:
            if not cm.modelCreated and not cm.animated:
                source = bpy.data.objects.get(cm.source_name)
            else:
                source = bpy.data.objects.get(cm.source_name + " (DO NOT RENAME)")
            if source is not None:
                source_details = bounds(source)
                sX = round(source_details.x.dist, 2)
                sY = round(source_details.y.dist, 2)
                sZ = round(source_details.z.dist, 2)
            else:
                sX = -1
                sY = -1
                sZ = -1
        else:
            sX = cm.modelScaleX
            sY = cm.modelScaleY
            sZ = cm.modelScaleZ
        # draw Brick Model dimensions to UI if set
        if sX != -1 and sY != -1 and sZ != -1:
            noCustomObj = False
            if cm.brickType in ["Bricks", "Plates", "Bricks and Plates"]:
                zStep = getZStep(cm)
                dimensions = Bricks.get_dimensions(cm.brickHeight, zStep/3, cm.gap)
                rX = int(sX/dimensions["width"])
                rY = int(sY/dimensions["width"])
                rZ = int(sZ/dimensions["height"])
            elif cm.brickType == "Custom":
                customObj = bpy.data.objects.get(cm.customObjectName)
                if customObj is not None and customObj.type == "MESH":
                    custom_details = bounds(customObj)
                    if custom_details.x.dist != 0 and custom_details.y.dist != 0 and custom_details.z.dist != 0:
                        multiplier = (cm.brickHeight/custom_details.z.dist)
                        rX = int(sX/(custom_details.x.dist * multiplier))
                        rY = int(sY/(custom_details.y.dist * multiplier))
                        rZ = int(sZ/cm.brickHeight)
                    else:
                        noCustomObj = True
                else:
                    noCustomObj = True
            if noCustomObj:
                col.label("[Custom object not found]")
            else:
                split = col.split(align=True, percentage=0.5)
                col1 = split.column(align=True)
                col1.label("~Num Bricks:")
                col2 = split.column(align=True)
                col2.alignment = "RIGHT"
                col2.label("%(rX)s x %(rY)s x %(rZ)s" % locals())
        row = col.row(align=True)
        row.prop(cm, "brickHeight")
        row = col.row(align=True)
        row.prop(cm, "gap")
        row = col.row(align=True)
        row.prop(cm, "mergeSeed")
        col = layout.column(align=True)
        row = col.row(align=True)

        if not cm.useAnimation:
            row = col.row(align=True)
            row.prop(cm, "splitModel")

        row = col.row(align=True)
        row.label("Randomize:")
        row = col.row(align=True)
        split = row.split(align=True, percentage=0.5)
        col1 = split.column(align=True)
        col1.prop(cm, "randomLoc", text="Location")
        col2 = split.column(align=True)
        col2.prop(cm, "randomRot", text="Rotation")

        row = col.row(align=True)
        row.label("Brick Shell:")
        row = col.row(align=True)
        row.prop(cm, "brickShell", text="")
        if cm.brickShell != "Inside Mesh":
            row = col.row(align=True)
            row.prop(cm, "calculationAxes", text="")
        row = col.row(align=True)
        row.prop(cm, "shellThickness", text="Thickness")
        if cm.modelCreated or cm.animated:
            obj = bpy.data.objects.get(cm.source_name + " (DO NOT RENAME)")
        else:
            obj = bpy.data.objects.get(cm.source_name)
        if obj is not None and not cm.isWaterTight:
            row = col.row(align=True)
            # row.scale_y = 0.7
            row.label("(Source is NOT single closed mesh)")
            # row = col.row(align=True)
            # row.operator("scene.make_closed_mesh", text="Make Single Closed Mesh", icon="EDIT")


class BrickTypesPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Brick Types"
    bl_idname      = "VIEW3D_PT_tools_Rebrickr_brick_types"
    bl_context     = "objectmode"
    bl_category    = "Rebrickr"
    bl_options     = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(self, context):
        if not settingsCanBeDrawn():
            return False
        return True

    def draw(self, context):
        layout = self.layout
        scn, cm, _ = getActiveContextInfo()

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(cm, "brickType", text="")

        if cm.brickType == "Custom":
            col = layout.column(align=True)
            split = col.split(align=True, percentage=0.85)
            col1 = split.column(align=True)
            col1.prop_search(cm, "customObjectName", scn, "objects", text='')
            col1 = split.column(align=True)
            col1.operator("rebrickr.eye_dropper", icon="EYEDROPPER", text="").target_prop = 'customObjectName'

            col = layout.column(align=True)
            col.label("Distance Offset:")
            split = col.split(align=True, percentage=0.333)

            col = split.column(align=True)
            row = col.row(align=True)
            row.prop(cm, "distOffsetX", text="X")

            col = split.column(align=True)
            row = col.row(align=True)
            row.prop(cm, "distOffsetY", text="Y")

            col = split.column(align=True)
            row = col.row(align=True)
            row.prop(cm, "distOffsetZ", text="Z")
        else:
            if cm.brickType == "Bricks and Plates":
                col = layout.column(align=True)
                row = col.row(align=True)
                row.prop(cm, "alignBricks")
                if cm.alignBricks:
                    row = col.row(align=True)
                    row.prop(cm, "offsetBrickLayers")

            col = layout.column(align=True)
            col.label("Max Brick Size:")
            split = col.split(align=True, percentage=0.5)

            col1 = split.column(align=True)
            row1 = col1.row(align=True)
            row1.prop(cm, "maxWidth", text="Width")

            col2 = split.column(align=True)
            row2 = col2.row(align=True)
            row2.prop(cm, "maxDepth", text="Depth")

            if cm.splitModel:
                col = layout.column(align=True)
                row = col.row(align=True)
                row.prop(cm, "originSet")


class MaterialsPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Materials"
    bl_idname      = "VIEW3D_PT_tools_Rebrickr_materials"
    bl_context     = "objectmode"
    bl_category    = "Rebrickr"
    bl_options     = {"DEFAULT_CLOSED"}
    # COMPAT_ENGINES = {"CYCLES", "BLENDER_RENDER"}

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns false) """
        if not settingsCanBeDrawn():
            return False
        return True

    def draw(self, context):
        layout = self.layout
        scn, cm, _ = getActiveContextInfo()

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(cm, "materialType", text="")


        if cm.materialType == "Custom":
            col = layout.column(align=True)
            row = col.row(align=True)
            row.prop_search(cm, "materialName", bpy.data, "materials", text="")
            if brick_materials_installed():
                if bpy.context.scene.render.engine != 'CYCLES':
                    row = col.row(align=True)
                    row.label("Switch to 'Cycles' for Brick materials")
                else:
                    if not brick_materials_loaded():
                        row = col.row(align=True)
                        row.operator("scene.append_abs_plastic_materials", text="Import Brick Materials", icon="IMPORT")
            if cm.modelCreated or cm.animated:
                col = layout.column(align=True)
                row = col.row(align=True)
                row.operator("rebrickr.apply_material", icon="FILE_TICK")
        elif cm.materialType == "Random":
            col = layout.column(align=True)
            if bpy.context.scene.render.engine != 'CYCLES':
                row = col.row(align=True)
                row.label("Switch to 'Cycles Render' engine")
            elif brick_materials_installed:
                if not brick_materials_loaded():
                    row = col.row(align=True)
                    row.operator("scene.append_abs_plastic_materials", text="Import Brick Materials", icon="IMPORT")
                    col = layout.column(align=True)
                    col.scale_y = 0.7
                    col.label("'Brick Materials' must be")
                    col.label("imported")
                else:
                    row = col.row(align=True)
                    row.prop(cm, "randomMatSeed")
                    if cm.modelCreated or cm.animated:
                        if not cm.brickMaterialsAreDirty and ((not cm.useAnimation and cm.lastSplitModel) or (cm.lastMaterialType == cm.materialType)):
                            col = layout.column(align=True)
                            row = col.row(align=True)
                            row.operator("rebrickr.apply_material", icon="FILE_TICK")
                        elif cm.materialIsDirty or cm.brickMaterialsAreDirty:
                            row = col.row(align=True)
                            row.label("Run 'Update Model' to apply changes")

            else:
                col.scale_y = 0.7
                col.label("Requires the 'Brick Materials'")
                col.label("addon, available for purchase")
                col.label("at the Blender Market.")
        elif cm.materialType == "Use Source Materials":
            col = layout.column(align=True)
            row = col.row(align=True)
            row.prop(cm, "mergeInconsistentMats")
            if cm.shellThickness > 1:
                col = layout.column(align=True)
                row = col.row(align=True)
                row.prop(cm, "matShellDepth")
                row = col.row(align=True)
                row.label("Internal:")
                row = col.row(align=True)
                row.prop_search(cm, "internalMatName", bpy.data, "materials", text="")
                if brick_materials_installed:
                    if bpy.context.scene.render.engine != 'CYCLES':
                        row = col.row(align=True)
                        row.label("Switch to 'Cycles' for Brick materials")
                    elif not brick_materials_loaded():
                        row = col.row(align=True)
                        row.operator("scene.append_abs_plastic_materials", text="Import Brick Materials", icon="IMPORT")
                if cm.modelCreated:
                    if cm.splitModel:
                        col = layout.column(align=True)
                        col.label("Run 'Update Model' to apply changes")
                    else:
                        col = layout.column(align=True)
                        row = col.row(align=True)
                        row.operator("rebrickr.apply_material", icon="FILE_TICK")

        if cm.modelCreated or cm.animated:
            obj = bpy.data.objects.get(cm.source_name + " (DO NOT RENAME)")
        else:
            obj = bpy.data.objects.get(cm.source_name)
        if obj is not None and cm.materialType == "Use Source Materials":
            if len(obj.data.uv_layers) > 0:
                row = col.row(align=True)
                row.prop(cm, "useUVMap")
                if cm.useUVMap:
                    row1 = col.row(align=True)
                    row1.prop(cm, "colorSnapAmount")
                    row = col.row(align=True)
                    if not brick_materials_loaded():
                        row.operator("scene.append_abs_plastic_materials", text="Import Brick Materials", icon="IMPORT")
                    else:
                        row.prop(cm, "snapToBrickColors")
                        row1.active = not cm.snapToBrickColors
            col = layout.column(align=True)
            col.scale_y = 0.7
            if len(obj.data.vertex_colors) > 0:
                col.label("(Vertex colors not supported)")


class DetailingPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Detailing"
    bl_idname      = "VIEW3D_PT_tools_Rebrickr_detailing"
    bl_context     = "objectmode"
    bl_category    = "Rebrickr"
    bl_options     = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(self, context):
        if not settingsCanBeDrawn():
            return False
        return True

    def draw(self, context):
        layout = self.layout
        scn, cm, _ = getActiveContextInfo()

        if cm.brickType == "Custom":
            col = layout.column(align=True)
            col.scale_y = 0.7
            col.label("Not available for custom")
            col.label("brick types")
            return

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
            if cm.logoDetail == "LEGO Logo":
                row = col.row(align=True)
                row.prop(cm, "logoResolution", text="Logo Resolution")
            else:
                col = layout.column(align=True)
                split = col.split(align=True, percentage=0.85)
                col1 = split.column(align=True)
                col1.prop_search(cm, "logoObjectName", scn, "objects", text="")
                col1 = split.column(align=True)
                col1.operator("rebrickr.eye_dropper", icon="EYEDROPPER", text="").target_prop = 'logoObjectName'
                row = col.row(align=True)
                row.prop(cm, "logoScale", text="Logo Scale")
                row = col.row(align=True)
                row.prop(cm, "logoInset", text="Logo Inset")
            col = layout.column(align=True)
        row = col.row(align=True)
        row.label("Underside Hidden:")
        row = col.row(align=True)
        row.prop(cm, "hiddenUndersideDetail", text="")
        row = col.row(align=True)
        row.label("Underside Exposed:")
        row = col.row(align=True)
        row.prop(cm, "exposedUndersideDetail", text="")


class SupportsPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Supports"
    bl_idname      = "VIEW3D_PT_tools_Rebrickr_supports"
    bl_context     = "objectmode"
    bl_category    = "Rebrickr"
    bl_options     = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(self, context):
        if not settingsCanBeDrawn():
            return False
        return True

    def draw(self, context):
        layout = self.layout
        scn, cm, _ = getActiveContextInfo()

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(cm, "internalSupports", text="")
        col = layout.column(align=True)
        row = col.row(align=True)
        if cm.internalSupports == "Lattice":
            row.prop(cm, "latticeStep")
            row = col.row(align=True)
            row.prop(cm, "alternateXY")
        elif cm.internalSupports == "Columns":
            row.prop(cm, "colStep")
            row = col.row(align=True)
            row.prop(cm, "colThickness")
        if cm.modelCreated or cm.animated:
            obj = bpy.data.objects.get(cm.source_name + " (DO NOT RENAME)")
        else:
            obj = bpy.data.objects.get(cm.source_name)
        if obj is not None and not cm.isWaterTight:
            row = col.row(align=True)
            # row.scale_y = 0.7
            row.label("(Source is NOT single closed mesh)")


class BevelPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Bevel"
    bl_idname      = "VIEW3D_PT_tools_Rebrickr_bevel"
    bl_context     = "objectmode"
    bl_category    = "Rebrickr"

    @classmethod
    def poll(self, context):
        if not settingsCanBeDrawn():
            return False
        scn, cm, _ = getActiveContextInfo()
        if not bpy.props.rebrickr_initialized:
            return False
        return True

    def draw(self, context):
        layout = self.layout
        scn, cm, n = getActiveContextInfo()

        if cm.lastBrickType == "Custom":
            col = layout.column(align=True)
            col.scale_y = 0.7
            col.label("Not available for custom")
            col.label("brick types")
            return

        col = layout.column(align=True)
        row = col.row(align=True)
        if not (cm.modelCreated or cm.animated):
            row.prop(cm, "bevelAdded", text="Bevel Bricks")
            return
        try:
            ff = cm.lastStartFrame
            testBrick = getBricks()[0]
            testBrick.modifiers[testBrick.name + '_bevel']
            row.prop(cm, "bevelWidth", text="Width")
            row = col.row(align=True)
            row.prop(cm, "bevelSegments", text="Segments")
            row = col.row(align=True)
            row.prop(cm, "bevelProfile", text="Profile")
            row = col.row(align=True)
            row.operator("rebrickr.bevel", text="Remove Bevel", icon="CANCEL")
        except (IndexError, KeyError):
            row.operator("rebrickr.bevel", text="Bevel bricks", icon="MOD_BEVEL")


class CustomizeModel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Customize Model"
    bl_idname      = "VIEW3D_PT_tools_Rebrickr_customize_model"
    # bl_context     = "objectmode"
    bl_category    = "Rebrickr"
    bl_options     = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(self, context):
        if not settingsCanBeDrawn():
            return False
        scn, cm, _ = getActiveContextInfo()
        if cm.version[:3] == "1_0":
            return False
        if not (cm.modelCreated or cm.animated):
            return False
        return True

    def draw(self, context):
        layout = self.layout
        scn, cm, _ = getActiveContextInfo()

        if cm.matrixIsDirty and cm.lastMatrixSettings != getMatrixSettings():
            layout.label("Matrix is dirty!")
            return
        if cm.animated:
            layout.label("Not available for animations")
            return
        if not cm.lastSplitModel:
            layout.label("Split model to customize")
            return
        if cm.buildIsDirty:
            layout.label("Run 'Update Model' to customize")
            return
        if not Caches.cacheExists(cm):
            layout.label("Matrix not cached!")
            return
        # if not bpy.props.rebrickr_initialized:
        #     layout.operator("rebrickr.customize_model", icon="MODIFIER")
        #     return

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
        # row = col1.row(align=True)
        # row.operator("rebrickr.change_brick_type", text="Change Type")
        # additional controls
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(cm, "autoUpdateExposed")
        # row = col.row(align=True)
        # row.operator("rebrickr.redraw_bricks")


class AdvancedPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Advanced"
    bl_idname      = "VIEW3D_PT_tools_Rebrickr_advanced"
    bl_context     = "objectmode"
    bl_category    = "Rebrickr"
    bl_options     = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(self, context):
        if not settingsCanBeDrawn():
            return False
        return True

    def draw(self, context):
        layout = self.layout
        scn, cm, n = getActiveContextInfo()

        # Alert user that update is available
        if addon_updater_ops.updater.update_ready:
            col = layout.column(align=True)
            col.scale_y = 0.7
            col.label("Rebrickr update available!", icon="INFO")
            col.label("Install from Rebrickr addon prefs")
            layout.separator()

        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("rebrickr.clear_cache", text="Clear Cache")
        row = col.row(align=True)
        row.label("Insideness:")
        row = col.row(align=True)
        row.prop(cm, "insidenessRayCastDir", text="")
        row = col.row(align=True)
        row.prop(cm, "castDoubleCheckRays")
        row = col.row(align=True)
        row.prop(cm, "useNormals")
        row = col.row(align=True)
        row.prop(cm, "verifyExposure")
        if not cm.useAnimation and not (cm.modelCreated or cm.animated):
            row = col.row(align=True)
            row.label("Model Orientation:")
            row = col.row(align=True)
            row.prop(cm, "useLocalOrient", text="Use Source Local")


class BrickDetailsPanel(Panel):
    """ for debugging purposes only """
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Brick Details"
    bl_idname      = "VIEW3D_PT_tools_Rebrickr_brick_details"
    # bl_context     = "objectmode"
    bl_category    = "Rebrickr"
    bl_options     = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(self, context):
        # return False # for debugging purposes only
        if not settingsCanBeDrawn():
            return False
        scn, cm, _ = getActiveContextInfo()
        if cm.version[:3] == "1_0":
            return False
        if not (cm.modelCreated or cm.animated):
            return False
        return True

    def draw(self, context):
        layout = self.layout
        scn, cm, _ = getActiveContextInfo()

        if cm.matrixIsDirty and cm.lastMatrixSettings != getMatrixSettings():
            layout.label("Matrix is dirty!")
            return
        if not Caches.cacheExists(cm):
            layout.label("Matrix not cached!")
            return

        col1 = layout.column(align=True)
        split = col1.split(align=True, percentage=0.33)
        col = split.column(align=True)
        col.prop(cm, "activeKeyX", text="x")
        col = split.column(align=True)
        col.prop(cm, "activeKeyY", text="y")
        col = split.column(align=True)
        col.prop(cm, "activeKeyZ", text="z")

        if cm.animated:
            bricksDict, _ = getBricksDict("UPDATE_ANIM", cm=cm, curFrame=getAnimAdjustedFrame(cm, scn.frame_current), restrictContext=True)
        elif cm.modelCreated:
            bricksDict, _ = getBricksDict("UPDATE_MODEL", cm=cm, restrictContext=True)
        if bricksDict is None:
            layout.label("Matrix not available")
            return
        aKX = cm.activeKeyX
        aKY = cm.activeKeyY
        aKZ = cm.activeKeyZ
        try:
            dictKey = listToStr([aKX, aKY, aKZ])
            brickD = bricksDict[dictKey]
        except Exception as e:
            layout.label("No brick details available")
            if len(bricksDict) == 0:
                print("Skipped drawing Brick Details")
            elif str(e)[1:-1] == dictKey:
                print("Key '" + str(dictKey) + "' not found")
                # try:
                #     print("Num Keys:", str(len(bricksDict)))
                # except:
                #     pass
            elif dictKey is None:
                print("Key not set (entered else)")
            else:
                print("Error fetching brickD:", e)
            return

        col1 = layout.column(align=True)
        split = col1.split(align=True, percentage=0.35)
        # hard code keys so that they are in the order I want
        keys = ["name", "val", "draw", "co", "mat_name", "rgba", "parent_brick", "size", "attempted_merge", "top_exposed", "bot_exposed", "type"]
        # draw keys
        col = split.column(align=True)
        col.scale_y = 0.65
        row = col.row(align=True)
        row.label("key:")
        for key in keys:
            row = col.row(align=True)
            row.label(key + ":")
        # draw values
        col = split.column(align=True)
        col.scale_y = 0.65
        row = col.row(align=True)
        row.label(dictKey)
        for key in keys:
            row = col.row(align=True)
            row.label(str(brickD[key]))
