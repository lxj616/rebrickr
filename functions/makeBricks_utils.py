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
import numpy as np

# Blender imports
import bpy
from mathutils import Vector, Matrix

# Rebrickr imports
from .hashObject import hash_object
from ..lib.Brick import Bricks
from ..lib.bricksDict import *
from .common import *
from .wrappers import *
from .general import bounds
from ..lib.caches import rebrickr_bm_cache


def drawBrick(cm, bricksDict, brickD, key, loc, keys, i, dimensions, brickSize, split, customData, customObj_details, brickScale, keysNotChecked, bricksCreated, supportBrickDs, allBrickMeshes, logo, logo_details, mats, brick_mats, internalMat, randS1, randS2, randS3, randS4):
    # check exposure of current [merged] brick
    if brickD["top_exposed"] is None or brickD["bot_exposed"] is None or cm.buildIsDirty:
        topExposed, botExposed = getBrickExposure(cm, bricksDict, key, loc)
        brickD["top_exposed"] = topExposed
        brickD["bot_exposed"] = botExposed
    else:
        topExposed = brickD["top_exposed"]
        botExposed = brickD["bot_exposed"]

    # get brick material
    mat = getMaterial(cm, bricksDict, key, brickSize, randS2, brick_mats, i)

    # set up arguments for brick mesh
    logoToUse = logo if topExposed else None
    useStud = (topExposed and cm.studDetail != "None") or cm.studDetail == "On All Bricks"
    undersideDetail = cm.exposedUndersideDetail if botExposed else cm.hiddenUndersideDetail

    ### CREATE BRICK ###

    # add brick with new mesh data at original location
    if cm.brickType == "Custom":
        bm = bmesh.new()
        bm.from_mesh(customData)
        addToMeshLoc((-customObj_details.x.mid, -customObj_details.y.mid, -customObj_details.z.mid), bm=bm)

        maxDist = max(customObj_details.x.dist, customObj_details.y.dist, customObj_details.z.dist)
        bmesh.ops.scale(bm, vec=Vector(((brickScale.x - dimensions["gap"]) / customObj_details.x.dist, (brickScale.y - dimensions["gap"]) / customObj_details.y.dist, (brickScale.z - dimensions["gap"]) / customObj_details.z.dist)), verts=bm.verts)
    else:
        # get brick mesh
        # bm = Bricks.new_mesh(dimensions=dimensions, size=brickSize, undersideDetail=undersideDetail, logo=logoToUse, logo_details=logo_details, logo_scale=cm.logoScale, logo_inset=cm.logoInset, stud=useStud, circleVerts=cm.circleVerts)
        bm = getBrickMesh(cm, brickD, randS4, dimensions, brickSize, undersideDetail, logoToUse, cm.logoDetail, logo_details, cm.logoScale, cm.logoInset, useStud, cm.circleVerts)
    # apply random rotation to BMesh according to parameters
    if cm.randomRot > 0:
        # get half width
        d = Vector((dimensions["width"] / 2, dimensions["width"] / 2, dimensions["height"] / 2))
        # get scalar for d in positive xyz directions
        scalar = Vector((brickSize[0] * 2 - 1,
                         brickSize[1] * 2 - 1,
                         1))
        # calculate center and rotate bm about center
        center = (vector_mult(d, scalar) - d) / 2
        center.z = 0
        randRot = randomizeRot(randS3, center.to_tuple(), brickSize, bm)
    # create new mesh and send bm to it
    m = bpy.data.meshes.new(brickD["name"] + 'Mesh')
    bm.to_mesh(m)
    # apply random location to edit mesh according to parameters
    if cm.randomLoc > 0:
        randomizeLoc(randS3, dimensions["width"], dimensions["height"], mesh=m)
    # undo bm rotation if not custom, since 'bm' points to bmesh used by all other similar bricks
    if cm.brickType != "Custom" and cm.randomRot > 0:
        rotateBack(bm, center, randRot)
    # get brick's location
    if brickSize[2] == 3 and cm.brickType == "Bricks and Plates":
        brickLoc = Vector(brickD["co"])
        brickLoc[2] = brickLoc[2] + dimensions["height"] + dimensions["gap"]
    else:
        brickLoc = Vector(brickD["co"])
    if split:
        # create new object with mesh data
        brick = bpy.data.objects.new(brickD["name"], m)
        brick.cmlist_id = cm.id
        # set brick's location
        brick.location = brickLoc
        # set brick's material
        brick.data.materials.append(mat if mat is not None else internalMat)
        # add edge split modifier
        addEdgeSplitMod(brick)
        # append to bricksCreated
        bricksCreated.append(brick)
    else:
        # transform brick mesh to coordinate on matrix
        addToMeshLoc(brickLoc, mesh=m)
        # keep track of mats already use
        if mat in mats:
            matIdx = mats.index(mat)
        elif mat is not None:
            mats.append(mat)
            matIdx = len(mats) - 1
        # set material for mesh
        if mat is not None:
            m.materials.append(mat)
            for p in m.polygons:
                p.material_index = matIdx
        else:
            for p in m.polygons:
                p.material_index = 0
        # append mesh to allBrickMeshes list
        allBrickMeshes.append(m)


def addEdgeSplitMod(obj):
    """ Add edge split modifier """
    eMod = obj.modifiers.new('Edge Split', 'EDGE_SPLIT')


def mergeWithAdjacentBricks(cm, brickD, bricksDict, key, keysNotChecked, loc, brickSizes, zStep, randS1):
    if brickD["size"] is None or (cm.buildIsDirty):
        preferLargest = brickD["val"] > 0 and brickD["val"] < 1
        brickSize = attemptMerge(cm, bricksDict, key, keysNotChecked, loc, brickSizes, zStep, randS1, preferLargest=preferLargest, mergeVertical=True)
    else:
        brickSize = brickD["size"]
    return brickSize


def printBuildStatus(keys, printStatus, cursorStatus, keysNotChecked, old_percent):
    if printStatus:
        # print status to terminal
        percent = 1 - (len(keysNotChecked) / len(keys))
        if percent - old_percent > 0.001 and percent < 1:
            update_progress("Building", percent)
            if cursorStatus:
                wm = bpy.context.window_manager
                wm.progress_update(percent*100)
            old_percent = percent
    return old_percent


def updateKeysNotChecked(brickSize, loc, zStep, keysNotChecked, key):
    for x1 in range(brickSize[0]):
        for y1 in range(brickSize[1]):
            for z1 in range(brickSize[2], zStep):
                try:
                    keyChecked = listToStr([Vector(loc) + Vector((x1, y1, z1))])
                    keysNotChecked.remove(keyChecked)
                except ValueError:
                    pass


def skipThisRow(timeThrough, lowestLoc, loc):
    if timeThrough == 0:  # first time
        if (loc[2] - cm.offsetBrickLayers - lowestLoc) % 3 in [1, 2]:
            return True
    else:  # second time
        if (loc[2] - cm.offsetBrickLayers - lowestLoc) % 3 == 0:
            return True
    return False


def combineMeshes(meshes):
    """ return combined mesh from 'meshes' """
    bm = bmesh.new()
    # add meshes to bmesh
    for m in meshes:
        bm.from_mesh(m)
    finalMesh = bpy.data.meshes.new("newMesh")
    bm.to_mesh(finalMesh)
    return finalMesh


def addToMeshLoc(co, bm=None, mesh=None):
    """ add 'co' to bm/mesh location """
    assert bm or mesh  # one or the other must not be None!
    verts = bm.verts if bm else mesh.vertices
    for v in verts:
        v.co = (v.co[0] + co[0], v.co[1] + co[1], v.co[2] + co[2])


def randomizeLoc(rand, width, height, bm=None, mesh=None):
    """ translate bm/mesh location by (width,width,height) randomized by cm.randomLoc """
    assert bm or mesh  # one or the other must not be None!
    verts = bm.verts if bm else mesh.vertices
    scn, cm, _ = getActiveContextInfo()

    x = rand.uniform(-(width/2) * cm.randomLoc, (width/2) * cm.randomLoc)
    y = x
    z = rand.uniform(-(height/2) * cm.randomLoc, (height/2) * cm.randomLoc)
    for v in verts:
        v.co += Vector((x, y, z))
    return (x, y, z)


def translateBack(bm, loc):
    """ translate bm location by -loc """
    for v in bm.verts:
        v.co -= Vector(loc)


def randomizeRot(rand, center, brickSize, bm):
    """ rotate 'bm' around 'center' randomized by cm.randomRot """
    scn, cm, _ = getActiveContextInfo()
    if max(brickSize) == 0:
        denom = 0.75
    else:
        denom = brickSize[0] * brickSize[1]
    mult = cm.randomRot / denom
    x = rand.uniform(-math.radians(11.25) * mult, math.radians(11.25) * mult)
    y = rand.uniform(-math.radians(11.25) * mult, math.radians(11.25) * mult)
    z = rand.uniform(-math.radians(45)    * mult, math.radians(45)    * mult)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=center, matrix=Matrix.Rotation(x, 3, 'X'))
    bmesh.ops.rotate(bm, verts=bm.verts, cent=center, matrix=Matrix.Rotation(y, 3, 'Y'))
    bmesh.ops.rotate(bm, verts=bm.verts, cent=center, matrix=Matrix.Rotation(z, 3, 'Z'))
    return (x, y, z)


def rotateBack(bm, center, rot):
    """ rotate bm around center -rot """
    for i, axis in enumerate(['Z', 'Y', 'X']):
        bmesh.ops.rotate(bm, verts=bm.verts, cent=center, matrix=Matrix.Rotation(-rot[2-i], 3, axis))


def prepareLogoAndGetDetails(logo):
    """ duplicate and normalize custom logo object; return logo and bounds(logo) """
    scn, cm, _ = getActiveContextInfo()
    if cm.logoDetail != "LEGO Logo" and logo is not None:
        oldLayers = list(scn.layers)
        setLayers(logo.layers)
        logo.hide = False
        select(logo, active=logo)
        bpy.ops.object.duplicate()
        logo = scn.objects.active
        for mod in logo.modifiers:
            mod.show_viewport = False
        logo.parent = None
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        setLayers(oldLayers)
        logo_details = bounds(logo)
    else:
        logo_details = None
    return logo_details, logo


def getBrickMesh(cm, brickD, rand, dimensions, brickSize, undersideDetail, logoToUse, logo_type, logo_details, logo_scale, logo_inset, useStud, circleVerts):
    # get bm_cache_string
    bm_cache_string = ""
    if cm.brickType in ["Bricks", "Plates", "Bricks and Plates"]:
        custom_logo_used = logoToUse is not None and logo_type == "Custom Logo"
        bm_cache_string = json.dumps((cm.brickHeight, brickSize, undersideDetail,
                                      cm.logoResolution if logoToUse is not None else None,
                                      hash_object(logoToUse) if custom_logo_used else None,
                                      logo_scale if custom_logo_used else None,
                                      logo_inset if custom_logo_used else None,
                                      useStud, cm.circleVerts, brickD["type"],
                                      brickD["flipped"] if brickD["type"] in ["SLOPE", "SLOPE_INVERTED"] else None,
                                      brickD["rotated"] if brickD["type"] in ["SLOPE", "SLOPE_INVERTED"] else None))

    # check for bmesh in cache
    bms = rebrickr_bm_cache.get(bm_cache_string)
    # if bmesh in cache
    if bms is not None:
        bm = bms[rand.randint(0, len(bms))] if len(bms) > 1 else bms[0]
    # if not found in rebrickr_bm_cache, create new brick mesh(es) and store to cache
    else:
        bms = Bricks.new_mesh(dimensions=dimensions, size=brickSize, type=brickD["type"], undersideDetail=undersideDetail, flip=brickD["flipped"], rotate90=brickD["rotated"], logo=logoToUse, logo_type=logo_type, all_vars=logoToUse is not None, logo_details=logo_details, logo_scale=cm.logoScale, logo_inset=cm.logoInset, stud=useStud, circleVerts=cm.circleVerts)
        if cm.brickType in ["Bricks", "Plates", "Bricks and Plates"]:
            rebrickr_bm_cache[bm_cache_string] = bms
        bm = bms[rand.randint(0, len(bms))]

    return bm


def getMaterial(cm, bricksDict, key, brickSize, randState, brick_mats, k):
    mat = None
    highestVal = 0
    matsL = []
    if cm.materialType == "Custom":
        mat = bpy.data.materials.get(cm.materialName)
    elif cm.materialType == "Use Source Materials":
        # get most frequent material in brick size
        for x in range(brickSize[0]):
            for y in range(brickSize[1]):
                loc = strToList(key)
                x0, y0, z0 = loc
                key0 = listToStr([x0 + x, y0 + y, z0])
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
    elif cm.materialType == "Random" and len(brick_mats) > 0:
        randState.seed(cm.randomMatSeed + k)
        if len(brick_mats) > 1:
            randIdx = randState.randint(0, len(brick_mats))
        else:
            randIdx = 0
        matName = brick_mats[randIdx]
        mat = bpy.data.materials.get(matName)
    return mat
