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
from operator import itemgetter

# Blender imports
import bpy
from bpy.props import *
from bpy.types import Panel, UIList
props = bpy.props

# Bricker imports
from ..functions import *
from ..buttons.bevel import *


def matchProperties(cmTo, cmFrom, bh=False):
    # list properties to match
    cm_attrs = ["shellThickness",
                "studDetail",
                "logoDetail",
                "logoResolution",
                "logoObjectName",
                "logoScale",
                "logoInset",
                "hiddenUndersideDetail",
                "exposedUndersideDetail",
                "circleVerts",
                "gap",
                "mergeSeed",
                "randomLoc",
                "randomRot",
                "brickType",
                "alignBricks",
                "offsetBrickLayers",
                "originSet",
                "distOffsetX",
                "distOffsetY",
                "distOffsetZ",
                "customObjectName",
                "maxWidth",
                "maxDepth",
                "splitModel",
                "internalSupports",
                "matShellDepth",
                "latticeStep",
                "alternateXY",
                "colThickness",
                "colStep",
                "materialType",
                "materialName",
                "internalMatName",
                "matShellDepth",
                "mergeInconsistentMats",
                "randomMatSeed",
                "useUVMap",
                "useNormals",
                "verifyExposure",
                "insidenessRayCastDir",
                "castDoubleCheckRays",
                "startFrame",
                "stopFrame",
                "useAnimation",
                "autoUpdateExposed",
                "brickShell",
                "calculationAxes",
                "useLocalOrient"]
    # more properties to match if condition is true
    if bh:
        cm_attrs.append("brickHeight")
    if cmFrom.bevelAdded and cmTo.bevelAdded:
        cm_attrs.append("bevelWidth")
        cm_attrs.append("bevelSegments")
        cm_attrs.append("bevelProfile")
    # match properties from 'cmFrom' to 'cmTo'
    for attr in cm_attrs:
        oldVal = getattr(cmFrom, attr)
        setattr(cmTo, attr, oldVal)


# ui list item actions
class Bricker_Uilist_actions(bpy.types.Operator):
    bl_idname = "cmlist.list_action"
    bl_label = "Brick Model List Action"

    action = bpy.props.EnumProperty(
        items=(
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
            ('REMOVE', "Remove", ""),
            ('ADD', "Add", ""),
        )
    )

    # @classmethod
    # def poll(self, context):
    #     """ ensures operator can execute (if not, returns false) """
    #     scn = context.scene
    #     for cm in scn.cmlist:
    #         if cm.animated:
    #             return False
    #     return True

    def execute(self, context):
        try:
            scn = context.scene
            idx = scn.cmlist_index

            try:
                item = scn.cmlist[idx]
            except IndexError:
                pass

            if self.action == 'REMOVE' and len(scn.cmlist) > 0 and scn.cmlist_index >= 0:
                self.removeItem(idx)

            elif self.action == 'ADD':
                self.addItem()

            elif self.action == 'DOWN' and idx < len(scn.cmlist) - 1:
                self.moveDown(item)

            elif self.action == 'UP' and idx >= 1:
                self.moveUp(item)
        except:
            handle_exception()
        return{"FINISHED"}

    def addItem(self):
        scn = bpy.context.scene
        active_object = scn.objects.active
        # if active object isn't on visible layer, don't set it as default source for new model
        if active_object:
            objVisible = False
            for i in range(20):
                if active_object.layers[i] and scn.layers[i]:
                    objVisible = True
            if not objVisible:
                active_object = None
        # if active object already has a model or isn't on visible layer, don't set it as default source for new model
        # NOTE: active object may have been removed, so we need to re-check if none
        if active_object:
            for cm in scn.cmlist:
                if cm.source_name == active_object.name:
                    active_object = None
                    break
        item = scn.cmlist.add()
        last_index = scn.cmlist_index
        scn.cmlist_index = len(scn.cmlist)-1
        if active_object and active_object.type == "MESH" and not active_object.name.startswith("Bricker_"):
            item.source_name = active_object.name
            item.name = active_object.name
            item.version = bpy.props.rebrickr_version
            # set up default brickHeight values
            source = bpy.data.objects.get(item.source_name)
            if source:
                source_details = bounds(source)
                h = max(source_details.x.dist, source_details.y.dist, source_details.z.dist)
                # update brick height based on model height
                item.brickHeight = h / 20

        else:
            item.source_name = ""
            item.name = "<New Model>"
        # get all existing IDs
        existingIDs = [cm.id for cm in scn.cmlist]
        i = max(existingIDs) + 1
        # protect against massive item IDs
        if i > 9999:
            i = 1
            while i in existingIDs:
                i += 1
        # set item ID to unique number
        item.id = i
        item.idx = len(scn.cmlist)-1
        item.startFrame = scn.frame_start
        item.stopFrame = scn.frame_end

    def removeItem(self, idx):
        scn, cm, sn = getActiveContextInfo()
        n = cm.name
        if not cm.modelCreated and not cm.animated:
            if len(scn.cmlist) - 1 == scn.cmlist_index:
                scn.cmlist_index -= 1
            scn.cmlist.remove(idx)
            if scn.cmlist_index == -1 and len(scn.cmlist) > 0:
                scn.cmlist_index = 0
        else:
            self.report({"WARNING"}, 'Please delete the Brickified model before attempting to remove this item.' % locals())

    def moveDown(self, item):
        scn = bpy.context.scene
        scn.cmlist.move(scn.cmlist_index, scn.cmlist_index+1)
        scn.cmlist_index += 1
        self.updateIdxs(scn.cmlist)

    def moveUp(self, item):
        scn = bpy.context.scene
        scn.cmlist.move(scn.cmlist_index, scn.cmlist_index-1)
        scn.cmlist_index -= 1
        self.updateIdxs(scn.cmlist)

    def updateIdxs(self, cmlist):
        for i,cm in enumerate(cmlist):
            cm.idx = i


# -------------------------------------------------------------------
# draw
# -------------------------------------------------------------------

# custom list
class Bricker_UL_items(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # Make sure your code supports all 3 layout types
        if self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
        split = layout.split(0.9)
        split.prop(item, "name", text="", emboss=False, translate=False, icon='MOD_REMESH')

    def invoke(self, context, event):
        pass


# copy settings from current index to all other indices (exclude height)
class Bricker_Uilist_copySettingsToOthersExcludeHeight(bpy.types.Operator):
    bl_idname = "cmlist.copy_to_others_exclude_height"
    bl_label = "Copy Settings to Other Brick Models (excluding Brick Height)"
    bl_description = "Copies the settings (excluding 'Brick Height' setting) from the current model to all other Brick Models"

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns false) """
        scn = context.scene
        if scn.cmlist_index == -1:
            return False
        if len(scn.cmlist) == 1:
            return False
        return True

    def execute(self, context):
        try:
            scn, cm0, _ = getActiveContextInfo()
            for cm1 in scn.cmlist:
                if cm0 != cm1:
                    matchProperties(cm1, cm0)
        except:
            handle_exception()
        return{'FINISHED'}


# copy settings from current index to all other indices
class Bricker_Uilist_copySettingsToOthers(bpy.types.Operator):
    bl_idname = "cmlist.copy_to_others"
    bl_label = "Copy Settings to Other Brick Models"
    bl_description = "Copies the settings from the current model to all other Brick Models"

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns false) """
        scn = context.scene
        if scn.cmlist_index == -1:
            return False
        if len(scn.cmlist) == 1:
            return False
        return True

    def execute(self, context):
        try:
            scn, cm0, _ = getActiveContextInfo()
            for cm1 in scn.cmlist:
                if cm0 != cm1:
                    matchProperties(cm1, cm0, bh=True)
        except:
            handle_exception()
        return{'FINISHED'}


# copy settings from current index to memory
class Bricker_Uilist_copySettings(bpy.types.Operator):
    bl_idname = "cmlist.copy_settings"
    bl_label = "Copy Settings from Current Brick Model"
    bl_description = "Stores the ID of the current model for pasting"

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns false) """
        scn = context.scene
        if scn.cmlist_index == -1:
            return False
        return True

    def execute(self, context):
        try:
            scn, cm, _ = getActiveContextInfo()
            scn.Bricker_copy_from_id = cm.id
        except:
            handle_exception()
        return{'FINISHED'}


# paste settings from index in memory to current index
class Bricker_Uilist_pasteSettings(bpy.types.Operator):
    bl_idname = "cmlist.paste_settings"
    bl_label = "Paste Settings to Current Brick Model"
    bl_description = "Pastes the settings from stored model ID to the current index"

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns false) """
        scn = context.scene
        if scn.cmlist_index == -1:
            return False
        return True

    def execute(self, context):
        try:
            scn, cm0, _ = getActiveContextInfo()
            for cm1 in scn.cmlist:
                if cm0 != cm1 and cm1.id == scn.Bricker_copy_from_id:
                    matchProperties(cm0, cm1)
                    break
        except:
            handle_exception()
        return{'FINISHED'}


# set source to active button
class Bricker_Uilist_setSourceToActive(bpy.types.Operator):
    bl_idname = "cmlist.set_to_active"
    bl_label = "Set Bricker Source to Active Object"
    bl_description = "Set source to active object in scene"

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns false) """
        scn = context.scene
        if scn.cmlist_index == -1:
            return False
        active_obj = context.scene.objects.active
        if active_obj is None:
            return False
        for i in range(20):
            if scn.layers[i] and active_obj.layers[i]:
                return True
        return False

    def execute(self, context):
        try:
            scn, cm, _ = getActiveContextInfo()
            active_object = context.scene.objects.active
            if cm.source_name != active_object.name:
                cm.source_name = active_object.name
        except:
            handle_exception()

        return{'FINISHED'}


# select button
class Bricker_Uilist_selectSource(bpy.types.Operator):
    bl_idname = "cmlist.select_source"
    bl_label = "Select Source Object"
    bl_description = "Select only source object for model"

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns false) """
        scn = context.scene
        if scn.cmlist_index == -1:
            return False
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        Bricker_source = "Bricker_%(n)s" % locals()
        if groupExists(Bricker_source) and len(bpy.data.groups[Bricker_source].objects) == 1:
            return True
        obj = py.data.objects.get(n)
        if obj and obj.type == "MESH":
            return True
        return False

    def execute(self, context):
        try:
            scn, cm, n = getActiveContextInfo()
            obj = bpy.data.objects[n]
            select(obj, active=obj)
        except:
            handle_exception()
        return{'FINISHED'}


# select button
class Bricker_Uilist_selectAllBricks(bpy.types.Operator):
    bl_idname = "cmlist.select_bricks"
    bl_label = "Select All Bricks"
    bl_description = "Select only bricks in model"

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns false) """
        scn = context.scene
        if scn.cmlist_index == -1:
            return False
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        Bricker_bricks = "Bricker_%(n)s_bricks" % locals()
        if groupExists(Bricker_bricks) and len(bpy.data.groups[Bricker_bricks].objects) != 0:
            return True
        return False

    def execute(self, context):
        try:
            scn, cm, n = getActiveContextInfo()
            Bricker_bricks = "Bricker_%(n)s_bricks" % locals()
            if groupExists(Bricker_bricks):
                objs = list(bpy.data.groups[Bricker_bricks].objects)
                select(active=objs[0])
                if len(objs) > 0:
                    select(objs)
        except:
            handle_exception()
        return{'FINISHED'}


def uniquifyName(self, context):
    """ if Brick Model exists with name, add '.###' to the end """
    scn, cm, _ = getActiveContextInfo()
    name = cm.name
    while scn.cmlist.keys().count(name) > 1:
        if name[-4] == ".":
            try:
                num = int(name[-3:])+1
            except ValueError:
                num = 1
            name = name[:-3] + "%03d" % (num)
        else:
            name = name + ".001"
    if cm.name != name:
        cm.name = name


# def updateMeshObjectName(self, context, n):
#     obj = bpy.data.objects.get(n)
#     if obj is None:
#         self.report({"WARNING"}, "Object could not be found in the scene")
#     elif obj.type != "MESH":
#         self.report({"WARNING"}, "Object is not of type 'MESH'")
#     else:
#         cm.dirtyModel = True
#         return None
#
# def updateCustomObjName(self, context):
#     scn = bpy.context.scene
#     cm = scn.cmlist[scn.cmlist_index]
#     updateMeshObjectName(self, context, cm.customObjectName)
#

def setNameIfEmpty(self, context):
    scn = context.scene
    last_cmlist_index = scn.cmlist_index
    cm0 = scn.cmlist[last_cmlist_index]
    # verify model doesn't exist with that name
    if cm0.source_name != "":
        for i, cm1 in enumerate(scn.cmlist):
            if cm1 != cm0 and cm1.source_name == cm0.source_name:
                cm0.source_name = ""
                scn.cmlist_index = i
    # if scn.cmlist_index == last_cmlist_index:
    #     updateMeshObjectName(self, context, cm0.source_name)


def updateBevel(self, context):
    # get bricks to bevel
    try:
        scn, cm, n = getActiveContextInfo()
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        if cm.lastBevelWidth != cm.bevelWidth or cm.lastBevelSegments != cm.bevelSegments or cm.lastBevelProfile != cm.bevelProfile:
            bricks = getBricks()
            createBevelMods(bricks)
            cm.lastBevelWidth = cm.bevelWidth
            cm.lastBevelSegments = cm.bevelSegments
            cm.lastBevelProfile = cm.bevelProfile
    except Exception as e:
        print(e)
        pass


def updateStartAndStopFrames(self, context):
    scn, cm, _ = getActiveContextInfo()
    if cm.useAnimation:
        cm.startFrame = scn.frame_start
        cm.stopFrame = scn.frame_end


def updateParentExposure(self, context):
    scn, cm, _ = getActiveContextInfo()
    if not (cm.modelCreated or cm.animated):
        return
    if cm.exposeParent:
        parentOb = bpy.data.objects.get(cm.parent_name)
        if parentOb:
            safeLink(parentOb, unhide=True, protect=True)
            select(parentOb, active=parentOb)
    else:
        parentOb = bpy.data.objects.get(cm.parent_name)
        if parentOb:
            safeUnlink(parentOb)


def updateModelScale(self, context):
    scn, cm, _ = getActiveContextInfo()
    if not (cm.modelCreated or cm.animated):
        return
    _, _, s = getTransformData()
    parentOb = bpy.data.objects.get(cm.parent_name)
    if parentOb:
        parentOb.scale = Vector(s) * cm.transformScale


def dirtyAnim(self, context):
    scn, cm, _ = getActiveContextInfo()
    cm.animIsDirty = True


def dirtyMaterial(self, context):
    scn, cm, _ = getActiveContextInfo()
    cm.materialIsDirty = True


def dirtyModel(self, context):
    scn, cm, _ = getActiveContextInfo()
    cm.modelIsDirty = True


def dirtyMatrix(self=None, context=None):
    scn, cm, _ = getActiveContextInfo()
    cm.matrixIsDirty = True


def dirtyInternal(self, context):
    scn, cm, _ = getActiveContextInfo()
    cm.internalIsDirty = True


def dirtyBuild(self, context):
    scn, cm, _ = getActiveContextInfo()
    cm.buildIsDirty = True


def dirtyBricks(self, context):
    scn, cm, _ = getActiveContextInfo()
    cm.bricksAreDirty = True


# def updateActiveObject(self, context):
#     scn, cm, _ = getActiveContextInfo()
#     dictKey = cm.activeBFMKey
#     bricksDict, _ = getBricksDict(cm=cm)
#     brickD = bricksDict[dictKey]
#     obj = bpy.data.objects.get(brickD["name"])
#     if obj:
#         select(obj, active=obj, only=False)


# Create custom property group
class Bricker_CreatedModels(bpy.types.PropertyGroup):
    name = StringProperty(update=uniquifyName)
    id = IntProperty()
    idx = IntProperty()

    source_name = StringProperty(
        name="Source Object Name",
        description="Name of the source object to Brickify",
        default="",
        update=setNameIfEmpty)

    parent_name = StringProperty(
        name="Parent Object Name",
        description="Name of the parent object for the brickified model",
        default="")

    lastShellThickness = IntProperty(default=1)
    shellThickness = IntProperty(
        name="Shell Thickness",
        description="Thickness of the Brick shell",
        update=dirtyBuild,
        min=1, max=100,
        default=1)

    studDetail = EnumProperty(
        name="Stud Detailing",
        description="Choose where to draw the studs",
        items=[("ALL", "On All Bricks", "Include Brick Logo only on bricks with studs exposed"),
               ("EXPOSED", "On Exposed Bricks", "Include Brick Logo only on bricks with studs exposed"),
               ("NONE", "None", "Don't include Brick Logo on bricks")],
        update=dirtyBricks,
        default="EXPOSED")

    logoDetail = EnumProperty(
        name="Logo Detailing",
        description="Choose where to draw the logo",
        items=[("CUSTOM", "Custom Logo", "Choose a mesh object to use as the brick stud logo"),
               ("LEGO", "LEGO Logo", "Include a LEGO logo on each stud"),
               ("NONE", "None", "Don't include Brick Logo on bricks")],
        update=dirtyBricks,
        default="NONE")

    logoResolution = FloatProperty(
        name="Logo Resolution",
        description="Resolution of the Brick Logo",
        update=dirtyBricks,
        min=0.1, max=1,
        step=1,
        precision=1,
        default=0.2)

    logoObjectName = StringProperty(
        name="Logo Object Name",
        description="Name of the logo object",
        update=dirtyBricks,
        default="")
    logoScale = FloatProperty(
        name="Logo Scale",
        description="Scale of the logo (relative to stud scale)",
        step=1,
        update=dirtyBricks,
        precision=2,
        min=0.000001, max=2,
        default=0.78)
    logoInset = FloatProperty(
        name="Logo Scale",
        description="How deep to inset the logo into the stud",
        step=1,
        update=dirtyBricks,
        precision=2,
        min=0.0, max=1.0,
        default=0.02)

    hiddenUndersideDetail = EnumProperty(
        name="Hidden Underside Detailing",
        description="Choose the level of detail to include for the underside of hidden bricks",
        items=[("HIGH", "High Detail", "Draw intricate details on brick underside"),
               ("MEDIUM", "Medium Detail", "Draw most details on brick underside"),
               ("LOW", "Low Detail", "Draw minimal details on brick underside"),
               ("FLAT", "Flat", "draw single face on brick underside")],
        update=dirtyBricks,
        default="FLAT")
    exposedUndersideDetail = EnumProperty(
        name="Eposed Underside Detailing",
        description="Choose the level of detail to include for the underside of exposed bricks",
        items=[("HIGH", "High Detail", "Draw intricate details on brick underside"),
               ("MEDIUM", "Medium Detail", "Draw most details on brick underside"),
               ("LOW", "Low Detail", "Draw minimal details on brick underside"),
               ("FLAT", "Flat", "draw single face on brick underside")],
        update=dirtyBricks,
        default="FLAT")

    circleVerts = IntProperty(
        name="Num Verts",
        description="Number of vertices for each circle of brick mesh",
        update=dirtyBricks,
        min=4, max=64,
        default=16)

    modelScaleX = FloatProperty(
        name="Model Scale X",
        description="Scale of the source object to Brickify on X axis",
        default=-1)
    modelScaleY = FloatProperty(
        name="Model Scale Y",
        description="Scale of the source object to Brickify on Y axis",
        default=-1)
    modelScaleZ = FloatProperty(
        name="Model Scale Z",
        description="Scale of the source object to Brickify on Z axis",
        default=-1)
    brickHeight = FloatProperty(
        name="Brick Height",
        description="Height of the bricks in the final Brick Model",
        update=dirtyMatrix,
        step=1,
        precision=3,
        min=0.001, max=10,
        default=0.1)
    gap = FloatProperty(
        name="Gap Between Bricks",
        description="Distance between bricks",
        update=dirtyMatrix,
        step=1,
        precision=3,
        min=0, max=0.1,
        default=0.01)

    mergeSeed = IntProperty(
        name="Random Seed",
        description="Random seed for brick merging calculations",
        update=dirtyBuild,
        min=-1, max=5000,
        default=1000)

    randomLoc = FloatProperty(
        name="Random Location",
        description="Max random location applied to each brick",
        update=dirtyModel,
        step=1,
        precision=3,
        min=0, max=1,
        default=0.005)
    randomRot = FloatProperty(
        name="Random Rotation",
        description="Max random rotation applied to each brick",
        update=dirtyModel,
        step=1,
        precision=3,
        min=0, max=1,
        default=0.025)

    lastBrickType = StringProperty(default="BRICKS")
    brickType = EnumProperty(
        name="Brick Type",
        description="Type of brick used to build the model",
        items=[("PLATES", "Plates Only", "Use plates to build the model"),
               ("BRICKS", "Bricks Only (fast)", "Use bricks to build the model"),
               ("BRICKS AND PLATES", "Bricks and Plates", "Use bricks and plates to build the model"),
               ("CUSTOM", "Custom", "Use custom object to build the model")],
        update=dirtyMatrix,
        default="BRICKS")
    alignBricks = BoolProperty(
        name="Align Bricks Horizontally",
        description="Keep bricks aligned horizontally, and fill the gaps with plates",
        update=dirtyBuild,
        default=True)
    offsetBrickLayers = IntProperty(
        name="Offset Brick Layers",
        description="Offset the layers that will be merged into bricks if possible",
        update=dirtyBuild,
        step=1,
        min=0, max=2,
        default=1)

    originSet = BoolProperty(
        name="Center brick origins",
        description="Set all brick origins to center of bricks (slower)",
        update=dirtyBricks,
        default=False)

    distOffsetX = FloatProperty(
        name="X",
        description="Offset of custom bricks on X axis (1.0 = side-by-side)",
        update=dirtyMatrix,
        step=1,
        precision=3,
        min=0.001, max=2,
        default=1)
    distOffsetY = FloatProperty(
        name="Y",
        description="Offset of custom bricks on Y axis (1.0 = side-by-side)",
        step=1,
        update=dirtyMatrix,
        precision=3,
        min=0.001, max=2,
        default=1)
    distOffsetZ = FloatProperty(
        name="Z",
        description="Offset of custom bricks on Z axis (1.0 = side-by-side)",
        step=1,
        update=dirtyMatrix,
        precision=3,
        min=0.001, max=2,
        default=1)

    customObjectName = StringProperty(
        name="Custom Object Name",
        description="Name of the object to use as bricks",
        update=dirtyMatrix,
        default="")

    maxWidth = IntProperty(
        name="Max Width",
        description="Maximum brick width",
        update=dirtyBuild,
        step=1,
        min=1, max=16,
        default=2)
    maxDepth = IntProperty(
        name="Max Depth",
        description="Maximum brick depth",
        update=dirtyBuild,
        step=1,
        min=1, max=24,
        default=10)

    # used to check rebrickr version model was created with
    version = StringProperty(default="1_0_4")
    # left over from rebrickr v1.0
    maxBrickScale1 = IntProperty(default=-1)
    maxBrickScale2 = IntProperty(default=-1)

    splitModel = BoolProperty(
        name="Split Model",
        description="Split model into separate objects (slower)",
        update=dirtyModel,
        default=False)

    internalSupports = EnumProperty(
        name="Internal Supports",
        description="Choose what type of brick support structure to use inside your model",
        items=[("NONE", "None", "No internal supports"),
               ("LATTICE", "Lattice", "Use latice inside model"),
               ("COLUMNS", "Columns", "Use columns inside model")],
        update=dirtyInternal,
        default="NONE")
    latticeStep = IntProperty(
        name="Lattice Step",
        description="Distance between cross-beams",
        update=dirtyInternal,
        step=1,
        min=2, max=25,
        default=2)
    alternateXY = BoolProperty(
        name="Alternate X and Y",
        description="Alternate back-and-forth and side-to-side beams",
        update=dirtyInternal,
        default=False)
    colThickness = IntProperty(
        name="Column Thickness",
        description="Thickness of the columns",
        update=dirtyInternal,
        min=1, max=25,
        default=2)
    colStep = IntProperty(
        name="Column Step",
        description="Distance between columns",
        update=dirtyInternal,
        step=1,
        min=1, max=25,
        default=2)

    materialType = EnumProperty(
        name="Material Type",
        description="Choose what materials will be applied to model",
        items=[("NONE", "None", "No material applied to bricks"),
               ("RANDOM", "Rand om", "Apply a random material from Brick materials to each generated brick"),
               ("CUSTOM", "Cust om", "Choose a custom material to apply to all generated bricks"),
               ("SOURCE", "Use Source Materials", "Apply material based on closest intersecting face")],
        update=dirtyMaterial,
        default="SOURCE")
    materialName = StringProperty(
        name="Material Name",
        description="Name of the material to apply to all bricks",
        default="")
    internalMatName = StringProperty(
        name="Material Name",
        description="Name of the material to apply to bricks inside material shell",
        update=dirtyMaterial,
        default="")
    matShellDepth = IntProperty(
        name="Material Shell Depth",
        description="Depth to which the outer materials should be applied (1 = Only exposed bricks",
        step=1,
        min=1, max=100,
        default=1,
        update=dirtyModel)
    mergeInconsistentMats = BoolProperty(
        name="Merge Inconsistent Materials",
        description="Merge 1x1 bricks to form larger bricks whether or not they share a material",
        default=False,
        update=dirtyBuild)
    randomMatSeed = IntProperty(
        name="Random Seed",
        description="Random seed for material assignment",
        min=-1, max=5000,
        default=1000)
    useUVMap = BoolProperty(
        name="Use UV Map",
        description="Transfer colors from source UV map",
        default=True,
        update=dirtyMaterial)
    uvImageName = StringProperty(
        name="UV Image",
        description="UV Image to use for UV Map color transfer (defaults to active UV if left blank)",
        default="",
        update=dirtyBuild)
    snapToBrickColors = BoolProperty(
        name="Snap to Brick Colors",
        description="Snap nearest material to brick material",
        default=False,
        update=dirtyMaterial)
    colorSnapAmount = FloatProperty(
        name="Color Snap Amount",
        description="Amount to snap colors by",
        precision=3,
        min=0.0, max=1.0,
        default=0.0,
        update=dirtyBuild)

    lastMatrixSettings = StringProperty(default="")
    useNormals = BoolProperty(
        name="Use Normals",
        description="Use normals to calculate insideness of bricks (WARNING: May produce inaccurate model if source is not single closed mesh)",
        default=False,
        update=dirtyMatrix)
    verifyExposure = BoolProperty(
        name="Verify Exposure",
        description="Run additional calculations to verify exposure of studs and underside detailing (WARNING: May compromise 'Shell Thickness' functionality if source is not single closed mesh)",
        default=False,
        update=dirtyMatrix)
    insidenessRayCastDir = EnumProperty(
        name="Insideness Ray Cast Direction",
        description="Choose which axis/axes to cast rays for calculation of insideness",
        items=[("HIGH EFFICIENCY", "High Efficiency", "Reuses single ray casted in brickFreqMatrix calculations"),
               ("X", "X", "Cast rays along X axis for insideness calculations"),
               ("Y", "Y", "Cast rays along Y axis for insideness calculations"),
               ("Z", "Z", "Cast rays along Z axis for insideness calculations"),
               ("XYZ", "XYZ (Best Result)", "Cast rays in all axis directions for insideness calculation (slowest; uses result consistent for at least 2 of the 3 rays)")],
        update=dirtyMatrix,
        default="HIGH EFFICIENCY")
    castDoubleCheckRays = BoolProperty(
        name="Cast Both Directions",
        description="Cast rays in both positive and negative directions on the axes specified for insideness calculation (Favors outside; uncheck to cast only in positive direction)",
        default=True,
        update=dirtyMatrix)

    objVerts = IntProperty(default=0)
    objPolys = IntProperty(default=0)
    objEdges = IntProperty(default=0)
    isWaterTight = BoolProperty(default=False)
    maxDepthExceeded = BoolProperty(default=False)

    lastLogoDetail = StringProperty(default="NONE")
    lastLogoResolution = FloatProperty(default=0)
    lastSplitModel = BoolProperty(default=False)
    lastStartFrame = IntProperty(default=-1)
    lastStopFrame = IntProperty(default=-1)
    lastSourceMid = StringProperty(default="-1,-1,-1")
    lastMaterialType = StringProperty(default="SOURCE")

    modelLoc = StringProperty(default="-1,-1,-1")
    modelRot = StringProperty(default="-1,-1,-1")
    modelScale = StringProperty(default="-1,-1,-1")
    transformScale = FloatProperty(
        name="Scale",
        description="Scale of the brick model",
        update=updateModelScale,
        step=1,
        default=1.0)
    applyToSourceObject = BoolProperty(
        name="Apply to source",
        description="Apply transformations to source object when Brick Model is deleted",
        default=True)
    exposeParent = BoolProperty(
        name="Expose parent object",
        description="Expose the parent object for this model and make it active for simple transformations",
        update=updateParentExposure,
        default=False)

    # Bevel Settings
    lastBevelWidth = FloatProperty()
    bevelWidth = FloatProperty(
        name="Bevel Width",
        description="Bevel value/amount",
        step=1,
        min=0.000001, max=10,
        default=0.01,
        update=updateBevel)
    lastBevelSegments = IntProperty()
    bevelSegments = IntProperty(
        name="Bevel Resolution",
        description="Number of segments for round edges/verts",
        step=1,
        min=1, max=10,
        default=1,
        update=updateBevel)
    lastBevelProfile = IntProperty()
    bevelProfile = FloatProperty(
        name="Bevel Profile",
        description="The profile shape (0.5 = round)",
        step=1,
        min=0, max=1,
        default=0.7,
        update=updateBevel)

    # ANIMATION SETTINGS
    startFrame = IntProperty(
        name="Start Frame",
        description="Start frame of Brick animation",
        update=dirtyAnim,
        min=0, max=500000,
        default=1)
    stopFrame = IntProperty(
        name="Stop Frame",
        description="Stop frame of Brick animation",
        update=dirtyAnim,
        min=0, max=500000,
        default=10)
    useAnimation = BoolProperty(
        name="Use Animation",
        description="Create Brick Model for each frame, from start to stop frame (WARNING: Calculation takes time, and may result in large blend file size)",
        update=updateStartAndStopFrames,
        default=False)

    autoUpdateExposed = BoolProperty(
        name="Auto Update Exposed",
        description="When bricks are deleted, automatically update bricks that become exposed",
        default=True)

    # CACHED BRICKFREQMATRIX
    BFMCache = StringProperty(default="")
    # source_hash = StringProperty(default="")

    # ADVANCED SETTINGS
    brickShell = EnumProperty(
        name="Brick Shell",
        description="Choose whether the shell of the model will be inside or outside source mesh",
        items=[("INSIDE", "Inside Mesh (recommended)", "Draw brick shell inside source mesh (Recommended)"),
               ("OUTSIDE", "Outside Mesh", "Draw brick shell outside source mesh"),
               ("INSIDE AND OUTSIDE", "Inside and Outside", "Draw brick shell inside and outside source mesh (two layers)")],
        update=dirtyMatrix,
        default="INSIDE")
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
        update=dirtyMatrix,
        default="XY")
    useLocalOrient = BoolProperty(
        name="Use Local Orient",
        description="When bricks are deleted, automatically update bricks that become exposed",
        default=False)

    activeKeyX = IntProperty(default=-1)
    activeKeyY = IntProperty(default=-1)
    activeKeyZ = IntProperty(default=-1)
    firstKey = StringProperty(default="")

    modelCreatedOnFrame = IntProperty(default=-1)

    numBricksGenerated = IntProperty(default=-1)

    modelCreated = BoolProperty(default=False)
    animated = BoolProperty(default=False)
    materialApplied = BoolProperty(default=False)
    armature = BoolProperty(default=False)
    bevelAdded = BoolProperty(default=False)
    customized = BoolProperty(default=True)
    brickSizesUsed = StringProperty(default="")  # list of brickSizes used separated by | (e.g. '5,4,3|7,4,5|8,6,5')
    brickTypesUsed = StringProperty(default="")  # list of brickTypes used separated by | (e.g. 'PLATE|BRICK|STUD')

    animIsDirty = BoolProperty(default=True)
    materialIsDirty = BoolProperty(default=True)
    brickMaterialsAreDirty = BoolProperty(default=True)
    modelIsDirty = BoolProperty(default=True)
    buildIsDirty = BoolProperty(default=True)
    bricksAreDirty = BoolProperty(default=True)
    matrixIsDirty = BoolProperty(default=True)
    internalIsDirty = BoolProperty(default=True)

    blender_undo_state = IntProperty(default=0)


# -------------------------------------------------------------------
# register
# -------------------------------------------------------------------


def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.createdModelsCollection = CollectionProperty(type=Bricker_CreatedModels)
    bpy.types.Scene.cmlist_index = IntProperty()


def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.createdModelsCollection
    del bpy.types.Scene.cmlist_index


if __name__ == "__main__":
    register()
