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
from mathutils import Vector, Quaternion

# Bricker imports
from .common import confirmList
from .general import *


def storeTransformData(cm, obj, offsetBy=None):
    """ store transform data from obj into cm.modelLoc/Rot/Scale """
    if obj:
        loc = obj.location
        if offsetBy is not None:
            loc += Vector(offsetBy)
        cm.modelLoc = listToStr(loc.to_tuple())
        # cm.modelLoc = listToStr(obj.matrix_world.to_translation().to_tuple())
        lastMode = obj.rotation_mode
        obj.rotation_mode = "QUATERNION"
        cm.modelRot = listToStr(tuple(obj.rotation_quaternion))
        cm.modelScale = listToStr(obj.scale.to_tuple())
        obj.rotation_mode = lastMode
    elif obj is None:
        cm.modelLoc = "0,0,0"
        cm.modelRot = "1,0,0,0"
        cm.modelScale = "1,1,1"


def getTransformData(cm):
    """ return transform data from cm.modelLoc/Rot/Scale """
    l = tuple(strToList(cm.modelLoc, float))
    r = tuple(strToList(cm.modelRot, float))
    s = tuple(strToList(cm.modelScale, float))
    return l, r, s


def clearTransformData(cm):
    cm.modelLoc = "0,0,0"
    cm.modelRot = "1,0,0,0"
    cm.modelScale = "1,1,1"


def applyTransformData(cm, objList):
    """ apply transform data from cm.modelLoc/Rot/Scale to objects in objList """
    objList = confirmList(objList)
    # apply matrix to objs
    for obj in objList:
        # LOCATION
        l, r, s = getTransformData(cm)
        obj.location = obj.location + Vector(l)
        # ROTATION
        lastMode = obj.rotation_mode
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion.rotate(Quaternion(r))
        obj.rotation_mode = lastMode
        # SCALE
        osx, osy, osz = obj.scale
        obj.scale = (osx * s[0],
                     osy * s[1],
                     osz * s[2])
