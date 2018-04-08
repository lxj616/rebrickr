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
import sys
import random
import json
import copy
import numpy as np

# Blender imports
import bpy
from mathutils import Vector, Matrix

# Addon imports
from .hashObject import hash_object
from ..lib.Brick import Bricks
from ..lib.bricksDict import *
from .common import *
from .wrappers import *
from .general import *
from ..lib.caches import bricker_bm_cache


def drawBrick(ft, cm, bricksDict, key, loc, i, dimensions, zStep, brickSize, split, customData, customObj_details, brickScale, bricksCreated, allMeshes, logo, logo_details, mats, brick_mats, internalMat, randS1, randS2, randS3):
    brickD = bricksDict[key]
    # check exposure of current [merged] brick
    if brickD["top_exposed"] is None or brickD["bot_exposed"] is None or cm.buildIsDirty:
        topExposed, botExposed = getBrickExposure(cm, bricksDict, key, loc)
        brickD["top_exposed"] = topExposed
        brickD["bot_exposed"] = botExposed
    else:
        topExposed = brickD["top_exposed"]
        botExposed = brickD["bot_exposed"]

    # get brick material
    mat = getMaterial(cm, bricksDict, key, brickSize, brick_mats, i)

    # set up arguments for brick mesh
    useStud = (topExposed and cm.studDetail != "NONE") or cm.studDetail == "ALL"
    logoToUse = logo if useStud else None
    undersideDetail = cm.exposedUndersideDetail if botExposed else cm.hiddenUndersideDetail

    ### CREATE BRICK ###

    # add brick with new mesh data at original location
    if brickD["type"] == "CUSTOM":
        # copy custom mesh
        m = customData.copy()
    else:
        # get brick mesh
        bm = getBrickMesh(cm, brickD, randS3, dimensions, brickSize, undersideDetail, logoToUse, cm.logoDetail, logo_details, cm.logoScale, cm.logoInset, useStud, cm.circleVerts)
        # create new mesh and send bm to it
        meshName = brickD["name"] + 'Mesh' if split else "Bricker_junkMesh"
        m = bpy.data.meshes.get(meshName)
        if m is None:
            m = bpy.data.meshes.new(meshName)
        elif len(m.materials.keys()) > 0:
            m.materials.clear()
        # send bmesh data to 'm' edit mesh
        bm.to_mesh(m)
    # center mesh origin
    centerMeshOrigin(m, dimensions, brickSize)
    # apply random rotation to edit mesh according to parameters
    if cm.randomRot > 0: randomizeRot(cm.randomRot, randS2, brickSize, m)
    # get brick location
    locOffset = getRandomLoc(cm.randomLoc, randS2, dimensions["width"], dimensions["height"]) if cm.randomLoc > 0 else Vector((0, 0, 0))
    brickLoc = getBrickCenter(cm, bricksDict, key, loc, zStep) + locOffset

    if split:
        brick = bpy.data.objects.get(brickD["name"])
        if brick:
            # set brick.data to new mesh (resets materials)
            brick.data = m
            # NOTE: last brick mesh is left in memory (faster)
        else:
            # create new object with mesh data
            brick = bpy.data.objects.new(brickD["name"], m)
            brick.cmlist_id = cm.id
            # add edge split modifier
            if cm.brickType != "CUSTOM":
                addEdgeSplitMod(brick)
        # set brick location
        brick.location = brickLoc
        # set brick material
        if mat is not None or internalMat is not None:
            brick.data.materials.append(mat or internalMat)
        # append to bricksCreated
        bricksCreated.append(brick)
    else:
        # transform brick mesh to coordinate on matrix
        m.transform(Matrix.Translation(brickLoc))
        # keep track of mats already use
        if mat in mats:
            matIdx = mats.index(mat)
        elif mat is not None:
            mats.append(mat)
            matIdx = len(mats) - 1
        # set material for mesh
        if mat is not None:
            m.materials.append(mat)
            brickD["mat_name"] = mat.name
            for p in m.polygons:
                p.material_index = matIdx
        # append mesh to allMeshes bmesh object
        allMeshes.from_mesh(m)

    return bricksDict


def addEdgeSplitMod(obj):
    """ Add edge split modifier """
    eMod = obj.modifiers.new('Edge Split', 'EDGE_SPLIT')


def mergeWithAdjacentBricks(cm, brickD, bricksDict, key, keysNotChecked, defaultSize, zStep, randS1, mergeVertical=True):
    if brickD["size"] is None or (cm.buildIsDirty):
        preferLargest = brickD["val"] > 0 and brickD["val"] < 1
        brickSize = attemptMerge(cm, bricksDict, key, keysNotChecked, defaultSize, zStep, randS1, preferLargest=preferLargest, mergeVertical=mergeVertical)
    else:
        brickSize = brickD["size"]
    return brickSize


def updateKeysLists(cm, size, loc, availableKeys, key):
    keysChecked = getKeysInBrick(cm, size, key, loc)
    for k in keysChecked:
        if k in availableKeys:
            availableKeys.remove(k)


def skipThisRow(cm, timeThrough, lowestZ, z):
    if timeThrough == 0:  # first time
        if (z - cm.offsetBrickLayers - lowestZ) % 3 in [1, 2]:
            return True
    else:  # second time
        if (z - cm.offsetBrickLayers - lowestZ) % 3 == 0:
            return True
    return False


def getRandomLoc(randomLoc, rand, width, height):
    """ get random location between (0,0,0) and (width/2, width/2, height/2) """
    loc = Vector((0,0,0))
    loc.xy = [rand.uniform(-(width/2) * randomLoc, (width/2) * randomLoc)]*2
    loc.z = rand.uniform(-(height/2) * randomLoc, (height/2) * randomLoc)
    return loc


def centerMeshOrigin(m, dimensions, size):
    # get half width
    d0 = Vector((dimensions["width"] / 2, dimensions["width"] / 2, 0))
    # get scalar for d0 in positive xy directions
    scalar = Vector((size[0] * 2 - 1,
                     size[1] * 2 - 1,
                     0))
    # calculate center and rotate bm about center
    center = (vec_mult(d0, scalar) - d0) / 2
    # apply translation matrix to center mesh
    m.transform(Matrix.Translation(-Vector(center)))


def randomizeRot(randomRot, rand, brickSize, m):
    """ rotate edit mesh 'm' randomized by randomRot """
    denom = 0.75 if max(brickSize) == 0 else brickSize[0] * brickSize[1]
    mult = randomRot / denom
    # calculate rotation angles in radians
    x = rand.uniform(-math.radians(11.25) * mult, math.radians(11.25) * mult)
    y = rand.uniform(-math.radians(11.25) * mult, math.radians(11.25) * mult)
    z = rand.uniform(-math.radians(45)    * mult, math.radians(45)    * mult)
    # get rotation matrix
    x_mat = Matrix.Rotation(x, 4, 'X')
    y_mat = Matrix.Rotation(y, 4, 'Y')
    z_mat = Matrix.Rotation(z, 4, 'Z')
    combined_mat = x_mat * y_mat * z_mat
    # apply rotation matrices to edit mesh
    m.transform(combined_mat)


def prepareLogoAndGetDetails(scn, cm, logo, dimensions):
    """ duplicate and normalize custom logo object; return logo and bounds(logo) """
    if cm.logoDetail != "LEGO" and logo is not None:
        # prepare for logo duplication
        originalActiveName = scn.objects.active.name
        oldLayers = list(scn.layers)
        setLayers(logo.layers)
        logo.hide = False
        # duplicate logo object
        logo = duplicateObj(logo)
        # disable modifiers for logo object
        for mod in logo.modifiers:
            mod.show_viewport = False
        # apply logo object transformation
        logo.parent = None
        select(logo, active=True, only=True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        # select original selection
        originalActive = bpy.data.objects[originalActiveName]
        select(originalActive, active=True, only=True)
        # set scene layers back to original active layers
        setLayers(oldLayers)
        # get logo details
        logo_details = bounds(logo)
        m = logo.data
        # select all verts in logo
        for v in m.vertices:
            v.select = True
        # scale logo
        t_mat = Matrix.Translation(-logo_details.mid)
        distMax = max(logo_details.dist.xy)
        lw = dimensions["logo_width"] * cm.logoScale
        s_mat = Matrix.Scale(lw / distMax, 4)
        # transform logo into place
        m.transform(t_mat)
        m.transform(s_mat)
    else:
        logo_details = None
    return logo_details, logo


def getBrickMesh(cm, brickD, rand, dimensions, brickSize, undersideDetail, logoToUse, logo_type, logo_details, logo_scale, logo_inset, useStud, circleVerts):
    # get bm_cache_string
    bm_cache_string = ""
    if cm.brickType != "CUSTOM":
        custom_logo_used = logoToUse is not None and logo_type == "CUSTOM"
        bm_cache_string = json.dumps((cm.brickHeight, brickSize, undersideDetail,
                                      cm.logoResolution if logoToUse is not None else None,
                                      hash_object(logoToUse) if custom_logo_used else None,
                                      logo_scale if custom_logo_used else None,
                                      logo_inset if custom_logo_used else None,
                                      useStud, cm.circleVerts, brickD["type"],
                                      brickD["flipped"] if brickD["type"] in ["SLOPE", "SLOPE_INVERTED"] else None,
                                      brickD["rotated"] if brickD["type"] in ["SLOPE", "SLOPE_INVERTED"] else None))

    # check for bmesh in cache
    bms = bricker_bm_cache.get(bm_cache_string)
    # if bmesh in cache
    if bms is not None:
        bm = bms[rand.randint(0, len(bms))] if len(bms) > 1 else bms[0]
    # if not found in bricker_bm_cache, create new brick mesh(es) and store to cache
    else:
        bms = Bricks.new_mesh(dimensions=dimensions, size=brickSize, type=brickD["type"], undersideDetail=undersideDetail, flip=brickD["flipped"], rotate90=brickD["rotated"], logo=logoToUse, logo_type=logo_type, all_vars=logoToUse is not None, logo_details=logo_details, logo_inset=cm.logoInset, stud=useStud, circleVerts=cm.circleVerts, cm=cm)
        if cm.brickType != "CUSTOM":
            bricker_bm_cache[bm_cache_string] = bms
        bm = bms[rand.randint(0, len(bms))]

    return bm


def getMaterial(cm, bricksDict, key, size, brick_mats=None, seedInc=None):
    mat = None
    highestVal = 0
    matsL = []
    if cm.materialType == "CUSTOM":
        mat = bpy.data.materials.get(cm.materialName)
    elif cm.materialType == "SOURCE":
        # get most frequent material in brick size
        keysInBrick = getKeysInBrick(cm, size, key)
        for key0 in keysInBrick:
            curBrickD = bricksDict[key0]
            if curBrickD["val"] >= highestVal:
                highestVal = curBrickD["val"]
                matName = curBrickD["mat_name"]
                if curBrickD["val"] == 1:
                    matsL.append(matName)
        # if multiple shell materials, use the most frequent one
        if len(matsL) > 1:
            matName = most_common(matsL)
        mat = bpy.data.materials.get(matName)
    elif cm.materialType == "RANDOM" and len(brick_mats) > 0:
        randState.seed(cm.randomMatSeed + seedInc)
        if len(brick_mats) > 1:
            randState = np.random.RandomState(0)
            randIdx = randState.randint(0, len(brick_mats))
        else:
            randIdx = 0
        matName = brick_mats[randIdx]
        mat = bpy.data.materials.get(matName)
    return mat
