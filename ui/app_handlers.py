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

# Addon imports
from ..functions import *
from ..lib.bricksDict import lightToDeepCache, deepToLightCache, getDictKey
from ..lib.caches import bricker_bfm_cache
from ..buttons.customize.tools import *


def brickerIsActive():
    return hasattr(bpy.props, "bricker_module_name") and bpy.props.bricker_module_name in bpy.context.user_preferences.addons.keys()


def brickerRunningOp():
    scn = bpy.context.scene
    return hasattr(scn, "Bricker_runningOperation") and scn.Bricker_runningOperation


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
    if not brickerIsActive():
        return
    for i, cm in enumerate(scn.cmlist):
        if not cm.animated:
            continue
        n = cm.source_name
        for cf in range(cm.lastStartFrame, cm.lastStopFrame + 1):
            curBricks = bpy.data.groups.get("Bricker_%(n)s_bricks_frame_%(cf)s" % locals())
            if curBricks is None:
                continue
            adjusted_frame_current = getAnimAdjustedFrame(cm, scn.frame_current)
            onCurF = adjusted_frame_current == cf
            for brick in curBricks.objects:
                # hide bricks from view and render unless on current frame
                if brick.hide == onCurF:
                    brick.hide = not onCurF
                    brick.hide_render = not onCurF
                if scn.objects.active and "Bricker_%(n)s_bricks_combined_frame_" % locals() in scn.objects.active.name and onCurF:
                    select(brick, active=brick)
                # prevent bricks from being selected on frame change
                elif brick.select:
                    brick.select = False


bpy.app.handlers.frame_change_pre.append(handle_animation)


def isObjVisible(scn, cm, n):
    objVisible = False
    if cm.modelCreated or cm.animated:
        gn = "Bricker_%(n)s_bricks" % locals()
        if groupExists(gn) and len(bpy.data.groups[gn].objects) > 0:
            obj = bpy.data.groups[gn].objects[0]
        else:
            obj = None
    else:
        obj = bpy.data.objects.get(cm.source_name)
    if obj:
        objVisible = False
        for i in range(20):
            if obj.layers[i] and scn.layers[i]:
                objVisible = True
    return objVisible, obj


@persistent
def handle_selections(scene):
    scn = bpy.context.scene
    if not brickerIsActive() or brickerRunningOp():
        return
    # if scn.layers changes and active object is no longer visible, set scn.cmlist_index to -1
    if scn.Bricker_last_layers != str(list(scn.layers)):
        scn.Bricker_last_layers = str(list(scn.layers))
        curObjVisible = False
        if scn.cmlist_index != -1:
            cm0 = scn.cmlist[scn.cmlist_index]
            curObjVisible, _ = isObjVisible(scn, cm0, cm0.source_name)
        if not curObjVisible or scn.cmlist_index == -1:
            setIndex = False
            for i, cm in enumerate(scn.cmlist):
                if i != scn.cmlist_index:
                    nextObjVisible, obj = isObjVisible(scn, cm, cm.source_name)
                    if nextObjVisible and bpy.context.active_object == obj:
                        scn.cmlist_index = i
                        setIndex = True
                        break
            if not setIndex:
                scn.cmlist_index = -1
    # select and make source or Brick Model active if scn.cmlist_index changes
    elif scn.Bricker_last_cmlist_index != scn.cmlist_index and scn.cmlist_index != -1:
        scn.Bricker_last_cmlist_index = scn.cmlist_index
        cm = scn.cmlist[scn.cmlist_index]
        obj = bpy.data.objects.get(cm.source_name)
        if obj is None:
            obj = bpy.data.objects.get(cm.source_name + " (DO NOT RENAME)")
        if obj and cm.version[:3] != "1_0":
            if cm.modelCreated:
                n = cm.source_name
                bricks = getBricks()
                if bricks and len(bricks) > 0:
                    select(bricks, active=bricks[0])
                    scn.Bricker_last_active_object_name = scn.objects.active.name
            elif cm.animated:
                n = cm.source_name
                cf = scn.frame_current
                if cf > cm.stopFrame:
                    cf = cm.stopFrame
                elif cf < cm.startFrame:
                    cf = cm.startFrame
                gn = "Bricker_%(n)s_bricks_frame_%(cf)s" % locals()
                if len(bpy.data.groups[gn].objects) > 0:
                    select(list(bpy.data.groups[gn].objects), active=bpy.data.groups[gn].objects[0])
                    scn.Bricker_last_active_object_name = scn.objects.active.name
            else:
                select(obj, active=obj)
            scn.Bricker_last_active_object_name = obj.name
        else:
            for i in range(len(scn.cmlist)):
                cm = scn.cmlist[i]
                if cm.source_name == scn.Bricker_active_object_name:
                    select(None)
                    break
    # open Brick Model settings for active object if active object changes
    elif scn.objects.active and scn.Bricker_last_active_object_name != scn.objects.active.name and len(scn.cmlist) > 0 and (scn.cmlist_index == -1 or scn.cmlist[scn.cmlist_index].source_name != "") and scn.objects.active.type == "MESH":
        scn.Bricker_last_active_object_name = scn.objects.active.name
        beginningString = "Bricker_"
        if scn.objects.active.name.startswith(beginningString):
            usingSource = False
            if "_bricks" in scn.objects.active.name:
                frameLoc = scn.objects.active.name.rfind("_bricks")
            elif "_brick_" in scn.objects.active.name:
                frameLoc = scn.objects.active.name.rfind("_brick_")
            else:
                frameLoc = None
            if frameLoc is not None:
                scn.Bricker_active_object_name = scn.objects.active.name[len(beginningString):frameLoc]
        else:
            usingSource = True
            scn.Bricker_active_object_name = scn.objects.active.name
        for i in range(len(scn.cmlist)):
            cm = scn.cmlist[i]
            if createdWithUnsupportedVersion() or cm.source_name != scn.Bricker_active_object_name or (usingSource and cm.modelCreated):
                continue
            scn.cmlist_index = i
            scn.Bricker_last_cmlist_index = scn.cmlist_index
            active_obj = scn.objects.active
            if active_obj.isBrick:
                # adjust scn.active_brick_detail based on active brick
                x0, y0, z0 = getDictLoc(getDictKey(active_obj.name))
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
        if obj and (len(obj.data.vertices) != cm.objVerts or len(obj.data.polygons) != cm.objPolys or len(obj.data.edges) != cm.objEdges):
            cm.objVerts = len(obj.data.vertices)
            cm.objPolys = len(obj.data.polygons)
            cm.objEdges = len(obj.data.edges)
            cm.isWaterTight = cm.objVerts + cm.objPolys - cm.objEdges == 2


bpy.app.handlers.scene_update_pre.append(handle_selections)


@persistent
def prevent_user_from_viewing_storage_scene(scene):
    scn = bpy.context.scene
    if not brickerIsActive() or brickerRunningOp():
        return
    if scn.name == "Bricker_storage (DO NOT RENAME)":
        i = 0
        if bpy.data.scenes[i].name == scn.name:
            i += 1
        bpy.context.screen.scene = bpy.data.scenes[i]
        showErrorMessage("This scene is for Bricker internal use only")


bpy.app.handlers.scene_update_pre.append(prevent_user_from_viewing_storage_scene)


@persistent
def keep_object_names_unique(scene):
    scn = bpy.context.scene
    if not brickerIsActive() or brickerRunningOp():
        return
    # for object in scene
    for obj_name in scn.objects.keys():
        for cm in scn.cmlist:
            if obj_name != cm.source_name:
                continue
            # rename object if not part of a model or animation
            obj = bpy.data.objects.get(obj_name)
            if obj and (cm.modelCreated or cm.animated):
                obj.name = "%(obj_name)s.001" % locals()


bpy.app.handlers.scene_update_pre.append(keep_object_names_unique)


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
#     if brickerIsActive() and scn.Bricker_snapping:
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


# clear light cache before file load
@persistent
def clear_bfm_cache(dummy):
    if not brickerIsActive():
        return
    for key in bricker_bfm_cache.keys():
        bricker_bfm_cache[key] = None


bpy.app.handlers.load_pre.append(clear_bfm_cache)


# pull dicts from deep cache to light cache on load
@persistent
def handle_loading_to_light_cache(dummy):
    if not brickerIsActive():
        return
    deepToLightCache(bricker_bfm_cache)


bpy.app.handlers.load_post.append(handle_loading_to_light_cache)


# push dicts from light cache to deep cache on save
@persistent
def handle_storing_to_deep_cache(scene):
    if not brickerIsActive():
        return
    lightToDeepCache(bricker_bfm_cache)


bpy.app.handlers.save_pre.append(handle_storing_to_deep_cache)


# send parent object to scene for linking scene in other file
@persistent
def safe_link_parent(scene):
    if not brickerIsActive():
        return
    for scn in bpy.data.scenes:
        for cm in scn.cmlist:
            n = cm.source_name
            Bricker_parent_on = "Bricker_%(n)s_parent" % locals()
            p = bpy.data.objects.get(Bricker_parent_on)
            if (cm.modelCreated or cm.animated) and not cm.exposeParent:
                print(p.name)
                safeLink(p)


bpy.app.handlers.save_pre.append(safe_link_parent)


# send parent object to scene for linking scene in other file
@persistent
def safe_unlink_parent(scene):
    if not brickerIsActive():
        return
    for scn in bpy.data.scenes:
        for cm in scn.cmlist:
            n = cm.source_name
            Bricker_parent_on = "Bricker_%(n)s_parent" % locals()
            p = bpy.data.objects.get(Bricker_parent_on)
            if (cm.modelCreated or cm.animated) and not cm.exposeParent:
                safeUnlink(p)


bpy.app.handlers.save_post.append(safe_unlink_parent)
bpy.app.handlers.load_post.append(safe_unlink_parent)


@persistent
def handle_upconversion(scene):
    scn = bpy.context.scene
    if not brickerIsActive():
        return
    for cm in scn.cmlist:
        if createdWithUnsupportedVersion():
            # normalize cm.version
            if cm.version[1] == ",":
                cm.version = cm.version.replace(", ", ".")
            # convert from v1_0 to v1_1
            if int(cm.version[2]) < 1:
                cm.brickWidth = 2 if cm.maxBrickScale2 > 1 else 1
                cm.brickDepth = cm.maxBrickScale2
                cm.matrixIsDirty = True
            # convert from v1_2 to v1_3
            if int(cm.version[2]) < 3:
                if cm.colorSnapAmount == 0:
                    cm.colorSnapAmount = 0.00001
                for obj in bpy.data.objects:
                    if obj.name.startswith("Rebrickr"):
                        obj.name = obj.name.replace("Rebrickr", "Bricker")
                for scn in bpy.data.scenes:
                    if scn.name.startswith("Rebrickr"):
                        scn.name = scn.name.replace("Rebrickr", "Bricker")
                for group in bpy.data.groups:
                    if group.name.startswith("Rebrickr"):
                        group.name = group.name.replace("Rebrickr", "Bricker")


bpy.app.handlers.load_post.append(handle_upconversion)
