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
from .common_functions import confirmList

def storeTransformData(obj):
    """ store transform data from obj into cm.modelLoc/Rot/Scale """
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    if obj is not None:
        cm.modelLoc = str(obj.location.to_tuple())[1:-1]
        # cm.modelLoc = str(obj.matrix_world.to_translation().to_tuple())[1:-1]
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
            obj.scale = (obj.scale[0] * s[0], obj.scale[1] * s[1], obj.scale[2] * s[2])
            if source is not None:
                obj.scale -= Vector(source.scale) - Vector(source["previous_scale"])

def getTransformData():
    """ return transform data from cm.modelLoc/Rot/Scale """
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    l = tuple(convertToFloats(cm.modelLoc.split(",")))
    r = tuple(convertToFloats(cm.modelRot.split(",")))
    s = tuple(convertToFloats(cm.modelScale.split(",")))
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
    source.scale = (source.scale[0] * objScale[0] * objParentScale[0], source.scale[1] * objScale[1] * objParentScale[1], source.scale[2] * objScale[2] * objParentScale[2])
