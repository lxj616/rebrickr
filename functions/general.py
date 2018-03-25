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
from mathutils import Vector, Euler, Matrix

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
    returns object details with the following subattribute Vectors:

    .max : maximum value of object
    .min : minimum value of object
    .mid : midpoint value of object
    .dist: distance min to max

    """

    local_coords = obj.bound_box[:]
    om = obj.matrix_world

    if not local:
        worldify = lambda p: om * Vector(p[:])
        coords = [worldify(p).to_tuple() for p in local_coords]
    else:
        coords = [p[:] for p in local_coords]

    rotated = zip(*coords[::-1])
    getMax = lambda i: max([co[i] for co in coords])
    getMin = lambda i: min([co[i] for co in coords])

    info = lambda: None
    info.max = Vector((getMax(0), getMax(1), getMax(2)))
    info.min = Vector((getMin(0), getMin(1), getMin(2)))
    info.mid = (info.min + info.max) / 2
    info.dist = info.max - info.min

    return info


def setOriginToObjOrigin(toObj, fromObj=None, fromLoc=None, deleteFromObj=False):
    assert fromObj or fromLoc
    scn = bpy.context.scene
    oldCursorLocation = tuple(scn.cursor_location)
    unlinkToo = False
    if fromObj:
        scn.cursor_location = fromObj.matrix_world.to_translation().to_tuple()
    else:
        scn.cursor_location = fromLoc
    setActiveObj(toObj)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    scn.cursor_location = oldCursorLocation
    if fromObj:
        if deleteFromObj:
            m = fromObj.data
            bpy.data.objects.remove(fromObj, True)
            bpy.data.meshes.remove(m)


def getBricks(cm=None, typ=None):
    """ get bricks in 'cm' model """
    cm = cm or getActiveContextInfo()[1]
    typ = typ or ("MODEL" if cm.modelCreated else "ANIM")
    n = cm.source_name
    if typ == "MODEL":
        gn = "Bricker_%(n)s_bricks" % locals()
        bGroup = bpy.data.groups[gn]
        bricks = list(bGroup.objects)
    elif typ == "ANIM":
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
    assert type(lst) in [list, tuple, Vector]
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
    parent_key = key if bricksDict[key]["parent"] in ["self", None] else bricksDict[key]["parent"]
    return parent_key


def createdWithUnsupportedVersion(cm=None):
    cm = cm or getActiveContextInfo()[1]
    return cm.version[:3] != bpy.props.bricker_version[:3]


def getLocsInBrick(size, key, loc=None, zStep=None):
    zStep = zStep or getZStep(getActiveContextInfo()[1])
    x0, y0, z0 = loc or strToList(key)
    return [[x0 + x, y0 + y, z0 + z] for z in range(0, size[2], zStep) for y in range(size[1]) for x in range(size[0])]


def getKeysInBrick(size, key, loc=None, zStep=None):
    locs = getLocsInBrick(size=size, key=key, loc=loc, zStep=zStep)
    return [listToStr(loc) for loc in locs]


def isOnShell(bricksDict, key, loc=None):
    """ check if any locations in brick are on the shell """
    size = bricksDict[key]["size"]
    brickKeys = getKeysInBrick(size=size, key=key, loc=loc)
    return bricksDict[key]["val"] == 1 or 1 in [bricksDict[k]["val"] for k in brickKeys]


def getDictKey(name):
    """ get dict key details of obj """
    dictKey = name.split("__")[1]
    dictLoc = strToList(dictKey)
    return dictKey, dictLoc


def getBrickCenter(bricksDict, key, loc=None):
    brickKeys = getKeysInBrick(size=bricksDict[key]["size"], key=key, loc=loc)
    coords = [strToList(bricksDict[k0]["co"], item_type=float) for k0 in brickKeys]
    coord_ave = Vector((np.mean([co[0] for co in coords]), np.mean([co[1] for co in coords]), np.mean([co[2] for co in coords])))
    return coord_ave


def getNormalDirection(normal, maxDist=0.77):
    # initialize vars
    minDist = maxDist
    minDir = None
    # skip normals that aren't within 0.3 of the z values
    if normal is None or ((normal.z > -0.2 and normal.z < 0.2) or normal.z > 0.8 or normal.z < -0.8):
        return minDir
    # set Vectors for perfect normal directions
    normDirs = {"^X+":Vector((1, 0, 0.5)),
                "^Y+":Vector((0, 1, 0.5)),
                "^X-":Vector((-1, 0, 0.5)),
                "^Y-":Vector((0, -1, 0.5)),
                "vX+":Vector((1, 0, -0.5)),
                "vY+":Vector((0, 1, -0.5)),
                "vX-":Vector((-1, 0, -0.5)),
                "vY-":Vector((0, -1, -0.5))}
    # calculate nearest
    for dir,v in normDirs.items():
        dist = (v - normal).length
        if dist < minDist:
            minDist = dist
            minDir = dir
    return minDir


def get_override(area_type, region_type):
    for area in bpy.context.screen.areas:
        if area.type == area_type:
            for region in area.regions:
                if region.type == region_type:
                    override = {'area': area, 'region': region}
                    return override
    #error message if the area or region wasn't found
    raise RuntimeError("Wasn't able to find", region_type," in area ", area_type,
                        "\n Make sure it's open while executing script.")


def setPivotPoint(pivot_point='CURSOR'):
    scr = bpy.context.window.screen
    v3d = [area for area in scr.areas if area.type == 'VIEW_3D'][0]
    v3d.spaces[0].pivot_point = pivot_point


def getExportPath(fn, ext):
    cm = getActiveContextInfo()[1]
    fullPath = cm.exportPath
    lastSlash = fullPath.rfind("/")
    # setup the render dump folder based on user input
    if fullPath.startswith("//"):
        fullPath = os.path.join(bpy.path.abspath("//"), fullPath[2:])
    path = fullPath[:len(fullPath) if lastSlash == -1 else lastSlash + 1]
    fn0 = "" if lastSlash == -1 else fullPath[lastSlash + 1:len(fullPath)]
    # if no user input, use default render location
    if path == "":
        path = bpy.path.abspath("//") or "/tmp/"
    # check to make sure dumpLoc exists on local machine
    if not os.path.exists(path):
        os.mkdir(path)
    # create full path from path and filename
    fullPath = os.path.join(path, (fn if fn0 == "" else fn0) + ext)
    return fullPath
