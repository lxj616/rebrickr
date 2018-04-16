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

# Addon imports
from .cmlist_attrs import *
from .cmlist_actions import *
from .app_handlers import *
from .matlist_window import *
from .matlist_actions import *
from ..lib.bricksDict import *
from ..lib.Brick.test_brick_generators import *
from ..buttons.delete import BrickerDelete
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
    if not bpy.props.bricker_initialized:
        return False
    return True


class BasicMenu(bpy.types.Menu):
    bl_idname      = "Bricker_specials_menu"
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
    bl_idname      = "VIEW3D_PT_tools_Bricker_brick_models"
    bl_context     = "objectmode"
    bl_category    = "Bricker"

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
            col.label('Bricker requires Blender 2.78+')
            return

        # draw UI list and list actions
        if len(scn.cmlist) < 2:
            rows = 2
        else:
            rows = 4
        row = layout.row()
        row.template_list("Bricker_UL_cmlist_items", "", scn, "cmlist", scn, "cmlist_index", rows=rows)

        col = row.column(align=True)
        col.operator("cmlist.list_action" if bpy.props.bricker_initialized else "bricker.initialize", text="", icon="ZOOMIN").action = 'ADD'
        col.operator("cmlist.list_action", icon='ZOOMOUT', text="").action = 'REMOVE'
        col.menu("Bricker_specials_menu", icon='DOWNARROW_HLT', text="")
        if len(scn.cmlist) > 1:
            col.separator()
            col.operator("cmlist.list_action", icon='TRIA_UP', text="").action = 'UP'
            col.operator("cmlist.list_action", icon='TRIA_DOWN', text="").action = 'DOWN'

        # draw menu options below UI list
        if scn.cmlist_index == -1:
            layout.operator("cmlist.list_action" if bpy.props.bricker_initialized else "bricker.initialize", text="New Brick Model", icon="ZOOMIN").action = 'ADD'
        else:
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
                col.operator("bricker.eye_dropper", icon="EYEDROPPER", text="").target_prop = 'source_name'
                col1 = layout.column(align=True)

            # initialize obj variable
            obj = bpy.data.objects.get(cm.source_name)

            # if undo stack not initialized, draw initialize button
            if not bpy.props.bricker_initialized:
                row = col1.row(align=True)
                row.operator("bricker.initialize", text="Initialize Bricker", icon="MODIFIER")
                # draw test brick generator button (for testing purposes only)
                if testBrickGenerators.drawUIButton():
                    col = layout.column(align=True)
                    col.operator("bricker.test_brick_generators", text="Test Brick Generators", icon="OUTLINER_OB_MESH")
            # if use animation is selected, draw animation options
            elif cm.useAnimation:
                if cm.animated:
                    row = col1.row(align=True)
                    row.operator("bricker.delete", text="Delete Brick Animation", icon="CANCEL")
                    col = layout.column(align=True)
                    row = col.row(align=True)
                    row.operator("bricker.brickify", text="Update Animation", icon="FILE_REFRESH")
                    if createdWithUnsupportedVersion():
                        v_str = cm.version[:3]
                        col = layout.column(align=True)
                        col.scale_y = 0.7
                        col.label("Model was created with")
                        col.label("Bricker v%(v_str)s. Please" % locals())
                        col.label("run 'Update Model' so")
                        col.label("it is compatible with")
                        col.label("your current version.")
                else:
                    row = col1.row(align=True)
                    if obj:
                        row.active = obj.type == 'MESH'
                    else:
                        row.active = False
                    row.operator("bricker.brickify", text="Brickify Animation", icon="MOD_REMESH")
            # if use animation is not selected, draw modeling options
            else:
                if not cm.animated and not cm.modelCreated:
                    row = col1.row(align=True)
                    if obj:
                        row.active = obj.type == 'MESH'
                    else:
                        row.active = False
                    row.operator("bricker.brickify", text="Brickify Object", icon="MOD_REMESH")
                else:
                    row = col1.row(align=True)
                    row.operator("bricker.delete", text="Delete Brickified Model", icon="CANCEL")
                    col = layout.column(align=True)
                    col.operator("bricker.brickify", text="Update Model", icon="FILE_REFRESH")
                    if createdWithUnsupportedVersion():
                        v_str = cm.version[:3]
                        col = layout.column(align=True)
                        col.scale_y = 0.7
                        col.label("Model was created with")
                        col.label("Bricker v%(v_str)s. Please" % locals())
                        col.label("run 'Update Model' so")
                        col.label("it is compatible with")
                        col.label("your current version.")
                    elif matrixReallyIsDirty(cm) and cm.customized:
                        row = col.row(align=True)
                        row.label("Customizations will be lost")
                        row = col.row(align=True)
                        row.operator("bricker.revert_matrix_settings", text="Revert Settings", icon="LOOP_BACK")

            col = layout.column(align=True)
            row = col.row(align=True)

        if bpy.data.texts.find('Bricker_log') >= 0:
            split = layout.split(align=True, percentage=0.9)
            col = split.column(align=True)
            row = col.row(align=True)
            row.operator("bricker.report_error", text="Report Error", icon="URL")
            col = split.column(align=True)
            row = col.row(align=True)
            row.operator("bricker.close_report_error", text="", icon="PANEL_CLOSE")


def is_baked(mod):
    return mod.point_cache.is_baked is not False


class AnimationPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Animation"
    bl_idname      = "VIEW3D_PT_tools_Bricker_animation"
    bl_context     = "objectmode"
    bl_category    = "Bricker"
    bl_options     = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(self, context):
        if not settingsCanBeDrawn():
            return False
        scn, cm, _ = getActiveContextInfo()
        if cm.modelCreated:
            return False
        # groupExistsBool = groupExists(Bricker_bricks) or groupExists("Bricker_%(n)s" % locals()) or groupExists("Bricker_%(n)s_refBricks" % locals())
        # if groupExistsBool:
        #     return False
        # cm = scn.cmlist[scn.cmlist_index]
        # n = cm.source_name
        # if not groupExists('Bricker_%(n)s' % locals()):
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
            if source:
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
    bl_idname      = "VIEW3D_PT_tools_Bricker_model_transform"
    bl_context     = "objectmode"
    bl_category    = "Bricker"
    bl_options     = {"DEFAULT_CLOSED"}

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

        if not cm.lastSplitModel:
            col.scale_y = 0.7
            row.label("Use Blender's built-in")
            row = col.row(align=True)
            row.label("transformation manipulators")
            col = layout.column(align=True)
            return

        row.prop(cm, "applyToSourceObject")
        if cm.animated or (cm.lastSplitModel and cm.modelCreated):
            row = col.row(align=True)
            row.prop(cm, "exposeParent")
        row = col.row(align=True)
        parent = bpy.data.objects['Bricker_%(n)s_parent' % locals()]
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
    bl_idname      = "VIEW3D_PT_tools_Bricker_model_settings"
    bl_context     = "objectmode"
    bl_category    = "Bricker"

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns false) """
        if not settingsCanBeDrawn():
            return False
        return True

    def draw(self, context):
        layout = self.layout
        scn, cm, _ = getActiveContextInfo()
        source = bpy.data.objects.get(cm.source_name)

        col = layout.column(align=True)
        # set up model dimensions variables sX, sY, and sZ
        s = Vector((-1, -1, -1))
        if cm.modelScaleX == -1 or cm.modelScaleY == -1 or cm.modelScaleZ == -1:
            if source:
                source_details = bounds(source, use_adaptive_domain=False)
                s.x = round(source_details.dist.x, 2)
                s.y = round(source_details.dist.y, 2)
                s.z = round(source_details.dist.z, 2)
        else:
            s = Vector((cm.modelScaleX, cm.modelScaleY, cm.modelScaleZ))
        # draw Brick Model dimensions to UI if set
        if -1 not in s:
            if cm.brickType != "CUSTOM":
                dimensions = Bricks.get_dimensions(cm.brickHeight, getZStep(cm), cm.gap)
                full_d = Vector((dimensions["width"],
                                 dimensions["width"],
                                 dimensions["height"]))
                r = vec_div(s, full_d)
            elif cm.brickType == "CUSTOM":
                customObjFound = False
                customObj = bpy.data.objects.get(cm.customObjectName1)
                if customObj and customObj.type == "MESH":
                    custom_details = bounds(customObj)
                    if 0 not in custom_details.dist.to_tuple():
                        mult = (cm.brickHeight / custom_details.dist.z)
                        full_d = Vector((custom_details.dist.x * mult,
                                         custom_details.dist.y * mult,
                                         cm.brickHeight))
                        r = vec_div(s, full_d)
                        customObjFound = True
            if cm.brickType == "CUSTOM" and not customObjFound:
                col.label("[Custom object not found]")
            else:
                split = col.split(align=True, percentage=0.5)
                col1 = split.column(align=True)
                col1.label("Dimensions:")
                col2 = split.column(align=True)
                col2.alignment = "RIGHT"
                col2.label("{}x{}x{}".format(int(r.x), int(r.y), int(r.z)))
        row = col.row(align=True)
        row.prop(cm, "brickHeight")
        row = col.row(align=True)
        row.prop(cm, "gap")
        row = col.row(align=True)
        row.prop(cm, "connectThresh")
        row.active = cm.brickType != "CUSTOM"

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
        if cm.brickShell != "INSIDE":
            row = col.row(align=True)
            row.prop(cm, "calculationAxes", text="")
        row = col.row(align=True)
        row.prop(cm, "shellThickness", text="Thickness")
        obj = bpy.data.objects.get(cm.source_name)
        # if obj and not cm.isWaterTight:
        #     row = col.row(align=True)
        #     # row.scale_y = 0.7
        #     row.label("(Source is NOT single closed mesh)")
        #     # row = col.row(align=True)
        #     # row.operator("scene.make_closed_mesh", text="Make Single Closed Mesh", icon="EDIT")



class SmokeSettingsPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Smoke Settings"
    bl_idname      = "VIEW3D_PT_tools_Bricker_smoke_settings"
    bl_context     = "objectmode"
    bl_category    = "Bricker"
    bl_options     = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns false) """
        if not settingsCanBeDrawn():
            return False
        scn = bpy.context.scene
        if scn.cmlist_index == -1:
            return False
        cm = scn.cmlist[scn.cmlist_index]
        source = bpy.data.objects.get(cm.source_name)
        if source is None:
            return False
        return is_smoke(source)

    def draw(self, context):
        layout = self.layout
        scn, cm, _ = getActiveContextInfo()
        source = bpy.data.objects.get(cm.source_name)

        col = layout.column(align=True)
        if is_smoke(source):
            row = col.row(align=True)
            row.prop(cm, "smokeDensity", text="Density")

        if is_smoke(source):
            col = layout.column(align=True)
            row = col.row(align=True)
            row.label("Smoke Color:")
            row = col.row(align=True)
            row.prop(cm, "smokeBrightness", text="Brightness")
            row = col.row(align=True)
            row.prop(cm, "smokeSaturation", text="Saturation")
            row = col.row(align=True)
            row.label("Flame Color:")
            row = col.row(align=True)
            row.prop(cm, "flameColor", text="")
            row = col.row(align=True)
            row.prop(cm, "flameIntensity", text="Intensity")


class BrickTypesPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Brick Types"
    bl_idname      = "VIEW3D_PT_tools_Bricker_brick_types"
    bl_context     = "objectmode"
    bl_category    = "Bricker"
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

        if cm.brickType != "CUSTOM":
            if cm.brickType == "BRICKS AND PLATES":
                col = layout.column(align=True)
                row = col.row(align=True)
                row.prop(cm, "alignBricks")
                if cm.alignBricks:
                    row = col.row(align=True)
                    row.prop(cm, "offsetBrickLayers")

            if mergableBrickType(cm):
                col = layout.column(align=True)
                col.label("Max Brick Size:")
                row = col.row(align=True)
                row.prop(cm, "maxWidth", text="Width")
                row.prop(cm, "maxDepth", text="Depth")
                row = col.row(align=True)
                row.label("Merge Type:")
                row = col.row(align=True)
                row.prop(cm, "mergeType", text="")
                if cm.mergeType == "RANDOM":
                    row = col.row(align=True)
                    row.prop(cm, "mergeSeed")
                elif cm.mergeType == "GREEDY":
                    row = col.row(align=True)
                    row.prop(cm, "legalBricksOnly")
                row = col.row(align=True)
                row.prop(cm, "mergeInconsistentMats")

        if cm.brickType != "CUSTOM":
            col.label("Custom Brick Objects:")
        else:
            col = layout.column(align=True)
            col.label("Brick Type Object:")
        for prop in ["customObjectName1", "customObjectName2", "customObjectName3"]:
            if prop[-1] == "2" and cm.brickType == "CUSTOM":
                col = layout.column(align=True)
                col.label("Other Objects:")
            split = col.split(align=True, percentage=0.65)
            col1 = split.column(align=True)
            col1.prop_search(cm, prop, scn, "objects", text="")
            col1 = split.column(align=True)
            col1.operator("bricker.eye_dropper", icon="EYEDROPPER", text="").target_prop = prop
            col1 = split.column(align=True)
            col1.operator("bricker.redraw_custom", icon="FILE_REFRESH", text="").target_prop = prop


        if cm.brickType == "CUSTOM":
            col.label("Distance Offset:")
            split = col.split(align=True, percentage=0.333)
            col = split.column(align=True)
            col.prop(cm, "distOffsetX", text="X")
            col = split.column(align=True)
            col.prop(cm, "distOffsetY", text="Y")
            col = split.column(align=True)
            col.prop(cm, "distOffsetZ", text="Z")


class CustomizeModel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Customize Model"
    bl_idname      = "VIEW3D_PT_tools_Bricker_customize_mode"
    bl_context     = "objectmode"
    bl_category    = "Bricker"
    bl_options     = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(self, context):
        if not settingsCanBeDrawn():
            return False
        scn, cm, _ = getActiveContextInfo()
        if createdWithUnsupportedVersion():
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
        # if not bpy.props.bricker_initialized:
        #     layout.operator("bricker.initialize", icon="MODIFIER")
        #     return

        col1 = layout.column(align=True)
        col1.label("Selection:")
        split = col1.split(align=True, percentage=0.5)
        # set top exposed
        col = split.column(align=True)
        col.operator("bricker.select_bricks_by_type", text="By Type")
        # set bottom exposed
        col = split.column(align=True)
        col.operator("bricker.select_bricks_by_size", text="By Size")

        col1 = layout.column(align=True)
        col1.label("Toggle Exposure:")
        split = col1.split(align=True, percentage=0.5)
        # set top exposed
        col = split.column(align=True)
        col.operator("bricker.set_exposure", text="Top").side = "TOP"
        # set bottom exposed
        col = split.column(align=True)
        col.operator("bricker.set_exposure", text="Bottom").side = "BOTTOM"

        col1 = layout.column(align=True)
        col1.label("Brick Operations:")
        split = col1.split(align=True, percentage=0.5)
        # split brick into 1x1s
        col = split.column(align=True)
        col.operator("bricker.split_bricks", text="Split")
        # merge selected bricks
        col = split.column(align=True)
        col.operator("bricker.merge_bricks", text="Merge")
        # Add identical brick on +/- x/y/z
        row = col1.row(align=True)
        row.operator("bricker.draw_adjacent", text="Draw Adjacent Bricks")
        # change brick type
        row = col1.row(align=True)
        row.operator("bricker.change_brick_type", text="Change Type")
        # change material type
        # row = col1.row(align=True)
        # row.operator("bricker.change_brick_material", text="Change Material")
        # additional controls
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(cm, "autoUpdateOnDelete")
        # row = col.row(align=True)
        # row.operator("bricker.redraw_bricks")


class MaterialsPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Materials"
    bl_idname      = "VIEW3D_PT_tools_Bricker_materials"
    bl_context     = "objectmode"
    bl_category    = "Bricker"
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
        obj = bpy.data.objects.get(cm.source_name)

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(cm, "materialType", text="")

        if cm.materialType == "CUSTOM":
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
                row.operator("bricker.apply_material", icon="FILE_TICK")
        elif cm.materialType == "RANDOM":
            col = layout.column(align=True)
            row = col.row(align=True)
            row.prop(cm, "randomMatSeed")
            if cm.modelCreated or cm.animated:
                if cm.materialIsDirty and not cm.lastSplitModel:
                    col = layout.column(align=True)
                    row = col.row(align=True)
                    row.label("Run 'Update Model' to apply changes")
                elif cm.lastMaterialType == cm.materialType or (not cm.useAnimation and cm.lastSplitModel):
                    col = layout.column(align=True)
                    row = col.row(align=True)
                    row.operator("bricker.apply_material", icon="FILE_TICK")
        elif cm.materialType == "SOURCE" and obj:
            col = layout.column(align=True)
            col.active = len(obj.data.uv_layers) > 0
            row = col.row(align=True)
            row.prop(cm, "useUVMap", text="UV Map")
            if cm.useUVMap:
                split = row.split(align=True, percentage=0.75)
                split.prop_search(cm, "uvImageName", bpy.data, "images", text="")
                split.operator("image.open", icon="FILESEL", text="")
            if len(obj.data.vertex_colors) > 0:
                col = layout.column(align=True)
                col.scale_y = 0.7
                col.label("(Vertex colors not supported)")
            if cm.shellThickness > 1 or cm.internalSupports != "NONE":
                if len(obj.data.uv_layers) <= 0:
                    col = layout.column(align=True)
                row = col.row(align=True)
                row.label("Internal Material:")
                row = col.row(align=True)
                row.prop_search(cm, "internalMatName", bpy.data, "materials", text="")
                row = col.row(align=True)
                row.prop(cm, "matShellDepth")
                if cm.modelCreated:
                    row = col.row(align=True)
                    if cm.matShellDepth <= cm.lastMatShellDepth:
                        row.operator("bricker.apply_material", icon="FILE_TICK")
                    else:
                        row.label("Run 'Update Model' to apply changes")

            col = layout.column(align=True)
            row = col.row(align=True)
            row.label("Color Snapping:")
            row = col.row(align=True)
            row.prop(cm, "colorSnap", text="")
            if cm.colorSnap == "RGB":
                row = col.row(align=True)
                row.prop(cm, "colorSnapAmount")
            if cm.colorSnap == "ABS":
                row = col.row(align=True)
                if not brick_materials_installed:
                    row.label("'ABS Plastic Materials' not installed")
                elif scn.render.engine != 'CYCLES':
                    row.label("Switch to 'Cycles' for ABS Materials")
                else:
                    row.prop(cm, "transparentWeight", text="Transparent Weight")

        if cm.materialType == "RANDOM" or (cm.materialType == "SOURCE" and cm.colorSnap == "ABS"):
            matObj = getMatObject(cm)
            if matObj is not None:
                # draw materials UI list and list actions
                numMats = len(matObj.data.materials)
                rows = 5 if numMats > 5 else (numMats if numMats > 2 else 2)
                split = col.split(align=True, percentage=0.85)
                col1 = split.column(align=True)
                col1.template_list("MATERIAL_UL_matslots_example", "", matObj, "material_slots", matObj, "active_material_index", rows=rows)
                col1 = split.column(align=True)
                col1.operator("bricker.mat_list_action", icon='ZOOMOUT', text="").action = 'REMOVE'
                col1.scale_y = 1 + rows
                if not brick_materials_installed:
                    col.label("'ABS Plastic Materials' not installed")
                elif not brick_materials_loaded():
                    col.operator("scene.append_abs_plastic_materials", text="Import Brick Materials", icon="IMPORT")
                else:
                    col.operator("bricker.add_abs_plastic_materials", text="Add ABS Plastic Materials", icon="ZOOMIN")
                col = layout.column(align=True)
                split = col.split(align=True, percentage=0.25)
                col = split.column(align=True)
                col.label("Add:")
                col = split.column(align=True)
                col.prop_search(cm, "targetMaterial", bpy.data, "materials", text="")
                col = layout.column(align=True)

        if cm.materialType == "SOURCE" and obj and scn.render.engine == "CYCLES" and cm.colorSnap != "NONE" and (not cm.useUVMap or len(obj.data.uv_layers) == 0):
            col = layout.column(align=True)
            col.scale_y = 0.5
            col.label("Based on RGB value of")
            col.separator()
            col.label("first 'Diffuse' node")
            col.separator()
            col.separator()
            col.separator()


class DetailingPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Detailing"
    bl_idname      = "VIEW3D_PT_tools_Bricker_detailing"
    bl_context     = "objectmode"
    bl_category    = "Bricker"
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
        row.label("Studs:")
        row = col.row(align=True)
        row.prop(cm, "studDetail", text="")
        row = col.row(align=True)
        row.label("Logo:")
        row = col.row(align=True)
        row.prop(cm, "logoDetail", text="")
        if cm.logoDetail != "NONE":
            if cm.logoDetail == "LEGO":
                row = col.row(align=True)
                row.prop(cm, "logoResolution", text="Resolution")
                row.prop(cm, "logoDecimate", text="Decimate")
                row = col.row(align=True)
            else:
                row = col.row(align=True)
                split = row.split(align=True, percentage=0.85)
                col1 = split.column(align=True)
                col1.prop_search(cm, "logoObjectName", scn, "objects", text="")
                col1 = split.column(align=True)
                col1.operator("bricker.eye_dropper", icon="EYEDROPPER", text="").target_prop = 'logoObjectName'
                row = col.row(align=True)
                row.prop(cm, "logoScale", text="Scale")
            row.prop(cm, "logoInset", text="Inset")
            col = layout.column(align=True)
        row = col.row(align=True)
        row.label("Underside:")
        row = col.row(align=True)
        row.prop(cm, "hiddenUndersideDetail", text="")
        row.prop(cm, "exposedUndersideDetail", text="")
        row = col.row(align=True)
        row.label("Cylinders:")
        row = col.row(align=True)
        row.prop(cm, "circleVerts")
        row.active = not (cm.studDetail == "NONE" and cm.exposedUndersideDetail == "FLAT" and cm.hiddenUndersideDetail == "FLAT")

        row = col.row(align=True)
        row.label("Bevel:")
        if cm.lastBrickType == "CUSTOM":
            col = layout.column(align=True)
            col.scale_y = 0.7
            col.label("Not available for custom")
            col.label("brick types")
            return
        row = col.row(align=True)
        if not (cm.modelCreated or cm.animated):
            row.prop(cm, "bevelAdded", text="Bevel Bricks")
            return
        try:
            ff = cm.lastStartFrame
            testBrick = getBricks()[0]
            testBrick.modifiers[testBrick.name + '_bvl']
            row.prop(cm, "bevelWidth", text="Width")
            row = col.row(align=True)
            row.prop(cm, "bevelSegments", text="Segments")
            row = col.row(align=True)
            row.prop(cm, "bevelProfile", text="Profile")
            row = col.row(align=True)
            row.operator("bricker.bevel", text="Remove Bevel", icon="CANCEL")
        except (IndexError, KeyError):
            row.operator("bricker.bevel", text="Bevel bricks", icon="MOD_BEVEL")


class SupportsPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Supports"
    bl_idname      = "VIEW3D_PT_tools_Bricker_supports"
    bl_context     = "objectmode"
    bl_category    = "Bricker"
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
        if cm.internalSupports == "LATTICE":
            row.prop(cm, "latticeStep")
            row = col.row(align=True)
            row.prop(cm, "alternateXY")
        elif cm.internalSupports == "COLUMNS":
            row.prop(cm, "colThickness")
            row = col.row(align=True)
            row.prop(cm, "colStep")
        obj = bpy.data.objects.get(cm.source_name)
        # if obj and not cm.isWaterTight:
        #     row = col.row(align=True)
        #     # row.scale_y = 0.7
        #     row.label("(Source is NOT single closed mesh)")


class AdvancedPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Advanced"
    bl_idname      = "VIEW3D_PT_tools_Bricker_advanced"
    bl_context     = "objectmode"
    bl_category    = "Bricker"
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
            col.label("Bricker update available!", icon="INFO")
            col.label("Install from Bricker addon prefs")
            layout.separator()

        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("bricker.clear_cache", text="Clear Cache")
        row = col.row(align=True)
        row.label("Insideness:")
        row = col.row(align=True)
        row.prop(cm, "insidenessRayCastDir", text="")
        row = col.row(align=True)
        row.prop(cm, "castDoubleCheckRays")
        row = col.row(align=True)
        row.prop(cm, "useNormals")
        if not cm.useAnimation and not (cm.modelCreated or cm.animated):
            row = col.row(align=True)
            row.label("Model Orientation:")
            row = col.row(align=True)
            row.prop(cm, "useLocalOrient", text="Use Source Local")
        # draw test brick generator button (for testing purposes only)
        if testBrickGenerators.drawUIButton():
            col = layout.column(align=True)
            col.operator("bricker.test_brick_generators", text="Test Brick Generators", icon="OUTLINER_OB_MESH")


class BrickDetailsPanel(Panel):
    """ Display Matrix details for specified brick location """
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Brick Details"
    bl_idname      = "VIEW3D_PT_tools_Bricker_brick_details"
    bl_context     = "objectmode"
    bl_category    = "Bricker"
    bl_options     = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(self, context):
        if bpy.props.bricker_developer_mode < 1:
            return False
        if not settingsCanBeDrawn():
            return False
        scn, cm, _ = getActiveContextInfo()
        if createdWithUnsupportedVersion():
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
            bricksDict, _ = getBricksDict(dType="ANIM", cm=cm, curFrame=getAnimAdjustedFrame(cm, scn.frame_current))
        elif cm.modelCreated:
            bricksDict, _ = getBricksDict(cm=cm)
        if bricksDict is None:
            layout.label("Matrix not available")
            return
        try:
            dictKey = listToStr([cm.activeKeyX, cm.activeKeyY, cm.activeKeyZ])
            brickD = bricksDict[dictKey]
        except Exception as e:
            layout.label("No brick details available")
            if len(bricksDict) == 0:
                print("[Bricker] Skipped drawing Brick Details")
            elif str(e)[1:-1] == dictKey:
                pass
                # print("[Bricker] Key '" + str(dictKey) + "' not found")
            elif dictKey is None:
                print("[Bricker] Key not set (entered else)")
            else:
                print("[Bricker] Error fetching brickD:", e)
            return

        col1 = layout.column(align=True)
        split = col1.split(align=True, percentage=0.35)
        # hard code keys so that they are in the order I want
        keys = ["name", "val", "draw", "co", "near_face", "near_intersection", "near_normal", "mat_name", "rgba", "parent", "size", "attempted_merge", "top_exposed", "bot_exposed", "type", "flipped", "rotated", "created_from"]
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

class ExportPanel(Panel):
    """ Export Bricker Model """
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Export"
    bl_idname      = "VIEW3D_PT_tools_Bricker_export"
    bl_context     = "objectmode"
    bl_category    = "Bricker"
    bl_options     = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(self, context):
        if not settingsCanBeDrawn():
            return False
        scn, cm, _ = getActiveContextInfo()
        if createdWithUnsupportedVersion():
            return False
        if not (cm.modelCreated or cm.animated):
            return False
        return True

    def draw(self, context):
        layout = self.layout
        scn, cm, _ = getActiveContextInfo()

        col = layout.column(align=True)
        col.prop(cm, "exportPath", text="")
        col = layout.column(align=True)
        if bpy.props.bricker_developer_mode > 0:
            row = col.row(align=True)
            row.operator("bricker.export_model_data", text="Export Model Data", icon="EXPORT")
        if (cm.modelCreated or cm.animated) and cm.brickType != "CUSTOM":
            row = col.row(align=True)
            row.operator("bricker.export_ldraw", text="Export Ldraw", icon="EXPORT")
