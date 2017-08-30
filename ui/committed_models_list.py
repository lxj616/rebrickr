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
props = bpy.props

import bpy
from bpy.props import IntProperty, CollectionProperty #, StringProperty
from bpy.types import Panel, UIList

def matchProperties(cmNew, cmOld):
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
    cmNew.randomRot = cmOld.randomRot
    cmNew.randomLoc = cmOld.randomLoc
    cmNew.splitModel = cmOld.splitModel
    cmNew.maxBrickScale1 = cmOld.maxBrickScale1
    cmNew.maxBrickScale2 = cmOld.maxBrickScale2
    cmNew.originSet = cmOld.originSet
    cmNew.calculationAxes = cmOld.calculationAxes
    cmNew.bevelWidth = cmOld.bevelWidth
    cmNew.bevelSegments = cmOld.bevelSegments
    cmNew.bevelProfile = cmOld.bevelProfile
    cmNew.useAnimation = cmOld.useAnimation
    cmNew.startFrame = cmOld.startFrame
    cmNew.stopFrame = cmOld.stopFrame

# ui list item actions
class LEGOizer_Uilist_actions(bpy.types.Operator):
    bl_idname = "cmlist.list_action"
    bl_label = "List Action"

    action = bpy.props.EnumProperty(
        items=(
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
            ('REMOVE', "Remove", ""),
            ('ADD', "Add", ""),
            ('NONE', "None", ""),
        )
    )

    # @classmethod
    # def poll(cls, context):
    #     """ ensures operator can execute (if not, returns false) """
    #     scn = context.scene
    #     for cm in scn.cmlist:
    #         if cm.animated:
    #             return False
    #     return True

    def isObjVisible(self, cm):
        scn = bpy.context.scene
        n = cm.source_name
        objVisible = False
        if cm.modelCreated or cm.animated:
            gn = "LEGOizer_%(n)s_bricks" % locals()
            if groupExists(gn) and len(bpy.data.groups[gn].objects) > 0:
                obj = bpy.data.groups[gn].objects[0]
            else:
                obj = None
        else:
            obj = bpy.data.objects.get(cm.source_name)
        if obj is not None:
            objVisible = False
            for i in range(20):
                if obj.layers[i] and scn.layers[i]:
                    objVisible = True
        return objVisible, obj

    def modal(self, context, event):
        scn = bpy.context.scene
        # if scn.layers changes and active object is no longer visible, set scn.cmlist_index to -1
        if self.last_layers != list(scn.layers):
            self.last_layers = list(scn.layers)
            curObjVisible = False
            if scn.cmlist_index != -1:
                cm0 = scn.cmlist[scn.cmlist_index]
                curObjVisible,_ = self.isObjVisible(cm0)
            if not curObjVisible or scn.cmlist_index == -1:
                setIndex = False
                for i,cm in enumerate(scn.cmlist):
                    if i != scn.cmlist_index:
                        nextObjVisible,obj = self.isObjVisible(cm)
                        if nextObjVisible and bpy.context.active_object == obj:
                            scn.cmlist_index = i
                            setIndex = True
                            break
                if not setIndex:
                    scn.cmlist_index = -1
                redraw_areas("VIEW_3D")
        # select and make source or LEGO model active if scn.cmlist_index changes
        elif self.last_cmlist_index != scn.cmlist_index and scn.cmlist_index != -1:
            self.last_cmlist_index = scn.cmlist_index
            cm = scn.cmlist[scn.cmlist_index]
            obj = bpy.data.objects.get(cm.source_name)
            if obj is not None:
                if cm.modelCreated:
                    n = cm.source_name
                    gn = "LEGOizer_%(n)s_bricks" % locals()
                    if groupExists(gn) and len(bpy.data.groups[gn].objects) > 0:
                        select(list(bpy.data.groups[gn].objects), active=bpy.data.groups[gn].objects[0])
                elif cm.animated:
                    n = cm.source_name
                    cf = scn.frame_current
                    if cf > cm.stopFrame:
                        cf = cm.stopFrame
                    elif cf < cm.startFrame:
                        cf = cm.startFrame
                    gn = "LEGOizer_%(n)s_bricks_frame_%(cf)s" % locals()
                    if len(bpy.data.groups[gn].objects) > 0:
                        select(list(bpy.data.groups[gn].objects), active=bpy.data.groups[gn].objects[0])
                else:
                    select(obj, active=obj)
                self.last_active_object_name = obj.name
            else:
                for i in range(len(scn.cmlist)):
                    cm = scn.cmlist[i]
                    if cm.source_name == self.active_object_name:
                        select(None)
                        break
        # open LEGO model settings for active object if active object changes
        elif scn.objects.active and self.last_active_object_name != scn.objects.active.name and ( scn.cmlist_index == -1 or scn.cmlist[scn.cmlist_index].source_name != "") and scn.objects.active.type == "MESH":
            self.last_active_object_name = scn.objects.active.name
            if scn.objects.active.name.startswith("LEGOizer_"):
                if "_bricks" in scn.objects.active.name:
                    frameLoc = scn.objects.active.name.rfind("_bricks")
                elif "_brick_" in scn.objects.active.name:
                    frameLoc = scn.objects.active.name.rfind("_brick_")
                else:
                    frameLoc = None
                if frameLoc is not None:
                    self.active_object_name = scn.objects.active.name[9:frameLoc]
            else:
                self.active_object_name = scn.objects.active.name
            for i in range(len(scn.cmlist)):
                cm = scn.cmlist[i]
                if cm.source_name == self.active_object_name:
                    scn.cmlist_index = i
                    redraw_areas("VIEW_3D")
                    self.last_cmlist_index = scn.cmlist_index
                    return {"PASS_THROUGH"}
            scn.cmlist_index = -1
            redraw_areas("VIEW_3D")

        if scn.cmlist_index != -1:
            cm = scn.cmlist[scn.cmlist_index]
            obj = bpy.data.objects.get(cm.source_name)
            if obj is not None and (len(obj.data.vertices) != cm.objVerts or len(obj.data.polygons) != cm.objPolys or len(obj.data.edges) != cm.objEdges):
                cm.objVerts = len(obj.data.vertices)
                cm.objPolys = len(obj.data.polygons)
                cm.objEdges = len(obj.data.edges)
                cm.isWaterTight = cm.objVerts + cm.objPolys - cm.objEdges == 2
                redraw_areas("VIEW_3D")
        return {"PASS_THROUGH"}

    def execute(self, context):

        scn = context.scene
        idx = scn.cmlist_index
        self.active_object_name = -1
        self.last_active_object_name = -1
        self.last_cmlist_index = scn.cmlist_index
        self.last_layers = list(scn.layers)

        try:
            item = scn.cmlist[idx]
        except IndexError:
            pass

        if self.action == 'REMOVE' and len(scn.cmlist) > 0 and scn.cmlist_index >= 0:
            cm = scn.cmlist[scn.cmlist_index]
            sn = cm.source_name
            n = cm.name
            if not cm.modelCreated and not cm.animated:
                scn.cmlist_index -= 1
                scn.cmlist.remove(idx)
                if scn.cmlist_index == -1 and len(scn.cmlist) > 0:
                    scn.cmlist_index = 0
            else:
                self.report({"WARNING"}, 'Please delete the LEGOized model before attempting to remove this item.' % locals())

        if self.action == 'ADD':
            active_object = scn.objects.active
            # if active object isn't on visible layer, don't set it as default source for new model
            if active_object != None:
                objVisible = False
                for i in range(20):
                    if active_object.layers[i] and scn.layers[i]:
                        objVisible = True
                if not objVisible:
                    active_object = None
            # if active object already has a model or isn't on visible layer, don't set it as default source for new model
            # NOTE: active object may have been removed, so we need to re-check if none
            if active_object != None:
                for cm in scn.cmlist:
                    if cm.source_name == active_object.name:
                        active_object = None
                        break
            item = scn.cmlist.add()
            last_index = scn.cmlist_index
            scn.cmlist_index = len(scn.cmlist)-1
            if active_object and active_object.type == "MESH" and not active_object.name.startswith("LEGOizer_"):
                item.source_name = active_object.name
                item.name = active_object.name
            else:
                item.source_name = ""
                item.name = "<New Model>"
            item.id = len(scn.cmlist)
            item.idx = len(scn.cmlist)-1
            if last_index == -1:
                item.startFrame = scn.frame_start
                item.stopFrame = scn.frame_end
            else:
                matchProperties(scn.cmlist[scn.cmlist_index], scn.cmlist[last_index])

        elif self.action == 'DOWN' and idx < len(scn.cmlist) - 1:
            scn.cmlist.move(scn.cmlist_index, scn.cmlist_index+1)
            scn.cmlist_index += 1
            item.idx = scn.cmlist_index

        elif self.action == 'UP' and idx >= 1:
            scn.cmlist.move(scn.cmlist_index, scn.cmlist_index-1)
            scn.cmlist_index -= 1
            item.idx = scn.cmlist_index

        if listModalRunning():
            return{"FINISHED"}
        else:
            # run modal
            wm = bpy.context.window_manager
            bpy.context.window_manager["list_modal_running"] = True
            wm.modal_handler_add(self)
            return {"RUNNING_MODAL"}

# -------------------------------------------------------------------
# draw
# -------------------------------------------------------------------

# custom list
class LEGOizer_UL_items(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # Make sure your code supports all 3 layout types
        if self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
        split = layout.split(0.9)
        split.prop(item, "name", text="", emboss=False, translate=False, icon='MOD_REMESH')

    def invoke(self, context, event):
        pass


# print button
class LEGOizer_Uilist_printAllItems(bpy.types.Operator):
    bl_idname = "cmlist.print_list"
    bl_label = "Print List"
    bl_description = "Print all items to the console"

    def execute(self, context):
        scn = context.scene
        for i in scn.cmlist:
            print (i.source_name, i.id)
        return{'FINISHED'}

# set source to active button
class LEGOizer_Uilist_setSourceToActive(bpy.types.Operator):
    bl_idname = "cmlist.set_to_active"
    bl_label = "Set to Active"
    bl_description = "Set source to active object in scene"

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns false) """
        scn = context.scene
        if scn.cmlist_index == -1:
            return False
        active_obj = context.scene.objects.active
        if active_obj == None:
            return False
        for i in range(20):
            if scn.layers[i] and active_obj.layers[i]:
                return True
        # cm = scn.cmlist[scn.cmlist_index]
        # n = cm.source_name
        # LEGOizer_source = "LEGOizer_%(n)s" % locals()
        # if groupExists(LEGOizer_source) and len(bpy.data.groups[LEGOizer_source].objects) == 1:
        #     return True
        # try:
        #     if bpy.data.objects[cm.source_name].type == 'MESH':
        #         return True
        # except:
        #     return False
        return False

    def execute(self, context):
        scn = context.scene
        cm = scn.cmlist[scn.cmlist_index]
        active_object = context.scene.objects.active
        cm.source_name = active_object.name

        return{'FINISHED'}

# select button
class LEGOizer_Uilist_selectSource(bpy.types.Operator):
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
class LEGOizer_Uilist_selectAllBricks(bpy.types.Operator):
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
            select(active=objs[0])
            if len(objs) > 0:
                select(objs)

        return{'FINISHED'}

# clear button
class LEGOizer_Uilist_clearAllItems(bpy.types.Operator):
    bl_idname = "cmlist.clear_list"
    bl_label = "Clear List"
    bl_description = "Clear all items in the list"

    def execute(self, context):
        scn = context.scene
        lst = scn.createdModelsCollection
        current_index = scn.cmlist_index

        if len(lst) > 0:
             # reverse range to remove last item first
            for i in range(len(lst)-1,-1,-1):
                scn.createdModelsCollection.remove(i)
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
        if cm.lastBevelWidth != cm.bevelWidth or cm.lastBevelSegments != cm.bevelSegments or cm.lastBevelProfile != cm.bevelProfile:
            bricks = list(bpy.data.groups["LEGOizer_%(n)s_bricks" % locals()].objects)
            legoizerBevel.setBevelMods(bricks)
            cm.lastBevelWidth = cm.bevelWidth
            cm.lastBevelSegments = cm.bevelSegments
            cm.lastBevelProfile = cm.bevelProfile
    except:
        pass

def dirtyAnim(self, context):
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    cm.animIsDirty = True

def dirtyMaterial(self, context):
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    cm.materialIsDirty = True

def dirtyModel(self, context):
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    cm.modelIsDirty = True

def dirtyBuild(self, context):
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    cm.buildIsDirty = True

def dirtySource(self, context):
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    cm.sourceIsDirty = True

def dirtyBricks(self, context):
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    cm.bricksAreDirty = True

# Create custom property group
class LEGOizer_CreatedModels(bpy.types.PropertyGroup):
    name = StringProperty(update=uniquifyName)
    id = IntProperty()
    idx = IntProperty()

    source_name = StringProperty(
        name="Source Object Name",
        description="Name of the source object to legoize (defaults to active object)",
        default="",
        update=setNameIfEmpty)

    shellThickness = IntProperty(
        name="Shell Thickness",
        description="Thickness of the LEGO shell",
        update=dirtyBuild,
        min=1, max=100,
        default=1)

    studDetail = EnumProperty(
        name="Stud Detailing",
        description="Choose where to draw the studs",
        items=[("On All Bricks", "On All Bricks", "Include LEGO Logo only on bricks with studs exposed"),
              ("On Exposed Bricks", "On Exposed Bricks", "Include LEGO Logo only on bricks with studs exposed"),
              ("None", "None", "Don't include LEGO Logo on bricks")],
        update=dirtyBricks,
        default="On Exposed Bricks")

    logoDetail = EnumProperty(
        name="Logo Detailing",
        description="Choose where to draw the logo",
        items=[("On All Studs", "On All Studs", "Include LEGO Logo on all studs"),
              ("On Exposed Studs", "On Exposed Studs", "Include LEGO Logo only on exposed studs"),
              ("None", "None", "Don't include LEGO Logo on bricks")],
        update=dirtyBricks,
        default="None")

    logoResolution = FloatProperty(
        name="Logo Resolution",
        description="Resolution of the LEGO Logo",
        update=dirtyBricks,
        min=0.1, max=1,
        step=1,
        precision=1,
        default=0.2)

    hiddenUndersideDetail = EnumProperty(
        name="Hidden Underside Detailing",
        description="Choose the level of detail to include for the underside of hidden bricks",
        items=[("Full Detail", "Full Detail", "Draw true-to-life details on brick underside"),
              ("High Detail", "High Detail", "Draw intricate details on brick underside"),
              ("Medium Detail", "Medium Detail", "Draw most details on brick underside"),
              ("Low Detail", "Low Detail", "Draw minimal details on brick underside"),
              ("Flat", "Flat", "draw single face on brick underside")],
        update=dirtyBricks,
        default="Flat")
    exposedUndersideDetail = EnumProperty(
        name="Eposed Underside Detailing",
        description="Choose the level of detail to include for the underside of exposed bricks",
        items=[("Full Detail", "Full Detail", "Draw true-to-life details on brick underside"),
              ("High Detail", "High Detail", "Draw intricate details on brick underside"),
              ("Medium Detail", "Medium Detail", "Draw most details on brick underside"),
              ("Low Detail", "Low Detail", "Draw minimal details on brick underside"),
              ("Flat", "Flat", "draw single face on brick underside")],
        update=dirtyBricks,
        default="Flat")

    studVerts = IntProperty(
        name="Stud Verts",
        description="Number of vertices on LEGO stud",
        update=dirtyBricks,
        min=4, max=64,
        default=16)

    modelHeight = FloatProperty(
        name="Model Height",
        description="Height of the source object to LEGOize",
        default=-1)
    brickHeight = FloatProperty(
        name="Brick Height",
        description="Height of the bricks in the final LEGO model",
        update=dirtyModel,
        precision=3,
        min=0.001, max=10,
        default=.1)
    gap = FloatProperty(
        name="Gap Between Bricks",
        description="Height of the bricks in the final LEGO model",
        update=dirtyModel,
        step=1,
        precision=3,
        min=0, max=0.1,
        default=.01)

    mergeSeed = IntProperty(
        name="Random Seed",
        description="Random seed for brick merging calculations",
        update=dirtyBuild,
        min=-1, max=5000,
        default=1000)

    randomLoc = FloatProperty(
        name="Random Location",
        description="Random location applied to each brick individually",
        update=dirtyBuild,
        precision=3,
        min=0, max=1,
        default=0.005)
    randomRot = FloatProperty(
        name="Random Rotation",
        description="Random rotation applied to each brick individually",
        update=dirtyBuild,
        precision=3,
        min=0, max=1,
        default=0.025)

    brickType = EnumProperty(
        name="Brick Type",
        description="Choose what type of bricks to use to build the model",
        items=[("Plates", "Plates", "Use plates to build the model"),
              ("Bricks", "Bricks", "Use bricks to build the model"),
              #("Bricks and Plates", "Bricks and Plates", "Use bricks and plates to build the model")],
              ("Custom", "Custom", "Use custom object to build the model")],
        update=dirtyModel,
        default="Bricks")

    originSet = BoolProperty(
        name="Center brick origins",
        description="Set all brick origins to center of bricks (slower)",
        update=dirtyBricks,
        default=False)

    distOffsetX = FloatProperty(
        name="X",
        description="Distance Offset X",
        update=dirtyModel,
        precision=3,
        min=0.001, max=2,
        default=1)
    distOffsetY = FloatProperty(
        name="Y",
        description="Distance Offset Y",
        update=dirtyModel,
        precision=3,
        min=0.001, max=2,
        default=1)
    distOffsetZ = FloatProperty(
        name="Z",
        description="Distance Offset Z",
        update=dirtyModel,
        precision=3,
        min=0.001, max=2,
        default=1)

    customObjectName = StringProperty(
        name="Source Object Name",
        description="Name of the source object to legoize (defaults to active object)",
        update=dirtyModel,
        default="")

    maxBrickScale1 = IntProperty(
        name="Max 1 by x",
        description="Maximum scale of the 1 by X LEGO brick",
        update=dirtyBuild,
        min=1, max=10,
        default=10)
    maxBrickScale2 = IntProperty(
        name="Max 2 by x",
        description="Maximum scale of the 2 by X LEGO brick",
        update=dirtyBuild,
        min=1, max=10,
        default=10)

    splitModel = BoolProperty(
        name="Split Model",
        description="Split model into separate bricks (slower)",
        update=dirtyModel,
        default=False)

    internalSupports = EnumProperty(
        name="Internal Supports",
        description="Choose what type of bricks to use to build the model",
        items=[("None", "None", "No internal supports"),
              ("Lattice", "Lattice", "Use latice inside model"),
              ("Columns", "Columns", "Use columns inside model")],
        update=dirtyBuild,
        default="None")
    latticeStep = IntProperty(
        name="Lattice Step",
        update=dirtyBuild,
        min=2, max=25,
        default=2)
    alternateXY = BoolProperty(
        name="Alternate X and Y",
        update=dirtyBuild,
        default=False)
    colThickness = IntProperty(
        name="Column Thickness",
        update=dirtyBuild,
        min=1, max=25,
        default=2)
    colStep = IntProperty(
        name="Column Step",
        update=dirtyBuild,
        min=1, max=25,
        default=2)

    materialType = EnumProperty(
        name="Material Type",
        description="Choose what ",
        items=[("None", "None", "No material applied to LEGO bricks"),
              ("Custom", "Custom", "Choose a custom material to apply to all generated bricks"),
              ("Use Source Materials", "Use Source Materials", "Apply material based on closest intersecting face")],
        update=dirtyMaterial,
        default="Use Source Materials")
    materialName = StringProperty(
        name="Material Name",
        description="Name of the material to apply to all bricks",
        default="")
    internalMatName = StringProperty(
        name="Material Name",
        description="Name of the material to apply to bricks inside mat shell",
        update=dirtyMaterial,
        default="")
    matShellDepth = IntProperty(
        name="Material Shell Depth",
        description="How deep in layers the outer materials should be applied",
        default=2,
        min=1, max=100,
        update=dirtyModel)
    mergeInconsistentMats = BoolProperty(
        name="Merge Inconsistent Materials",
        description="Only merge bricks together to form bigger bricks if they share a material",
        default=False,
        update=dirtyBuild)

    useNormals = BoolProperty(
        name="Use Normals",
        description="Use normals to calculate insideness of bricks (WARNING: May produce inaccurate model if source mesh is not water-tight)",
        default=False,
        update=dirtyBuild)
    verifyExposure = BoolProperty(
        name="Verify Exposure",
        description="Run additional calculations to verify exposure of studs and underside detailing (WARNING: May compromise 'Shell Thickness' functionality if source mesh is not water-tight)",
        default=False,
        update=dirtyBuild)

    objVerts = IntProperty(default=0)
    objPolys = IntProperty(default=0)
    objEdges = IntProperty(default=0)
    isOneMesh = BoolProperty(default=False)
    isWaterTight = BoolProperty(default=False)
    maxDepthExceeded = BoolProperty(default=False)

    lastLogoDetail = StringProperty(default="None")
    lastLogoResolution = FloatProperty(default=0)
    lastSplitModel = BoolProperty(default=False)
    lastStartFrame = IntProperty(default=-1)
    lastStopFrame = IntProperty(default=-1)

    modelLoc = StringProperty(default="-1,-1,-1")
    modelRot = StringProperty(default="-1,-1,-1")
    modelScale = StringProperty(default="-1,-1,-1")
    applyToSourceObject = BoolProperty(
        name="Apply to source",
        description="Apply transformations to source object when LEGO Model is deleted",
        default=True)

    # Bevel Settings
    lastBevelWidth = FloatProperty()
    bevelWidth = FloatProperty(
        name="Bevel Width",
        default=0.001,
        min=0.000001, max=10,
        update=updateBevel)
    lastBevelSegments = IntProperty()
    bevelSegments = IntProperty(
        name="Bevel Resolution",
        default=1,
        min=1, max=10,
        update=updateBevel)
    lastBevelProfile = IntProperty()
    bevelProfile = FloatProperty(
        name="Bevel Profile",
        default=0.7,
        min=0, max=1,
        update=updateBevel)

    # ANIMATION SETTINGS
    startFrame = IntProperty(
        name="Start Frame",
        update=dirtyAnim,
        min=0, max=500000,
        default=1)
    stopFrame = IntProperty(
        name="Stop Frame",
        update=dirtyAnim,
        min=0, max=500000,
        default=10)
    useAnimation = BoolProperty(
        name="Use Animation",
        description="LEGOize object animation from start to stop frame (WARNING: Calculation takes time, and may result in large blend file size)",
        default=False)

    # ADVANCED SETTINGS
    brickShell = EnumProperty(
        name="Brick Shell",
        description="Choose whether the brick shell with be drawn inside or outside source mesh",
        items=[("Inside Mesh", "Inside Mesh (recommended)", "Draw brick shell inside source mesh (Recommended)"),
              ("Outside Mesh", "Outside Mesh", "Draw brick shell outside source mesh"),
              ("Inside and Outside", "Inside and Outside", "Draw brick shell inside and outside source mesh (two layers)")],
        update=dirtyModel,
        default="Inside Mesh")
    calculationAxes = EnumProperty(
        name="Expanded Axes",
        description="The brick shell will be drawn on the outside in these directions",
        items=[("XYZ", "XYZ", "PLACEHOLDER"),
              ("XY", "XY", "PLACEHOLDER"),
              ("YZ", "YZ", "PLACEHOLDER"),
              ("XZ", "XZ", "PLACEHOLDER"),
              ("X", "X", "PLACEHOLDER"),
              ("Y", "Y", "PLACEHOLDER"),
              ("Z", "Z", "PLACEHOLDER")],
        update=dirtyModel,
        default="XY")

    modelCreated = BoolProperty(default=False)
    animated = BoolProperty(default=False)
    materialApplied = BoolProperty(default=False)
    armature = BoolProperty(default=False)

    animIsDirty = BoolProperty(default=True)
    materialIsDirty = BoolProperty(default=True)
    modelIsDirty = BoolProperty(default=True)
    buildIsDirty = BoolProperty(default=True)
    sourceIsDirty = BoolProperty(default=True)
    bricksAreDirty = BoolProperty(default=True)

# -------------------------------------------------------------------
# register
# -------------------------------------------------------------------

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.createdModelsCollection = CollectionProperty(type=LEGOizer_CreatedModels)
    bpy.types.Scene.cmlist_index = IntProperty()

def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.createdModelsCollection
    del bpy.types.Scene.cmlist_index

if __name__ == "__main__":
    register()
