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
from bpy.app.handlers import persistent
from mathutils import Vector, Euler

# Rebrickr imports
from ..functions import *
from ..lib.bricksDict import lightToDeepCache, deepToLightCache, getDictKey
from ..lib.caches import rebrickr_bfm_cache
from ..buttons.brickMods import *

def rebrickrIsActive():
    try:
        rebrickrIsActive = bpy.props.rebrickr_module_name in bpy.context.user_preferences.addons.keys()
    except AttributeError:
        rebrickrIsActive = False
    return rebrickrIsActive

def getAnimAdjustedFrame(cm, frame):
    if frame < cm.lastStartFrame:
        curFrame = cm.lastStartFrame
    elif frame > cm.lastStopFrame:
        curFrame = cm.lastStopFrame
    else:
        curFrame = frame
    return curFrame

@persistent
def handle_animation(scene):
    scn = scene
    if rebrickrIsActive():
        for i,cm in enumerate(scn.cmlist):
            if cm.animated:
                n = cm.source_name
                for cf in range(cm.lastStartFrame, cm.lastStopFrame + 1):
                    curBricks = bpy.data.groups.get("Rebrickr_%(n)s_bricks_frame_%(cf)s" % locals())
                    adjusted_frame_current = getAnimAdjustedFrame(cm, scn.frame_current)
                    onCurF = adjusted_frame_current == cf
                    if curBricks is not None:
                        for brick in curBricks.objects:
                            # hide bricks from view and render unless on current frame
                            if brick.hide == onCurF:
                                brick.hide = not onCurF
                                brick.hide_render = not onCurF
                            if scn.objects.active is not None and "Rebrickr_%(n)s_bricks_combined_frame_" % locals() in scn.objects.active.name and onCurF:
                                select(brick, active=brick)
                            # prevent bricks from being selected on frame change
                            elif brick.select:
                                brick.select = False

bpy.app.handlers.frame_change_pre.append(handle_animation)

def isObjVisible(scn, cm):
    scn = bpy.context.scene
    n = cm.source_name
    objVisible = False
    if cm.modelCreated or cm.animated:
        gn = "Rebrickr_%(n)s_bricks" % locals()
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

@persistent
def handle_selections(scene):
    scn = bpy.context.scene
    try:
        rebrickrRunningOp = scn.Rebrickr_runningOperation
    except AttributeError:
        rebrickrRunningOp = False
    if rebrickrIsActive() and not rebrickrRunningOp:
        # if scn.layers changes and active object is no longer visible, set scn.cmlist_index to -1
        if scn.Rebrickr_last_layers != str(list(scn.layers)):
            scn.Rebrickr_last_layers = str(list(scn.layers))
            curObjVisible = False
            if scn.cmlist_index != -1:
                cm0 = scn.cmlist[scn.cmlist_index]
                curObjVisible,_ = isObjVisible(scn, cm0)
            if not curObjVisible or scn.cmlist_index == -1:
                setIndex = False
                for i,cm in enumerate(scn.cmlist):
                    if i != scn.cmlist_index:
                        nextObjVisible,obj = isObjVisible(scn, cm)
                        if nextObjVisible and bpy.context.active_object == obj:
                            scn.cmlist_index = i
                            setIndex = True
                            break
                if not setIndex:
                    scn.cmlist_index = -1
        # select and make source or Brick Model active if scn.cmlist_index changes
        elif scn.Rebrickr_last_cmlist_index != scn.cmlist_index and scn.cmlist_index != -1:
            scn.Rebrickr_last_cmlist_index = scn.cmlist_index
            cm = scn.cmlist[scn.cmlist_index]
            obj = bpy.data.objects.get(cm.source_name)
            if obj is None:
                obj = bpy.data.objects.get(cm.source_name + " (DO NOT RENAME)")
            if obj is not None:
                if cm.modelCreated:
                    n = cm.source_name
                    bricks = getBricks()
                    if bricks is not None and len(bricks) > 0:
                        select(bricks, active=bricks[0])
                        scn.Rebrickr_last_active_object_name = scn.objects.active.name
                elif cm.animated:
                    n = cm.source_name
                    cf = scn.frame_current
                    if cf > cm.stopFrame:
                        cf = cm.stopFrame
                    elif cf < cm.startFrame:
                        cf = cm.startFrame
                    gn = "Rebrickr_%(n)s_bricks_frame_%(cf)s" % locals()
                    if len(bpy.data.groups[gn].objects) > 0:
                        select(list(bpy.data.groups[gn].objects), active=bpy.data.groups[gn].objects[0])
                        scn.Rebrickr_last_active_object_name = scn.objects.active.name
                else:
                    select(obj, active=obj)
                scn.Rebrickr_last_active_object_name = obj.name
            else:
                for i in range(len(scn.cmlist)):
                    cm = scn.cmlist[i]
                    if cm.source_name == scn.Rebrickr_active_object_name:
                        select(None)
                        break
        # open Brick Model settings for active object if active object changes
        elif scn.objects.active and scn.Rebrickr_last_active_object_name != scn.objects.active.name and len(scn.cmlist) > 0 and ( scn.cmlist_index == -1 or scn.cmlist[scn.cmlist_index].source_name != "") and scn.objects.active.type == "MESH":
            scn.Rebrickr_last_active_object_name = scn.objects.active.name
            beginningString = "Rebrickr_"
            if scn.objects.active.name.startswith(beginningString):
                usingSource = False
                if "_bricks" in scn.objects.active.name:
                    frameLoc = scn.objects.active.name.rfind("_bricks")
                elif "_brick_" in scn.objects.active.name:
                    frameLoc = scn.objects.active.name.rfind("_brick_")
                else:
                    frameLoc = None
                if frameLoc is not None:
                    scn.Rebrickr_active_object_name = scn.objects.active.name[len(beginningString):frameLoc]
            else:
                usingSource = True
                scn.Rebrickr_active_object_name = scn.objects.active.name
            for i in range(len(scn.cmlist)):
                cm = scn.cmlist[i]
                if cm.source_name == scn.Rebrickr_active_object_name and (not usingSource or not cm.modelCreated):
                    scn.cmlist_index = i
                    scn.Rebrickr_last_cmlist_index = scn.cmlist_index
                    active_obj = scn.objects.active
                    if active_obj.isBrick:
                        # adjust scn.active_brick_detail based on active brick
                        _,dictLoc = getDictKey(active_obj.name)
                        x0,y0,z0 = dictLoc
                        cm.activeKeyX = x0
                        cm.activeKeyY = y0
                        cm.activeKeyZ = z0
                    return
            # if no matching cmlist item found, set cmlist_index to -1
            scn.cmlist_index = -1
        if scn.cmlist_index != -1:
            cm = scn.cmlist[scn.cmlist_index]
            # keep isWaterTight updated
            obj = bpy.data.objects.get(cm.source_name)
            if obj is not None and (len(obj.data.vertices) != cm.objVerts or len(obj.data.polygons) != cm.objPolys or len(obj.data.edges) != cm.objEdges):
                cm.objVerts = len(obj.data.vertices)
                cm.objPolys = len(obj.data.polygons)
                cm.objEdges = len(obj.data.edges)
                cm.isWaterTight = cm.objVerts + cm.objPolys - cm.objEdges == 2

bpy.app.handlers.scene_update_pre.append(handle_selections)

def find_3dview_space():
    # Find 3D_View window and its scren space
    area = None
    for a in bpy.data.window_managers[0].windows[0].screen.areas:
        if a.type == 'VIEW_3D':
            area = a
            break

    if area:
        space = area.spaces[0]
    else:
        space = bpy.context.space_data

    return space

# @persistent
# def handle_snapping(scene):
#     scn = bpy.context.scene
#     if rebrickrIsActive() and scn.Rebrickr_snapping:
#         # disable regular snapping if enabled
#         if not scn.tool_settings.use_snap:
#             scn.tool_settings.use_snap = True
#
#         if scn.cmlist_index != -1:
#             # snap transformations to scale
#             space = find_3dview_space()
#             cm = scn.cmlist[scn.cmlist_index]
#             space.grid_scale = cm.brickHeight + cm.gap
#
#
# bpy.app.handlers.scene_update_pre.append(handle_snapping)

@persistent
def handle_saving_in_edit_mode(scene):
    if rebrickrIsActive():
        sto_scn = bpy.data.scenes.get("Rebrickr_storage (DO NOT RENAME)")
        try:
            editingSourceInfo = bpy.context.window_manager["editingSourceInStorage"]
        except KeyError:
            editingSourceInfo = False
        if editingSourceInfo and bpy.context.scene == sto_scn:
            scn = bpy.context.scene
            source = bpy.data.objects.get(editingSourceInfo["source_name"])
            # if Rebrickr_storage scene is not active, set to active
            if bpy.context.scene != sto_scn:
                for screen in bpy.data.screens:
                    screen.scene = sto_scn
            # set source to object mode
            select(source, active=source)
            bpy.ops.object.mode_set(mode='OBJECT')
            setOriginToObjOrigin(toObj=source, fromLoc=editingSourceInfo["lastSourceOrigLoc"])
            # reset source origin to adjusted location
            if source["before_edit_location"] != -1:
                source.location = source["before_edit_location"]
            source.rotation_mode = "XYZ"
            source.rotation_euler = Euler(tuple(source["previous_rotation"]), "XYZ")
            source.scale = source["previous_scale"]
            setOriginToObjOrigin(toObj=source, fromLoc=source["before_origin_set_location"])
            if bpy.context.scene.name == "Rebrickr_storage (DO NOT RENAME)":
                for screen in bpy.data.screens:
                    screen.scene = bpy.data.scenes.get(bpy.props.Rebrickr_origScene)
            bpy.props.Rebrickr_commitEdits = False
            bpy.context.window_manager["editingSourceInStorage"] = False
            redraw_areas("VIEW_3D")
            scn.update()

bpy.app.handlers.save_pre.append(handle_saving_in_edit_mode)

# clear light cache before file load
@persistent
def clear_bfm_cache(dummy):
    if rebrickrIsActive():
        for key in rebrickr_bfm_cache.keys():
            rebrickr_bfm_cache[key] = None
bpy.app.handlers.load_pre.append(clear_bfm_cache)

# pull dicts from deep cache to light cache on load
@persistent
def handle_loading_to_light_cache(dummy):
    if rebrickrIsActive():
        deepToLightCache(rebrickr_bfm_cache)
bpy.app.handlers.load_post.append(handle_loading_to_light_cache)

# push dicts from light cache to deep cache on save
@persistent
def handle_storing_to_deep_cache(scene):
    if rebrickrIsActive():
        lightToDeepCache(rebrickr_bfm_cache)
bpy.app.handlers.save_pre.append(handle_storing_to_deep_cache)
