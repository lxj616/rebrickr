bl_info = {
    "name"        : "Rebrickr",
    "author"      : "Christopher Gearhart <chris@bblanimation.com>",
    "version"     : (0, 1, 0),
    "blender"     : (2, 78, 0),
    "description" : "Turn any mesh into a 3D brick sculpture or simulation with the click of a button",
    "location"    : "View3D > Tools > Rebrickr",
    "warning"     : "Work in progress",
    "wiki_url"    : "",
    "tracker_url" : "",
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

# system imports
import bpy
from bpy.props import *
from .ui import *
from .buttons import *
props = bpy.props

# store keymaps here to access after registration
addon_keymaps = []

bpy.types.Object.protected = props.BoolProperty(name = 'protected', default = False)
bpy.types.Object.isBrickifiedObject = props.BoolProperty(name = 'Is Brickified Object', default = False)
bpy.types.Object.isBrick = props.BoolProperty(name = 'Is Brick', default = False)
def deleteUnprotected(context):
    protected = []
    for obj in context.selected_objects:
        if obj.isBrickifiedObject or obj.isBrick:
            scn = context.scene
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
                bpy.context.scene.objects.active.select = False
            else:
                bpy.context.scene.objects.unlink(obj)
                bpy.data.objects.remove(obj)
        elif not obj.protected:
            bpy.context.scene.objects.unlink(obj)
            bpy.data.objects.remove(obj)
        else:
            print(obj.name +' is protected')
            protected.append(obj.name)

    return protected

class delete_override(bpy.types.Operator):
    """OK?"""
    bl_idname = "object.delete"
    bl_label = "Delete"
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        # return context.active_object is not None
        return True

    def runDelete(self, context):
        protected = deleteUnprotected(context)
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

    bpy.types.Scene.scene_to_return_to = StringProperty(
        name="Scene to return to",
        description="Scene to return to",
        default="")

    bpy.types.Scene.printTimes = BoolProperty(default=False)
    bpy.props.origScene = StringProperty(default="")
    bpy.props.commitEdits = False

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
    km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')
    kmi = km.keymap_items.new("scene.rebrickr_brickify", 'L', 'PRESS', alt=True, shift=True)
    kmi = km.keymap_items.new("scene.rebrickr_delete", 'D', 'PRESS', alt=True, shift=True)#, ctrl=True)
    kmi = km.keymap_items.new("scene.rebrickr_edit_source", 'TAB', 'PRESS', alt=True)#, ctrl=True)
    addon_keymaps.append(km)

    # other things (UI List)
    bpy.types.Scene.cmlist = CollectionProperty(type=Rebrickr_CreatedModels)
    bpy.types.Scene.cmlist_index = IntProperty(default=-1)

def unregister():
    Scn = bpy.types.Scene

    del Scn.cmlist_index
    del Scn.cmlist

    wm = bpy.context.window_manager
    for km in addon_keymaps:
        wm.keyconfigs.addon.keymaps.remove(km)

    # clear the list
    addon_keymaps.clear()

    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
