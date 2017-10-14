bl_info = {
    "name"        : "Rebrickr",
    "author"      : "Christopher Gearhart <chris@bblanimation.com>",
    "version"     : (1, 0, 1),
    "blender"     : (2, 78, 0),
    "description" : "Turn any mesh into a 3D brick sculpture or simulation with the click of a button",
    "location"    : "View3D > Tools > Rebrickr",
    "warning"     : "",  # used for warning icon and text in addons panel
    "wiki_url"    : "https://www.blendermarket.com/creator/products/rebrickr/",
    "tracker_url" : "https://github.com/bblanimation/rebrickr/issues",
    "category"    : "Object"}

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
from bpy.props import *
from bpy.types import Operator, AddonPreferences
props = bpy.props

# Rebrickr imports
from .ui import *
from .buttons import *
from .eyedropper import *

# updater import
from . import addon_updater_ops

# store keymaps here to access after registration
addon_keymaps = []

class RebrickrPreferences(AddonPreferences):
    bl_idname = __package__

    # cacheing preferences
    useCaching = BoolProperty(
            name="Use Cacheing",
            description="Store brick meshes and sculpture matrices to speed up operator run times (up to 3x speed boost)",
            default=True)

	# addon updater preferences
    auto_check_update = bpy.props.BoolProperty(
        name = "Auto-check for Update",
        description = "If enabled, auto-check for updates using an interval",
        default = False)
    updater_intrval_months = bpy.props.IntProperty(
        name='Months',
        description = "Number of months between checking for updates",
        default=0, min=0)
    updater_intrval_days = bpy.props.IntProperty(
        name='Days',
        description = "Number of days between checking for updates",
        default=7, min=0)
    updater_intrval_hours = bpy.props.IntProperty(
        name='Hours',
        description = "Number of hours between checking for updates",
        min=0, max=23,
        default=0)
    updater_intrval_minutes = bpy.props.IntProperty(
        name='Minutes',
        description = "Number of minutes between checking for updates",
        min=0, max=59,
        default=0)

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "useCaching")

        # updater draw function
        addon_updater_ops.update_settings_ui(self,context)

def deleteUnprotected(context, use_global=False):
    scn = context.scene
    protected = []
    for obj in context.selected_objects:
        if obj.isBrickifiedObject or obj.isBrick:
            cm = None
            for cmCur in scn.cmlist:
                n = cmCur.source_name
                if "Rebrickr_%(n)s_bricks_combined" % locals() in obj.name:
                    cm = cmCur
                    break
                elif "Rebrickr_%(n)s_brick_" % locals() in obj.name:
                    bGroup = bpy.data.groups.get("Rebrickr_%(n)s_bricks" % locals())
                    if bGroup is not None and len(bGroup.objects) < 2:
                        cm = cmCur
                        break
            if cm is not None:
                RebrickrDelete.runFullDelete(cm=cm)
                scn.objects.active.select = False
            else:
                obj_users_scene = len(obj.users_scene)
                scn.objects.unlink(obj)
                if use_global or obj_users_scene == 1:
                    bpy.data.objects.remove(obj, True)
        elif not obj.protected:
            obj_users_scene = len(obj.users_scene)
            scn.objects.unlink(obj)
            if use_global or obj_users_scene == 1:
                bpy.data.objects.remove(obj, True)
        else:
            print(obj.name +' is protected')
            protected.append(obj.name)

    return protected

class delete_override(bpy.types.Operator):
    """OK?"""
    bl_idname = "object.delete"
    bl_label = "Delete"
    bl_options = {'REGISTER', 'INTERNAL'}

    use_global = BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        # return context.active_object is not None
        return True

    def runDelete(self, context):
        protected = deleteUnprotected(context, self.use_global)
        if len(protected) > 0:
            self.report({"WARNING"}, "Rebrickr is using the following object(s): " + str(protected)[1:-1])
        # push delete action to undo stack
        bpy.ops.ed.undo_push(message="Delete")

    def execute(self, context):
        self.runDelete(context)
        return {'FINISHED'}

    def invoke(self, context, event):
        # Run confirmation popup for delete action
        confirmation_returned = context.window_manager.invoke_confirm(self, event)
        if confirmation_returned != {'FINISHED'}:
            return confirmation_returned
        else:
            self.runDelete(context)
            return {'FINISHED'}


def register():
    bpy.utils.register_module(__name__)

    bpy.props.rebrickr_module_name = __name__

    bpy.types.Object.protected = props.BoolProperty(name='protected', default=False)
    bpy.types.Object.isBrickifiedObject = props.BoolProperty(name='Is Brickified Object', default=False)
    bpy.types.Object.isBrick = props.BoolProperty(name='Is Brick', default=False)

    bpy.types.Scene.Rebrickr_printTimes = BoolProperty(default=False)
    bpy.props.Rebrickr_origScene = StringProperty(default="")
    bpy.props.Rebrickr_commitEdits = False

    bpy.types.Scene.Rebrickr_runningOperation = BoolProperty(default=False)
    bpy.types.Scene.Rebrickr_last_layers = StringProperty(default="")
    bpy.types.Scene.Rebrickr_last_cmlist_index = IntProperty(default=-2)
    bpy.types.Scene.Rebrickr_active_object_name = StringProperty(default="")
    bpy.types.Scene.Rebrickr_last_active_object_name = StringProperty(default="")

    bpy.types.Scene.Rebrickr_copy_from_id = IntProperty(default=-1)

    bpy.props.abs_plastic_materials = [
        'ABS Plastic Black',
        'ABS Plastic Blue',
        'ABS Plastic Bright Green',
        'ABS Plastic Brown',
        'ABS Plastic Dark Azur',
        'ABS Plastic Dark Green',
        'ABS Plastic Dark Grey',
        'ABS Plastic Dark Red',
        'ABS Plastic Gold',
        'ABS Plastic Green',
        'ABS Plastic Light Bluish Grey',
        'ABS Plastic Light Grey',
        'ABS Plastic Lime',
        'ABS Plastic Orange',
        'ABS Plastic Pink',
        'ABS Plastic Purple',
        'ABS Plastic Red',
        'ABS Plastic Tan',
        'ABS Plastic Trans-Blue',
        'ABS Plastic Trans-Clear',
        'ABS Plastic Trans-Light Green',
        'ABS Plastic Trans-Red',
        'ABS Plastic Trans-Yellow',
        'ABS Plastic White',
        'ABS Plastic Yellow']

    bpy.props.abs_plastic_materials_for_random = [
        'ABS Plastic Black',
        'ABS Plastic Blue',
        'ABS Plastic Bright Green',
        'ABS Plastic Brown',
        'ABS Plastic Dark Azur',
        'ABS Plastic Dark Green',
        'ABS Plastic Dark Grey',
        'ABS Plastic Dark Red',
        'ABS Plastic Gold',
        'ABS Plastic Green',
        'ABS Plastic Light Grey',
        'ABS Plastic Lime',
        'ABS Plastic Orange',
        'ABS Plastic Pink',
        'ABS Plastic Purple',
        'ABS Plastic Red',
        'ABS Plastic Tan',
        'ABS Plastic White',
        'ABS Plastic Yellow']

    # handle the keymap
    wm = bpy.context.window_manager
    # Note that in background mode (no GUI available), keyconfigs are not available either, so we have
    # to check this to avoid nasty errors in background case.
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')
        kmi = km.keymap_items.new("rebrickr.brickify", 'L', 'PRESS', alt=True, shift=True)
        kmi = km.keymap_items.new("rebrickr.delete", 'D', 'PRESS', alt=True, shift=True)#, ctrl=True)
        kmi = km.keymap_items.new("rebrickr.edit_source", 'TAB', 'PRESS', alt=True)#, ctrl=True)
        addon_keymaps.append(km)

    # other things (UI List)
    bpy.types.Scene.cmlist = CollectionProperty(type=Rebrickr_CreatedModels)
    bpy.types.Scene.cmlist_index = IntProperty(default=-1)

    # addon updater code and configurations
    addon_updater_ops.register(bl_info)

def unregister():
    Scn = bpy.types.Scene

    # addon updater unregister
    addon_updater_ops.unregister()

    del Scn.cmlist_index
    del Scn.cmlist
    del bpy.props.abs_plastic_materials_for_random
    del bpy.props.abs_plastic_materials
    del Scn.Rebrickr_copy_from_id
    del Scn.Rebrickr_last_active_object_name
    del Scn.Rebrickr_active_object_name
    del Scn.Rebrickr_last_cmlist_index
    del Scn.Rebrickr_last_layers
    del Scn.Rebrickr_runningOperation
    del bpy.props.Rebrickr_commitEdits
    del bpy.props.Rebrickr_origScene
    del Scn.Rebrickr_printTimes
    del bpy.props.rebrickr_module_name
    del bpy.types.Object.isBrick
    del bpy.types.Object.isBrickifiedObject
    del bpy.types.Object.protected


    # handle the keymaps
    wm = bpy.context.window_manager
    for km in addon_keymaps:
        wm.keyconfigs.addon.keymaps.remove(km)
    addon_keymaps.clear()

    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
