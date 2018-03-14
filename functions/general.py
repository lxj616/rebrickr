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
import math
import numpy as np

# Blender imports
import bpy
from mathutils import Vector, Euler

# Bricker imports
from .common import *


def getSafeScn():
    safeScn = bpy.data.scenes.get("Bricker_storage (DO NOT RENAME)")
    if safeScn == None:
        safeScn = bpy.data.scenes.new("Bricker_storage (DO NOT RENAME)")
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
    assert fromObj or fromLoc
    scn = bpy.context.scene
    oldCursorLocation = tuple(scn.cursor_location)
    unlinkToo = False
    if fromObj:
        scn.cursor_location = fromObj.matrix_world.to_translation().to_tuple()
    else:
        scn.cursor_location = fromLoc
    select(toObj, active=toObj)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    scn.cursor_location = oldCursorLocation
    if fromObj:
        if deleteFromObj:
            m = fromObj.data
            bpy.data.objects.remove(fromObj, True)
            bpy.data.meshes.remove(m)


def getBricks(cm=None):
    """ get bricks in 'cm' model """
    cm = cm or getActiveContextInfo()[1]
    n = cm.source_name
    if cm.modelCreated:
        gn = "Bricker_%(n)s_bricks" % locals()
        bGroup = bpy.data.groups.get(gn)
        if bGroup:
            bricks = list(bGroup.objects)
    elif cm.animated:
        bricks = []
        for cf in range(cm.lastStartFrame, cm.lastStopFrame+1):
            gn = "Bricker_%(n)s_bricks_frame_%(cf)s" % locals()
            bGroup = bpy.data.groups.get(gn)
            if bGroup:
                bricks += list(bGroup.objects)
    return bricks


def brick_materials_installed():
    scn = bpy.context.scene
    return hasattr(scn, "isBrickMaterialsInstalled") and scn.isBrickMaterialsInstalled


def brick_materials_loaded():
    scn = bpy.context.scene
    # make sure abs_plastic_materials addon is installed
    brick_mats_installed = hasattr(scn, "isBrickMaterialsInstalled") and scn.isBrickMaterialsInstalled
    if not brick_mats_installed:
        return False
    # check if any of the colors haven't been loaded
    mats = bpy.data.materials.keys()
    for color in bpy.props.abs_plastic_materials:
        if color not in mats:
            return False
    return True


def getMatrixSettings(cm=None):
    cm = cm or getActiveContextInfo()[1]
    return listToStr([cm.brickHeight, cm.gap, cm.brickType, cm.distOffsetX, cm.distOffsetY, cm.distOffsetZ, cm.customObjectName, cm.useNormals, cm.verifyExposure, cm.insidenessRayCastDir, cm.castDoubleCheckRays, cm.brickShell, cm.calculationAxes])


def matrixReallyIsDirty(cm):
    return cm.matrixIsDirty and cm.lastMatrixSettings != getMatrixSettings()


def listToStr(lst, separate_by=","):
    assert type(lst) in [list, tuple]
    string = str(lst[0])
    for i in range(1, len(lst)):
        item = lst[i]
        string = "%(string)s%(separate_by)s%(item)s" % locals()
    return string


def strToList(string, item_type=int, split_on=","):
    lst = string.split(split_on)
    assert type(string) is str and type(split_on) is str
    lst = list(map(item_type, lst))
    return lst


def strToTuple(string, item_type=int, split_on=","):
    tup = tuple(strToList(string, item_type, split_on))
    return tup


def isUnique(lst):
    return np.unique(lst).size == len(lst)


def getZStep(cm):
    return 3 if cm.brickType in ["BRICKS", "CUSTOM"] else 1


def gammaCorrect(rgba, val):
    r, g, b, a = rgba
    r = math.pow(r, val)
    g = math.pow(g, val)
    b = math.pow(b, val)
    return [r, g, b, a]


def getParentKey(bricksDict, key):
    if key not in bricksDict:
        return None
    parent_key = key if bricksDict[key]["parent_brick"] in ["self", None] else bricksDict[key]["parent_brick"]
    return parent_key


def createdWithUnsupportedVersion(cm=None):
    cm = cm or getActiveContextInfo()[1]
    return cm.version[:3] != bpy.props.bricker_version[:3]


def getLocsInBrick(size, key, loc=None):
    cm = getActiveContextInfo()[1]
    x0, y0, z0 = loc or strToList(key)
    return [[x0 + x, y0 + y, z0 + z] for z in range(0, size[2], getZStep(cm)) for y in range(size[1]) for x in range(size[0])]


def getKeysInBrick(size, key, loc=None):
    locs = getLocsInBrick(size=size, key=key, loc=loc)
    return [listToStr(loc) for loc in locs]


def isOnShell(bricksDict, key, loc=None):
    """ check if any locations in brick are on the shell """
    size = bricksDict[key]["size"]
    brickKeys = getKeysInBrick(size=size, key=key, loc=loc)
    return bricksDict[key]["val"] == 1 or 1 in [bricksDict[k]["val"] for k in brickKeys]


def getExportPath(fn, ext):
    cm = getActiveContextInfo()[1]
    fullPath = cm.exportPath
    lastSlash = fullPath.rfind("/")
    path = fullPath[:len(fullPath) if lastSlash == -1 else lastSlash]
    fn0 = "" if lastSlash == -1 else fullPath[lastSlash + 1:len(fullPath)]
    # setup the render dump folder based on user input
    if path.startswith("//"):
        path = os.path.join(bpy.path.abspath("//"), path[2:])
    # if no user input, use default render location
    elif path == "":
        path = bpy.path.abspath("//")
    # check to make sure dumpLoc exists on local machine
    if not os.path.exists(path):
        os.mkdir(path)
    # create full path from path and filename
    fullPath = os.path.join(path, (fn if fn0 == "" else fn0) + ext)
    return fullPath
