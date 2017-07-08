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

        if self.action == 'REMOVE':
            cm = scn.cmlist[scn.cmlist_index]
            sn = cm.source_name
            n = cm.name
            if not groupExists("LEGOizer_%(sn)s_bricks" % locals()):
                info = 'Item %(n)s removed from list' % locals()
                scn.cmlist_index -= 1
                self.report({'INFO'}, info)
                scn.cmlist.remove(idx)
            else:
                self.report({"WARNING"}, 'Please delete the LEGOized model before attempting to remove this item.' % locals())

        if self.action == 'ADD':
            active_object = scn.objects.active
            if active_object:
                name = active_object.name
            else:
                name = ""
            addItemToCMList(name)
            info = '%s added to list' % (name)
            self.report({'INFO'}, info)

        # elif self.action == 'DOWN' and idx < len(scn.cmlist) - 1:
        #     item_next = scn.cmlist[idx+1].source_name
        #     scn.cmlist_index += 1
        #     info = 'Item %d selected' % (scn.cmlist_index + 1)
        #     self.report({'INFO'}, info)
        #
        # elif self.action == 'UP' and idx >= 1:
        #     item_prev = scn.cmlist[idx-1].source_name
        #     scn.cmlist_index -= 1
        #     info = 'Item %d selected' % (scn.cmlist_index + 1)
        #     self.report({'INFO'}, info)

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
        split.prop(item, "name", text="", emboss=False, translate=False, icon='MOD_BUILD')

    def invoke(self, context, event):
        pass


# print button
class Uilist_printAllItems(bpy.types.Operator):
    bl_idname = "cmlist.print_list"
    bl_label = "Print List"
    bl_description = "Print all items to the console"

    def execute(self, context):
        scn = context.scene
        for i in scn.cmlist:
            print (i.source_name, i.id)
        return{'FINISHED'}

# select button
class Uilist_selectAllBricks(bpy.types.Operator):
    bl_idname = "cmlist.select_bricks"
    bl_label = "Select Bricks"
    bl_description = "Select all bricks in model"

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns false) """
        scn = context.scene
        if scn.cmlist_index == -1:
            return False
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        LEGOizer_bricks = "LEGOizer_%(n)s_bricks" % locals()
        if groupExists(LEGOizer_bricks) and len(bpy.data.groups[LEGOizer_bricks].objects) != 0:
            return True
        return False

    def execute(self, context):
        scn = context.scene
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        LEGOizer_bricks = "LEGOizer_%(n)s_bricks" % locals()
        if groupExists(LEGOizer_bricks):
            bpy.ops.object.select_all(action='DESELECT')
            objs = list(bpy.data.groups[LEGOizer_bricks].objects)
            if len(objs) > 0:
                select(objs)

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

# def setName(self, context):
#     scn = bpy.context.scene
#     cm = scn.cmlist[scn.cmlist_index]
#     cm.name = cm.source_name
#     return None

def uniquifyName(self, context):
    """ if LEGO model exists with name, add '.###' to the end """
    scn = context.scene
    cm = scn.cmlist[scn.cmlist_index]
    name = cm.name
    while scn.cmlist.keys().count(name) > 1:
        if name[-4] == ".":
            try:
                num = int(name[-3:])+1
            except:
                num = 1
            name = name[:-3] + "%03d" % (num)
        else:
            name = name + ".001"
    if cm.name != name:
        cm.name = name

def setNameIfEmpty(self, context):
    scn = context.scene
    cm = scn.cmlist[scn.cmlist_index]
    if cm.name == "":
        cm.name = cm.source_name


# Create custom property group
class CustomProp(bpy.types.PropertyGroup):
    name = StringProperty(update=uniquifyName)
    id = IntProperty()

    source_name = StringProperty(
        name="Source Object Name",
        description="Name of the source object to legoize (defaults to active object)",
        default="",
        update=setNameIfEmpty)

    changesToCommit = BoolProperty(
        default=False)

    preHollow = BoolProperty(
        name="Pre Hollow",
        description="Hollow out LEGO model with user defined shell thickness",
        default=True)

    logoDetail = EnumProperty(
        name="Logo Detailing",
        description="Choose whether to construct or deconstruct the LEGO bricks",
        items=[("On All Bricks", "On All Bricks", "Include LEGO Logo on all bricks"),
            #   ("On Exposed Bricks", "On Exposed Bricks", "Include LEGO Logo only on bricks with studs exposed"),
              ("None", "None", "Don't include LEGO Logo on bricks")],
        default="None")

    lastLogoDetail = StringProperty(
        default="None")

    logoResolution = FloatProperty(
        name="Logo Resolution",
        description="Resolution of the LEGO Logo",
        min=0.1, max=1,
        step=1,
        precision=2,
        default=0.5)

    lastLogoResolution = FloatProperty(
        default=0.5)

    undersideDetail = EnumProperty(
        name="Underside Detailing",
        description="Choose whether to construct or deconstruct the LEGO bricks",
        items=[("High Detail", "High Detail", "Draw intricate details on brick underside"),
              ("Low Detail", "Low Detail", "Draw minimal details on brick underside"),
              ("Flat", "Flat", "draw single face on brick underside")],
        default="Flat")

    studVerts = IntProperty(
        name="Stud Verts",
        description="Number of vertices on LEGO stud",
        min=3, max=64,
        default=16)

    shellThickness = IntProperty(
        name="Shell Thickness",
        description="Thickness of the LEGO shell",
        min=1, max=10,
        default=1)

    brickHeight = FloatProperty(
        name="Brick Height",
        description="Height of the bricks in the final LEGO model",
        min=.001, max=10,
        default=.1)
    gap = FloatProperty(
        name="Gap Between Bricks",
        description="Height of the bricks in the final LEGO model",
        min=.001, max=1,
        default=.01)

    lastBrickHeight = IntProperty(
        default=0)

    # ADVANCED SETTINGS
    calculationAxis = EnumProperty(
        name="Calculation Axis",
        description="PLACEHOLDER", # TODO: Fill in placeholders on this line and the next four
        items=[("Auto", "Auto", "PLACEHOLDER"),
              ("X Axis", "X Axis", "PLACEHOLDER"),
              ("Y Axis", "Y Axis", "PLACEHOLDER"),
              ("Z Axis", "Z Axis", "PLACEHOLDER")],
        default="Auto")

    logoMesh = None

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
