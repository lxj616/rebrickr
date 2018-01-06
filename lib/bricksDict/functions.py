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
    image_size_x, image_size_y = image.size
    x_co = round(uv_loc.x * (image_size_x - 1))
    y_co = round(uv_loc.y * (image_size_y - 1))
    uv_coord = (x_co, y_co)

    # return resulting uv coordinate
    return Vector(uv_coord)


# reference: https://svn.blender.org/svnroot/bf-extensions/trunk/py/scripts/addons/uv_bake_texture_to_vcols.py
def getUVImages(obj):
    uv_images = {}
    for uv_tex in obj.data.uv_textures.active.data:
        if not uv_tex.image or uv_tex.image.name in uv_images or not uv_tex.image.pixels:
            continue
        uv_images[uv_tex.image.name] = (uv_tex.image.size[0],
                                        uv_tex.image.size[1],
                                        uv_tex.image.pixels[:]
                                        # Accessing pixels directly is far too slow.
                                        # Copied to new array for massive performance-gain.
                                       )
    return uv_images


# reference: https://svn.blender.org/svnroot/bf-extensions/trunk/py/scripts/addons/uv_bake_texture_to_vcols.py
def getPixel(image, uv_coord, uv_images):
    rgba = []

    image_size_x, image_size_y, uv_pixels = uv_images[image.name]
    pixelNumber = (image_size_x * int(uv_coord.y)) + int(uv_coord.x)
    r = uv_pixels[pixelNumber*4 + 0]
    g = uv_pixels[pixelNumber*4 + 1]
    b = uv_pixels[pixelNumber*4 + 2]
    a = uv_pixels[pixelNumber*4 + 3]
    return (r, g, b, a)


def getClosestMaterial(obj, face_idx, point, uv_images):
    """ sets all matNames in bricksDict based on nearest_face """
    scn, cm, _ = getActiveContextInfo()
    if face_idx is None:
        return ""
    face = obj.data.polygons[face_idx]
    matName = ""
    # get closest material using UV map
    if cm.useUVMap and obj.data.uv_layers.active is not None:
        # get uv_texture for face
        image = obj.data.uv_textures.active.data[face_idx].image
        # get uv coordinate based on nearest face intersection
        uv_coord = getUVCoord(obj.data, face, point, image)
        # retrieve rgba value at uv coordinate
        rgba = getPixel(image, uv_coord, uv_images)

        # pick material based on rgba value
        brick_materials_installed = hasattr(scn, "isBrickMaterialsInstalled") and scn.isBrickMaterialsInstalled
        if cm.brickType != "Custom" and brick_materials_installed:
            matName = findNearestBrickColorName(rgba)
        else:
            # TODO: create new material with exact RGBA values found at pixel
            matName = ""
    # get closest material using material slot of face
    elif obj.data.uv_layers.active is None and len(obj.material_slots) > 0:
        slot = obj.material_slots[f.material_index]
        mat = slot.material
        matName = mat.name if mat is not None else ""

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
