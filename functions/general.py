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
import collections
import json

# Blender imports
import bpy
from mathutils import Vector, Euler

# Rebrickr imports
from .common import *

def getSafeScn():
    safeScn = bpy.data.scenes.get("Rebrickr_storage (DO NOT RENAME)")
    if safeScn == None:
        safeScn = bpy.data.scenes.new("Rebrickr_storage (DO NOT RENAME)")
    return safeScn
def safeUnlink(obj, hide=True, protect=True):
    scn = bpy.context.scene
    safeScn = getSafeScn()
    scn.objects.unlink(obj)
    safeScn.objects.link(obj)
    obj.protected = protect
    if hide:
        obj.hide = True
def safeLink(obj, unhide=False, protect=False):
    scn = bpy.context.scene
    safeScn = getSafeScn()
    scn.objects.link(obj)
    obj.protected = protect
    if unhide:
        obj.hide = False
    try:
        safeScn.objects.unlink(obj)
    except RuntimeError:
        pass

def setLayers(scn, layers):
    """ set active layers of scn w/o 'dag ZERO' error """
    assert len(layers) == 20
    # set active scene for all screens (prevents dag ZERO errors)
    for screen in bpy.data.screens:
        screen.scene = scn
    # set active layers of scn
    scn.layers = layers

def bounds(obj, local=False):
    """
    returns object details with the following subattributes for x (same for y & z):

    .x.max : maximum 'x' value of object
    .x.min : minimum 'x' value of object
    .x.mid : midpoint 'x' value of object
    .x.dist: distance 'x' min to 'x' max

    """

    local_coords = obj.bound_box[:]
    om = obj.matrix_world

    if not local:
        worldify = lambda p: om * Vector(p[:])
        coords = [worldify(p).to_tuple() for p in local_coords]
    else:
        coords = [p[:] for p in local_coords]

    rotated = zip(*coords[::-1])

    push_axis = []
    for (axis, _list) in zip('xyz', rotated):
        info = lambda: None
        info.max = max(_list)
        info.min = min(_list)
        info.mid = (info.min + info.max) / 2
        info.dist = info.max - info.min
        push_axis.append(info)

    originals = dict(zip(['x', 'y', 'z'], push_axis))

    o_details = collections.namedtuple('object_details', 'x y z')
    return o_details(**originals)

def setOriginToObjOrigin(toObj, fromObj=None, fromLoc=None, deleteFromObj=False):
    assert fromObj is not None or fromLoc is not None
    scn = bpy.context.scene
    oldCursorLocation = tuple(scn.cursor_location)
    unlinkToo = False
    if fromObj is not None:
        scn.cursor_location = fromObj.matrix_world.to_translation().to_tuple()
    elif fromLoc is not None:
        scn.cursor_location = fromLoc
    select(toObj, active=toObj)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    scn.cursor_location = oldCursorLocation
    if fromObj is not None:
        if deleteFromObj:
            m = fromObj.data
            bpy.data.objects.remove(fromObj, True)
            bpy.data.meshes.remove(m)

def getBricks(cm=None):
    """ get bricks in 'cm' model """
    if cm is None:
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
    bricks = []
    n = cm.source_name
    if cm.modelCreated:
        gn = "Rebrickr_%(n)s_bricks" % locals()
        bGroup = bpy.data.groups.get(gn)
        if bGroup is not None:
            bricks = list(bGroup.objects)
    elif cm.animated:
        for cf in range(cm.lastStartFrame, cm.lastStopFrame+1):
            gn = "Rebrickr_%(n)s_bricks_frame_%(cf)s" % locals()
            bGroup = bpy.data.groups.get(gn)
            if bGroup is not None:
                bricks += list(bGroup.objects)
    return bricks

def getMatrixSettings(cm=None):
    if cm is None:
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
    return listToStr([cm.brickHeight, cm.gap, cm.brickType, cm.distOffsetX, cm.distOffsetY, cm.distOffsetZ, cm.customObjectName, cm.useNormals, cm.verifyExposure, cm.insidenessRayCastDir, cm.castDoubleCheckRays, cm.brickShell, cm.calculationAxes])

def revertMatrixSettings(cm=None):
    if cm is None:
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
    settings = cm.lastMatrixSettings.split(",")
    cm.brickHeight = float(settings[0])
    cm.gap = float(settings[1])
    cm.brickType = settings[2]
    cm.distOffsetX = float(settings[3])
    cm.distOffsetY = float(settings[4])
    cm.distOffsetZ = float(settings[5])
    cm.customObjectName = settings[6]
    cm.useNormals = str_to_bool(settings[7])
    cm.verifyExposure = str_to_bool(settings[8])
    cm.insidenessRayCastDir = settings[9]
    cm.castDoubleCheckRays = str_to_bool(settings[10])
    cm.brickShell = settings[11]
    cm.calculationAxes = settings[12]
    cm.matrixIsDirty = False

def matrixReallyIsDirty(cm):
    return cm.matrixIsDirty and cm.lastMatrixSettings != getMatrixSettings()

def listToStr(lst):
    assert type(lst) in [list, tuple]
    string = str(lst[0])
    for i in range(1, len(lst)):
        item = lst[i]
        string = "%(string)s,%(item)s" % locals()
    return string
def strToList(string, item_type=int, split_on=","):
    lst = string.split(split_on)
    assert type(string) is str and type(split_on) is str
    lst = list(map(item_type, lst))
    return lst
def strToTuple(string, item_type=int, split_on=","):
    tup = tuple(strToList(string, item_type, split_on))
    return tup

def getZStep(cm):
    return 3 if cm.brickType in ["Bricks", "Custom"] else 1

def getAction(cm):
    """ returns action """
    if cm.modelCreated:
        action = "UPDATE_MODEL"
    elif cm.animated:
        action = "UPDATE_ANIM"
    elif not cm.useAnimation:
        action = "CREATE"
    else:
        action = "ANIMATE"
    return action
