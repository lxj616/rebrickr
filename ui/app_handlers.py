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

@persistent
def handle_animation(scene):
    scn = scene
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
                        # prevent bricks from being selected on frame change
                        if brick.select:
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
    # if scn.layers changes and active object is no longer visible, set scn.cmlist_index to -1
    if scn.last_layers != str(list(scn.layers)):
        scn.last_layers = str(list(scn.layers))
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
    elif scn.last_cmlist_index != scn.cmlist_index and scn.cmlist_index != -1:
        scn.last_cmlist_index = scn.cmlist_index
        cm = scn.cmlist[scn.cmlist_index]
        obj = bpy.data.objects.get(cm.source_name)
        if obj is None:
            obj = bpy.data.objects.get(cm.source_name + " (DO NOT RENAME)")
        if obj is not None:
            if cm.modelCreated:
                n = cm.source_name
                gn = "LEGOizer_%(n)s_bricks" % locals()
                print(gn, "MODEL")
                if groupExists(gn) and len(bpy.data.groups[gn].objects) > 0:
                    select(list(bpy.data.groups[gn].objects), active=bpy.data.groups[gn].objects[0])
                    scn.last_active_object_name = scn.objects.active.name
            elif cm.animated:
                n = cm.source_name
                cf = scn.frame_current
                if cf > cm.stopFrame:
                    cf = cm.stopFrame
                elif cf < cm.startFrame:
                    cf = cm.startFrame
                gn = "LEGOizer_%(n)s_bricks_frame_%(cf)s" % locals()
                print(gn, "ANIM")
                if len(bpy.data.groups[gn].objects) > 0:
                    select(list(bpy.data.groups[gn].objects), active=bpy.data.groups[gn].objects[0])
                    scn.last_active_object_name = scn.objects.active.name
            else:
                select(obj, active=obj)
            scn.last_active_object_name = obj.name
        else:
            for i in range(len(scn.cmlist)):
                cm = scn.cmlist[i]
                if cm.source_name == scn.active_object_name:
                    select(None)
                    break
    # open LEGO model settings for active object if active object changes
    elif scn.objects.active and scn.last_active_object_name != scn.objects.active.name and ( scn.cmlist_index == -1 or scn.cmlist[scn.cmlist_index].source_name != "") and scn.objects.active.type == "MESH":
        scn.last_active_object_name = scn.objects.active.name
        if scn.objects.active.name.startswith("LEGOizer_"):
            if "_bricks" in scn.objects.active.name:
                frameLoc = scn.objects.active.name.rfind("_bricks")
            elif "_brick_" in scn.objects.active.name:
                frameLoc = scn.objects.active.name.rfind("_brick_")
            else:
                frameLoc = None
            if frameLoc is not None:
                scn.active_object_name = scn.objects.active.name[9:frameLoc]
        else:
            scn.active_object_name = scn.objects.active.name
        for i in range(len(scn.cmlist)):
            cm = scn.cmlist[i]
            if cm.source_name == scn.active_object_name:
                scn.cmlist_index = i
                scn.last_cmlist_index = scn.cmlist_index
                return
        scn.cmlist_index = -1
    # keep isWaterTight updated
    if scn.cmlist_index != -1:
        cm = scn.cmlist[scn.cmlist_index]
        obj = bpy.data.objects.get(cm.source_name)
        if obj is not None and (len(obj.data.vertices) != cm.objVerts or len(obj.data.polygons) != cm.objPolys or len(obj.data.edges) != cm.objEdges):
            cm.objVerts = len(obj.data.vertices)
            cm.objPolys = len(obj.data.polygons)
            cm.objEdges = len(obj.data.edges)
            cm.isWaterTight = cm.objVerts + cm.objPolys - cm.objEdges == 2

bpy.app.handlers.scene_update_pre.append(handle_selections)
