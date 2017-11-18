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
from mathutils import Vector, Euler

# Rebrickr imports
from .common import confirmList
from .general import *

def storeTransformData(obj):
    """ store transform data from obj into cm.modelLoc/Rot/Scale """
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    if obj is not None:
        cm.modelLoc = listToStr(obj.location.to_tuple())
        # cm.modelLoc = listToStr(obj.matrix_world.to_translation().to_tuple())
        obj.rotation_mode = "XYZ"
        cm.modelRot = listToStr(tuple(obj.rotation_euler))
        cm.modelScale = listToStr(obj.scale.to_tuple())
    elif obj is None:
        cm.modelLoc = "0,0,0"
        cm.modelRot = "0,0,0"
        cm.modelScale = "1,1,1"

def setTransformData(objList, source=None, skipLocation=False, skipRotation=False, skipScale=False):
    """ apply transform data from cm.modelLoc/Rot/Scale to objects in objList """
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
        if not skipRotation:
            obj.rotation_mode = "XYZ"
            obj.rotation_euler.rotate(Euler(tuple(r), "XYZ"))
            if source is not None:
                obj.rotation_euler.rotate(source.rotation_euler.to_matrix().inverted())
                obj.rotation_euler.rotate(Euler(tuple(source["previous_rotation"]), "XYZ"))
        if not skipScale:
            osx,osy,osz = obj.scale
            obj.scale = (osx * s[0],
                         osy * s[1],
                         osz * s[2])
            if source is not None:
                obj.scale -= Vector(source.scale) - Vector(source["previous_scale"])

def getTransformData():
    """ return transform data from cm.modelLoc/Rot/Scale """
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    l = tuple(strToList(cm.modelLoc, float))
    r = tuple(strToList(cm.modelRot, float))
    s = tuple(strToList(cm.modelScale, float))
    return l,r,s

def setSourceTransform(source, obj=None, objParent=None, last_origin_obj=None, skipLocation=False):
    """ set source transform data relative to obj, parent, and/or last_origin_obj """
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
    ssx,ssy,ssz = source.scale
    osx,osy,osz = objScale
    opsx,opsy,opsz = objParentScale
    source.scale = (ssx * osx * opsx,
                    ssy * osy * opsy,
                    ssz * osz * opsz)
