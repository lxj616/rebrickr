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
from ..lib.bricksDict import *
from ..buttons.delete import RebrickrDelete
from ..functions import *
from ..lib.caches import rebrickr_bfm_cache

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
        if not cm.lastSplitModel:
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
        # print bricksDict key for active object
        row = col1.row(align=True)
        try:
            dictKey = scn.objects.active.name.split("__")[1]
            bricksDict,_ = getBricksDict("UPDATE_MODEL", cm=cm)
            brickD = bricksDict[dictKey]
            row.label(brickD["location"])
            row.label()
        except:
            pass

        # next level:
        # enter brick sculpt mode
        # add brick at selected vertex

class RebrickrBrickDetailsPanel(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_label       = "Brick Details"
    bl_idname      = "VIEW3D_PT_tools_Rebrickr_brick_details"
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
        if not (cm.modelCreated or cm.animated):
            return False
        if (rebrickr_bfm_cache[0] != cm.id or rebrickr_bfm_cache[1] is None) and cm.BFMCache == "":
            return False
        return True

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        cm = scn.cmlist[scn.cmlist_index]

        if len(cm.BFMKeys) == 0:
            layout.operator("rebrickr.populate_dict_keys", text="Populate Dict Keys")

        if cm.activeBFMKey != "" or len(cm.BFMKeys) == 0:
            dictKey = cm.activeBFMKey
        else:
            dictKey = cm.BFMKeys[0].name
        bricksDict,_ = getBricksDict("UPDATE_MODEL", cm=cm)
        try:
            brickD = bricksDict[dictKey]
        except Exception as e:
            print("Key", dictKey, "not found")
            return

        col1 = layout.column(align=True)
        if len(cm.BFMKeys) > 0:
            col1.prop_search(cm, "activeBFMKey", cm, "BFMKeys", text="Dict Key")
        # col1.prop(cm, "activeKeyInDetailViewer", text="DictKey")
        split = col1.split(align=True, percentage=0.35)
        # hard code keys so that they are in the order I want
        keys = ["name", "val", "draw", "co", "nearest_face_idx", "mat_name", "parent_brick", "size", "attempted_merge", "top_exposed", "bot_exposed", "type"]
        # keys = list(brickD.keys())
        # keys.sort()
        # draw keys
        col = split.column(align=True)
        col.scale_y = 0.65
        for key in keys:
            row = col.row(align=True)
            row.label(key + ":")
        # draw values
        col = split.column(align=True)
        col.scale_y = 0.65
        for key in keys:
            row = col.row(align=True)
            row.label(str(brickD[key]))
