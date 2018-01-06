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
from mathutils.interpolate import poly_3d_calc
import math

# Blender imports
import bpy

# Rebrickr imports
from ...functions import *
from ..Brick import Bricks


def getUVCoord(mesh, face, point, image):
    # get active uv layer data
    uv_layer = mesh.uv_layers.active
    if uv_layer is None:
        return None
    uv = uv_layer.data
    # get 3D coordinates of face's vertices
    lco = [mesh.vertices[i].co for i in face.vertices]
    # get uv coordinates of face's vertices
    luv = [uv[i].uv for i in face.loop_indices]
    # calculate barycentric weights for point
    lwts = poly_3d_calc(lco, point)
    # multiply barycentric weights by uv coordinates
    uv_loc = sum((p*w for p,w in zip(luv,lwts)), Vector((0,0)))
    # convert uv_loc in range(0,1) to uv coordinate
    uv_coord = (uv_loc.x * image.size[0], uv_loc.y * image.size[1])

    # return resulting uv coordinate
    return Vector(uv_coord)


def getPixel(image, uv_coord):
    rgba = []
    for i in range(4):
        # formula from 'TrumanBlending' at https://blenderartists.org/forum/archive/index.php/t-195230.html
        pixel_idx = (4 * (uv_coord.x + (image.size[0] * uv_coord.y))) + i
        rgba.append(image.pixels[math.floor(pixel_idx)])
    return rgba


def getClosestMaterial(source, face_idx, point):
    """ sets all matNames in bricksDict based on nearest_face """
    if face_idx is None:
        return ""
    face = source.data.polygons[face_idx]
    matName = ""
    if source.data.uv_layers.active is None and len(source.material_slots) > 0:
        slot = source.material_slots[f.material_index]
        mat = slot.material
        matName = mat.name if mat is not None else ""
    elif source.data.uv_layers.active is not None:
        # get uv_texture image for face
        image = source.data.uv_textures.active.data.values()[face_idx].image
        # get uv coordinate based on nearest face intersection
        uv_coord = getUVCoord(source.data, face, point, image)
        # retrieve rgba value at uv coordinate
        rgba = getPixel(image, uv_coord))

        # pick material based on rgba value
        if rgba[2] > 0.5:
            matName = "white"
        else:
            matName = "black"

    return matName


def getDictKey(name):
    """ get dict key details of obj """
    dictKey = name.split("__")[1]
    dictLoc = strToList(dictKey)
    return dictKey, dictLoc


def getDetailsAndBounds(source, skipDimensions=False):
    scn, cm, _ = getActiveContextInfo()
    # get dimensions and bounds
    source_details = bounds(source)
    if not skipDimensions:
        zStep = getZStep(cm)
        dimensions = Bricks.get_dimensions(cm.brickHeight, zStep/3, cm.gap)
        return source_details, dimensions
    else:
        return source_details


def getArgumentsForBricksDict(cm, source=None, source_details=None, dimensions=None):
    if source is None:
        source = bpy.data.objects.get(cm.source_name)
        if source is None: source = bpy.data.objects.get(cm.source_name + " (DO NOT RENAME)")
    if source_details is None or dimensions is None:
        source_details, dimensions = getDetailsAndBounds(source)
    if cm.brickType == "Custom":
        scn = bpy.context.scene
        customObj = bpy.data.objects[cm.customObjectName]
        oldLayers = list(scn.layers) # store scene layers for later reset
        setLayers(scn, customObj.layers)
        select(customObj, active=customObj)
        bpy.ops.object.duplicate()
        customObj0 = scn.objects.active
        select(customObj0, active=customObj0)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        customObj_details = bounds(customObj0)
        customData = customObj0.data
        bpy.data.objects.remove(customObj0, True)
        scale = cm.brickHeight/customObj_details.z.dist
        R = (scale * customObj_details.x.dist + dimensions["gap"],
             scale * customObj_details.y.dist + dimensions["gap"],
             scale * customObj_details.z.dist + dimensions["gap"])
        setLayers(scn, oldLayers)
    else:
        customData = None
        customObj_details = None
        R = (dimensions["width"] + dimensions["gap"],
             dimensions["width"] + dimensions["gap"],
             dimensions["height"]+ dimensions["gap"])
    return source, source_details, dimensions, R, customData, customObj_details
