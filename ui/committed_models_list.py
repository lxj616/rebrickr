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
from ..buttons.bevel import *
from ..lib import common_utilities
from ..lib.common_utilities import bversion
props = bpy.props

import bpy
from bpy.props import IntProperty, CollectionProperty #, StringProperty
from bpy.types import Panel, UIList

def matchProperties(cmNew, cmOld):
    cmNew.preHollow = cmOld.preHollow
    cmNew.shellThickness = cmOld.shellThickness
    cmNew.studDetail = cmOld.studDetail
    cmNew.logoDetail = cmOld.logoDetail
    cmNew.logoResolution = cmOld.logoResolution
    cmNew.hiddenUndersideDetail = cmOld.hiddenUndersideDetail
    cmNew.exposedUndersideDetail = cmOld.exposedUndersideDetail
    cmNew.studVerts = cmOld.studVerts
    cmNew.brickHeight = cmOld.brickHeight
    cmNew.gap = cmOld.gap
    cmNew.mergeSeed = cmOld.mergeSeed
    cmNew.maxBrickScale = cmOld.maxBrickScale
    cmNew.smoothCylinders = cmOld.smoothCylinders
    cmNew.calculationAxes = cmOld.calculationAxes
    cmNew.bevelWidth = cmOld.bevelWidth
    cmNew.bevelResolution = cmOld.bevelResolution

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
            # if active object already has a model, don't set it as default source for new model
            if active_object != None:
                for cm in scn.cmlist:
                    if cm.source_name == active_object.name:
                        active_object = None
                        break
            item = scn.cmlist.add()
            last_index = scn.cmlist_index
            scn.cmlist_index = len(scn.cmlist)-1
            item.name = "<New Model>"
            if active_object:
                item.source_name = active_object.name
            else:
                item.source_name = ""
            item.id = len(scn.cmlist)
            info = '%s added to list' % (item.name)
            matchProperties(scn.cmlist[scn.cmlist_index], scn.cmlist[last_index])
            self.report({'INFO'}, info)

        elif self.action == 'DOWN' and idx < len(scn.cmlist) - 1:
            item_next = scn.cmlist[idx+1].source_name
            scn.cmlist_index += 1
            info = 'Item %d selected' % (scn.cmlist_index + 1)
            self.report({'INFO'}, info)

        elif self.action == 'UP' and idx >= 1:
            item_prev = scn.cmlist[idx-1].source_name
            scn.cmlist_index -= 1
            info = 'Item %d selected' % (scn.cmlist_index + 1)
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
class Uilist_selectSource(bpy.types.Operator):
    bl_idname = "cmlist.select_source"
    bl_label = "Select Source Object"
    bl_description = "Select only source object for model"

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns false) """
        scn = context.scene
        if scn.cmlist_index == -1:
            return False
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        LEGOizer_source = "LEGOizer_%(n)s" % locals()
        if groupExists(LEGOizer_source) and len(bpy.data.groups[LEGOizer_source].objects) == 1:
            return True
        try:
            cm = scn.cmlist[scn.cmlist_index]
            if bpy.data.objects[cm.source_name].type == 'MESH':
                return True
        except:
            return False
        return False

    def execute(self, context):
        scn = context.scene
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        obj = bpy.data.objects[n]
        select(obj, active=obj)

        return{'FINISHED'}

# select button
class Uilist_selectAllBricks(bpy.types.Operator):
    bl_idname = "cmlist.select_bricks"
    bl_label = "Select Bricks"
    bl_description = "Select only bricks in model"

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
    cm0 = scn.cmlist[scn.cmlist_index]
    # verify model doesn't exist with that name
    if cm0.source_name != "":
        for i,cm1 in enumerate(scn.cmlist):
            if cm1 != cm0 and cm1.source_name == cm0.source_name:
                cm0.source_name = ""
                scn.cmlist_index = i

def updateBevel(self, context):
    # get bricks to bevel
    scn = context.scene
    try:
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        if cm.lastBevelWidth != cm.bevelWidth or cm.lastBevelResolution != cm.bevelResolution:
            bricks = list(bpy.data.groups["LEGOizer_%(n)s_bricks" % locals()].objects)
            legoizerBevel.setBevelMods(bricks)
            cm.lastBevelWidth = cm.bevelWidth
            cm.lastBevelResolution = cm.bevelResolution
    except:
        pass

# Create custom property group
class CreatedModels(bpy.types.PropertyGroup):
    name = StringProperty(update=uniquifyName)
    id = IntProperty()

    source_name = StringProperty(
        name="Source Object Name",
        description="Name of the source object to legoize (defaults to active object)",
        default="",
        update=setNameIfEmpty)

    preHollow = BoolProperty(
        name="Pre Hollow",
        description="Hollow out LEGO model with user defined shell thickness",
        default=True)

    shellThickness = IntProperty(
        name="Shell Thickness",
        description="Thickness of the LEGO shell",
        min=1, max=100,
        default=2)

    studDetail = EnumProperty(
        name="Stud Detailing",
        description="Choose where to draw the studs",
        items=[("On All Bricks", "On All Bricks", "Include LEGO Logo only on bricks with studs exposed"),
              ("On Exposed Bricks", "On Exposed Bricks", "Include LEGO Logo only on bricks with studs exposed"),
              ("None", "None", "Don't include LEGO Logo on bricks")],
        default="On Exposed Bricks")

    logoDetail = EnumProperty(
        name="Logo Detailing",
        description="Choose where to draw the logo",
        items=[("On All Studs", "On All Studs", "Include LEGO Logo on all studs"),
              ("On Exposed Studs", "On Exposed Studs", "Include LEGO Logo only on exposed studs"),
              ("None", "None", "Don't include LEGO Logo on bricks")],
        default="None")

    logoResolution = FloatProperty(
        name="Logo Resolution",
        description="Resolution of the LEGO Logo",
        min=0.1, max=1,
        step=1,
        precision=2,
        default=0.5)

    hiddenUndersideDetail = EnumProperty(
        name="Hidden Underside Detailing",
        description="Choose the level of detail to include for the underside of hidden bricks",
        items=[("Full Detail", "Full Detail", "Draw true-to-life details on brick underside"),
              ("High Detail", "High Detail", "Draw intricate details on brick underside"),
              ("Medium Detail", "Medium Detail", "Draw most details on brick underside"),
              ("Low Detail", "Low Detail", "Draw minimal details on brick underside"),
              ("Flat", "Flat", "draw single face on brick underside")],
        default="Flat")
    exposedUndersideDetail = EnumProperty(
        name="Eposed Underside Detailing",
        description="Choose the level of detail to include for the underside of exposed bricks",
        items=[("Full Detail", "Full Detail", "Draw true-to-life details on brick underside"),
              ("High Detail", "High Detail", "Draw intricate details on brick underside"),
              ("Medium Detail", "Medium Detail", "Draw most details on brick underside"),
              ("Low Detail", "Low Detail", "Draw minimal details on brick underside"),
              ("Flat", "Flat", "draw single face on brick underside")],
        default="Flat")

    studVerts = IntProperty(
        name="Stud Verts",
        description="Number of vertices on LEGO stud",
        min=4, max=64,
        default=16)

    brickHeight = FloatProperty(
        name="Brick Height",
        description="Height of the bricks in the final LEGO model",
        min=.001, max=10,
        default=.1)
    gap = FloatProperty(
        name="Gap Between Bricks",
        description="Height of the bricks in the final LEGO model",
        step=1,
        precision=3,
        min=0, max=0.1,
        default=.01)

    mergeSeed = IntProperty(
        name="Random Seed",
        description="Random seed for brick merging calculations",
        min=-1, max=5000,
        default=1000)

    maxBrickScale = IntProperty(
        name="Max Brick Scale",
        description="Maximum scale of the generated LEGO bricks (equivalent to num studs on top)",
        min=1, max=20,
        default=16)

    smoothCylinders = BoolProperty(
        name="Smooth Cylinders",
        description="Smooths cylinders with edge split and smooth shading (disable for bevel resolution control)",
        default=True)

    lastBrickHeight = FloatProperty(default=0)
    lastGap = FloatProperty(default=0)
    lastPreHollow = BoolProperty(default=False)
    lastShellThickness = IntProperty(default=0)
    lastCalculationAxes = StringProperty(default="")
    lastLogoDetail = StringProperty(default="None")
    lastLogoResolution = FloatProperty(default=0)
    lastStudDetail = StringProperty(default="None")
    lastStudVerts = FloatProperty(default=0)
    lastMergeSeed = IntProperty(default=1000)
    lastMaxBrickScale = IntProperty(default=10)
    lastExposedUndersideDetail = StringProperty(default="None")
    lastHiddenUndersideDetail = StringProperty(default="None")
    lastSmoothCylinders = BoolProperty(default=True)

    # Bevel Settings
    lastBevelWidth = FloatProperty()
    bevelWidth = FloatProperty(
        name="Bevel Width",
        default=0.001,
        min=0.000001, max=10,
        update=updateBevel)
    lastBevelResolution = IntProperty()
    bevelResolution = IntProperty(
        name="Bevel Resolution",
        default=1,
        min=1, max=10,
        update=updateBevel)

    # ADVANCED SETTINGS
    calculationAxes = EnumProperty(
        name="Calculation Axes",
        description="Choose which directions rays will be cast from",
        items=[("XYZ", "XYZ", "PLACEHOLDER"),
              ("XY", "XY", "PLACEHOLDER"),
              ("YZ", "YZ", "PLACEHOLDER"),
              ("XZ", "XZ", "PLACEHOLDER"),
              ("X", "X", "PLACEHOLDER"),
              ("Y", "Y", "PLACEHOLDER"),
              ("Z", "Z", "PLACEHOLDER")],
        default="XY")

# -------------------------------------------------------------------
# register
# -------------------------------------------------------------------

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.custom = CollectionProperty(type=CreatedModels)
    bpy.types.Scene.cmlist_index = IntProperty()

def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.custom
    del bpy.types.Scene.cmlist_index

if __name__ == "__main__":
    register()
