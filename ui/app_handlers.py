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
from bpy.app.handlers import persistent
from ..functions import *
from mathutils import Vector, Euler

@persistent
def handle_animation(scene):
    scn = scene
    if 'legoizer' in bpy.context.user_preferences.addons.keys():
        for i,cm in enumerate(scn.cmlist):
            if cm.animated:
                n = cm.source_name
                for cf in range(cm.lastStartFrame, cm.lastStopFrame + 1):
                    curBricks = bpy.data.groups.get("LEGOizer_%(n)s_bricks_frame_%(cf)s" % locals())
                    onCurF = scn.frame_current == cf or (cf == cm.lastStartFrame and scn.frame_current < cm.lastStartFrame) or (cf == cm.lastStopFrame and scn.frame_current > cm.lastStopFrame)
                    if curBricks is not None:
                        for brick in curBricks.objects:
                            # hide bricks from view and render unless on current frame
                            if brick.hide == onCurF:
                                brick.hide = not onCurF
                                brick.hide_render = not onCurF
                            if scn.objects.active is not None and "LEGOizer_%(n)s_bricks_combined_frame_" % locals() in scn.objects.active.name and onCurF:
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

@persistent
def handle_selections(scene):
    scn = bpy.context.scene
    if not scn.legoizer_runningOperation and 'legoizer' in bpy.context.user_preferences.addons.keys():
        # if scn.layers changes and active object is no longer visible, set scn.cmlist_index to -1
        if scn.legoizer_last_layers != str(list(scn.layers)):
            scn.legoizer_last_layers = str(list(scn.layers))
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
        # select and make source or LEGO model active if scn.cmlist_index changes
        elif scn.legoizer_last_cmlist_index != scn.cmlist_index and scn.cmlist_index != -1:
            scn.legoizer_last_cmlist_index = scn.cmlist_index
            cm = scn.cmlist[scn.cmlist_index]
            obj = bpy.data.objects.get(cm.source_name)
            if obj is None:
                obj = bpy.data.objects.get(cm.source_name + " (DO NOT RENAME)")
            if obj is not None:
                if cm.modelCreated:
                    n = cm.source_name
                    gn = "LEGOizer_%(n)s_bricks" % locals()
                    if groupExists(gn) and len(bpy.data.groups[gn].objects) > 0:
                        select(list(bpy.data.groups[gn].objects), active=bpy.data.groups[gn].objects[0])
                        scn.legoizer_last_active_object_name = scn.objects.active.name
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
                        scn.legoizer_last_active_object_name = scn.objects.active.name
                else:
                    select(obj, active=obj)
                scn.legoizer_last_active_object_name = obj.name
            else:
                for i in range(len(scn.cmlist)):
                    cm = scn.cmlist[i]
                    if cm.source_name == scn.legoizer_active_object_name:
                        select(None)
                        break
        # open LEGO model settings for active object if active object changes
        elif scn.objects.active and scn.legoizer_last_active_object_name != scn.objects.active.name and ( scn.cmlist_index == -1 or scn.cmlist[scn.cmlist_index].source_name != "") and scn.objects.active.type == "MESH":
            scn.legoizer_last_active_object_name = scn.objects.active.name
            if scn.objects.active.name.startswith("LEGOizer_"):
                if "_bricks" in scn.objects.active.name:
                    frameLoc = scn.objects.active.name.rfind("_bricks")
                elif "_brick_" in scn.objects.active.name:
                    frameLoc = scn.objects.active.name.rfind("_brick_")
                else:
                    frameLoc = None
                if frameLoc is not None:
                    scn.legoizer_active_object_name = scn.objects.active.name[9:frameLoc]
            else:
                scn.legoizer_active_object_name = scn.objects.active.name
            for i in range(len(scn.cmlist)):
                cm = scn.cmlist[i]
                if cm.source_name == scn.legoizer_active_object_name:
                    scn.cmlist_index = i
                    scn.legoizer_last_cmlist_index = scn.cmlist_index
                    return
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

@persistent
def handle_saving_in_edit_mode(scene):
    if 'legoizer' in bpy.context.user_preferences.addons.keys():
        sto_scn = bpy.data.scenes.get("LEGOizer_storage (DO NOT RENAME)")
        editingSourceInfo = bpy.context.window_manager["editingSourceInStorage"]
        if editingSourceInfo and bpy.context.scene == sto_scn:
            scn = bpy.context.scene
            source = bpy.data.objects.get(editingSourceInfo["source_name"])
            # if LEGOizer_storage scene is not active, set to active
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
            source.rotation_euler = Euler(tuple(source["previous_rotation"], "XYZ"))
            source.scale = source["previous_scale"]
            setOriginToObjOrigin(toObj=source, fromLoc=source["before_origin_set_location"])
            if bpy.context.scene.name == "LEGOizer_storage (DO NOT RENAME)":
                for screen in bpy.data.screens:
                    screen.scene = bpy.data.scenes.get(bpy.props.origScene)
            bpy.props.commitEdits = False
            bpy.context.window_manager["editingSourceInStorage"] = False
            redraw_areas("VIEW_3D")
            scn.update()

bpy.app.handlers.save_pre.append(handle_saving_in_edit_mode)
