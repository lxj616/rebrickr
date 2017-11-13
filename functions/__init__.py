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

# Blender imports
import bpy
from mathutils import Vector, Euler

# Rebrickr imports
from .common_functions import *
from .generate_lattice import generateLattice
from .makeBricks import *
from .makeBricksDict import *
from .modifyBricksDict import *
from .wrappers import *
from .hashObject import *
from .transformData import *
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
    except RuntimeError:
        pass

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

    originals = dict(zip(['x', 'y', 'z'], push_axis))

    o_details = collections.namedtuple('object_details', 'x y z')
    return o_details(**originals)

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
