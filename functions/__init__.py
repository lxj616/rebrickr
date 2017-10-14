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
import bmesh
import math
import time
from copy import copy, deepcopy

# Blender imports
import bpy
from mathutils import Matrix, Vector, geometry, Euler
props = bpy.props

# Rebrickr imports
from .common_functions import *
from .generate_lattice import generateLattice
from .makeBricks import *
from .makeBricksDict import *
from .wrappers import *
from .hashObject import *
from ..lib.Brick import Bricks

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
    except:
        pass

def confirmList(objList):
    """ if single object passed, convert to list """
    if type(objList) != list:
        objList = [objList]
    return objList

def bounds(obj, local=False):

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
        info.distance = info.max - info.min
        push_axis.append(info)

    import collections

    originals = dict(zip(['x', 'y', 'z'], push_axis))

    o_details = collections.namedtuple('object_details', 'x y z')
    return o_details(**originals)

def importLogo():
    """ import logo object from Rebrickr addon folder """
    addonsPath = bpy.utils.user_resource('SCRIPTS', "addons")
    Rebrickr = props.rebrickr_module_name
    logoObjPath = "%(addonsPath)s/%(Rebrickr)s/lego_logo.obj" % locals()
    bpy.ops.import_scene.obj(filepath=logoObjPath)
    logoObj = bpy.context.selected_objects[0]
    return logoObj

def getClosestPolyIndex(point,maxLen,ob):
    """ returns nearest polygon to point within edgeLen """
    # initialize variables
    shortestLen = maxLen
    closestPolyIdx = None
    # run initial intersection check
    for direction in [(1,0,0), (0,1,0), (0,0,1), (-1,0,0), (0,-1,0), (0,0,-1)]:
        _,location,normal,index = ob.ray_cast(point,direction)#,distance=edgeLen*1.00000000001)
        if index == -1: continue
        nextLen = (Vector(point) - Vector(location)).length
        if nextLen < shortestLen:
            shortestLen = nextLen
            closestPolyIdx = index
    # return helpful information
    return closestPolyIdx

def setOriginToObjOrigin(toObj, fromObj=None, fromLoc=None, deleteFromObj=False):
    scn = bpy.context.scene
    oldCursorLocation = tuple(scn.cursor_location)
    unlinkToo = False
    if fromObj is not None:
        scn.cursor_location = fromObj.matrix_world.to_translation().to_tuple()
    elif fromLoc is not None:
        scn.cursor_location = fromLoc
    else:
        print("ERROR in 'setOriginToObjOrigin': fromObj and fromLoc are both None")
        return
    select(toObj, active=toObj)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    scn.cursor_location = oldCursorLocation
    if fromObj is not None:
        if deleteFromObj:
            m = fromObj.data
            bpy.data.objects.remove(fromObj, True)
            bpy.data.meshes.remove(m)

def storeTransformData(obj):
    """ store location, rotation, and scale data for model """
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    if obj is not None:
        cm.modelLoc = str(obj.location.to_tuple())[1:-1]
        obj.rotation_mode = "XYZ"
        cm.modelRot = str(tuple(obj.rotation_euler))[1:-1]
        cm.modelScale = str(obj.scale.to_tuple())[1:-1]
    elif obj is None:
        cm.modelLoc = "0,0,0"
        cm.modelRot = "0,0,0"
        cm.modelScale = "1,1,1"

def convertToFloats(lst):
    for i in range(len(lst)):
        lst[i] = float(lst[i])
    return lst

def setTransformData(objList, source=None, skipLocation=False):
    """ set location, rotation, and scale data for model """
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    objList = confirmList(objList)
    for obj in objList:
        l,r,s = getTransformData()
        if not skipLocation:
            obj.location = obj.location + Vector(l)
            if source is not None:
                n = cm.source_name
                Rebrickr_last_origin_on = "Rebrickr_%(n)s_last_origin" % locals()
                last_origin_obj = bpy.data.objects.get(Rebrickr_last_origin_on)
                if last_origin_obj is not None:
                    obj.location -= Vector(last_origin_obj.location) - Vector(source["previous_location"])
                else:
                    obj.location -= Vector(source.location) - Vector(source["previous_location"])
        obj.rotation_mode = "XYZ"
        obj.rotation_euler.rotate(Euler(tuple(r), "XYZ"))
        if source is not None:
            obj.rotation_euler.rotate(source.rotation_euler.to_matrix().inverted())
            obj.rotation_euler.rotate(Euler(tuple(source["previous_rotation"]), "XYZ"))
        obj.scale = (obj.scale[0] * s[0], obj.scale[1] * s[1], obj.scale[2] * s[2])
        if source is not None:
            obj.scale -= Vector(source.scale) - Vector(source["previous_scale"])

def getTransformData():
    """ set location, rotation, and scale data for model """
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    l = tuple(convertToFloats(cm.modelLoc.split(",")))
    r = tuple(convertToFloats(cm.modelRot.split(",")))
    s = tuple(convertToFloats(cm.modelScale.split(",")))
    return l,r,s

def setSourceTransform(source, obj=None, objParent=None, last_origin_obj=None, skipLocation=False):
    if obj is not None:
        objLoc = obj.location
        obj.rotation_mode = "XYZ"
        objRot = obj.rotation_euler
        objScale = obj.scale
    else:
        objLoc = Vector((0,0,0))
        objRot = Euler((0,0,0), "XYZ")
        objScale = Vector((1,1,1))
    if objParent is not None:
        objParentLoc = objParent.location
        objParentRot = objParent.rotation_euler
        objParentScale = objParent.scale
    else:
        objParentLoc = Vector((0,0,0))
        objParentRot = Euler((0,0,0), "XYZ")
        objParentScale = Vector((1,1,1))
    if not skipLocation:
        if last_origin_obj is not None:
            source.location = objParentLoc + objLoc - (Vector(last_origin_obj.location) - Vector(source["previous_location"]))
        else:
            source.location = objParentLoc + objLoc
    source.rotation_mode = "XYZ"
    source.rotation_euler.rotate(objRot)
    source.rotation_euler.rotate(objParentRot)
    source.scale = (source.scale[0] * objScale[0] * objParentScale[0], source.scale[1] * objScale[1] * objParentScale[1], source.scale[2] * objScale[2] * objParentScale[2])
