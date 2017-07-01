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

import bpy
from bpy.props import IntProperty, CollectionProperty #, StringProperty
from bpy.types import Panel, UIList


# return name of selected object
def get_activeSceneObject():
    return bpy.context.scene.objects.active.name


# ui list item actions
class Uilist_actions(bpy.types.Operator):
    bl_idname = "cmlist.list_action"
    bl_label = "List Action"

    action = bpy.props.EnumProperty(
        items=(
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
            ('REMOVE', "Remove", ""),
            ('ADD', "Add", ""),
        )
    )

    def invoke(self, context, event):

        scn = context.scene
        idx = scn.cmlist_index

        try:
            item = scn.cmlist[idx]
        except IndexError:
            pass

        else:
            if self.action == 'DOWN' and idx < len(scn.cmlist) - 1:
                item_next = scn.cmlist[idx+1].name
                scn.cmlist_index += 1
                info = 'Item %d selected' % (scn.cmlist_index + 1)
                self.report({'INFO'}, info)

            elif self.action == 'UP' and idx >= 1:
                item_prev = scn.cmlist[idx-1].name
                scn.cmlist_index -= 1
                info = 'Item %d selected' % (scn.cmlist_index + 1)
                self.report({'INFO'}, info)

            elif self.action == 'REMOVE':
                info = 'Item %s removed from list' % (scn.cmlist[scn.cmlist_index].name)
                scn.cmlist_index -= 1
                self.report({'INFO'}, info)
                scn.cmlist.remove(idx)

        if self.action == 'ADD':
            name = get_activeSceneObject()
            success = addItemToCMList(name)
            if success:
                info = '%s added to list' % (name)
                self.report({'INFO'}, info)
            else:
                info = '%s already in the list' % (name)
                self.report({'INFO'}, info)

        return {"FINISHED"}

# -------------------------------------------------------------------
# draw
# -------------------------------------------------------------------

# custom list
class UL_items(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # Make sure your code supports all 3 layout types
        if self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
        split = layout.split(0.9)
        split.prop(item, "name", text="", emboss=False, translate=False, icon='OBJECT_DATAMODE')

    def invoke(self, context, event):
        pass


# print button
class Uilist_printAllItems(bpy.types.Operator):
    bl_idname = "cmlist.print_list"
    bl_label = "Print List"
    bl_description = "Print all items to the console"

    def execute(self, context):
        scn = context.scene
        for i in scn.custom:
            print (i.name, i.id)
        return{'FINISHED'}

# select button
class Uilist_selectAllItems(bpy.types.Operator):
    bl_idname = "cmlist.select_item"
    bl_label = "Select List Item"
    bl_description = "Select Item in scene"

    def execute(self, context):
        scn = context.scene
        bpy.ops.object.select_all(action='DESELECT')
        obj = bpy.data.objects[scn.custom[scn.cmlist_index].name]
        obj.select = True

        return{'FINISHED'}

# clear button
class Uilist_clearAllItems(bpy.types.Operator):
    bl_idname = "cmlist.clear_list"
    bl_label = "Clear List"
    bl_description = "Clear all items in the list"

    def execute(self, context):
        scn = context.scene
        lst = scn.custom
        current_index = scn.cmlist_index

        if len(lst) > 0:
             # reverse range to remove last item first
            for i in range(len(lst)-1,-1,-1):
                scn.custom.remove(i)
            self.report({'INFO'}, "All items removed")

        else:
            self.report({'INFO'}, "Nothing to remove")

        return{'FINISHED'}

# Create custom property group
class CustomProp(bpy.types.PropertyGroup):
    '''name = StringProperty() '''
    id = IntProperty()
    source_object = StringProperty(
        name="Source Object",
        description="Source object to legoize (defaults to active object)",
        default="")

    changesToCommit = BoolProperty(
        default=False)

# -------------------------------------------------------------------
# register
# -------------------------------------------------------------------

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.custom = CollectionProperty(type=CustomProp)
    bpy.types.Scene.cmlist_index = IntProperty()

def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.custom
    del bpy.types.Scene.cmlist_index

if __name__ == "__main__":
    register()
