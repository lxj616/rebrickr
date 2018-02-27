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
from ..lib.abs_plastic_materials import getAbsPlasticMaterials
from .makeBricks_utils import *


@timed_call('Time Elapsed')
def makeBricks(parent, logo, dimensions, bricksDict, cm=None, split=False, brickScale=None, customData=None, customObj_details=None, group_name=None, replaceExistingGroup=True, frameNum=None, cursorStatus=False, keys="ALL", printStatus=True):
    # set up variables
    scn = bpy.context.scene
    cm = cm or scn.cmlist[scn.cmlist_index]
    n = cm.source_name
    zStep = getZStep(cm)

    # apply transformation to logo duplicate and get bounds(logo)
    logo_details, logo = prepareLogoAndGetDetails(logo)

    # reset brickSizes/TypesUsed
    if keys == "ALL":
        cm.brickSizesUsed = ""
        cm.brickTypesUsed = ""

    mergeVertical = not keys == "ALL" or cm.brickType == "BRICKS AND PLATES"

    # get bricksDict dicts in seeded order
    if keys == "ALL":
        keys = list(bricksDict.keys())
    keys.sort()
    random.seed(cm.mergeSeed)
    random.shuffle(keys)
    # sort the list by the first character only
    keys.sort(key=lambda x: strToList(x)[2])

    # get brick group
    group_name = group_name or 'Rebrickr_%(n)s_bricks' % locals()
    bGroup = bpy.data.groups.get(group_name)
    # create new group if no existing group found
    if bGroup is None:
        bGroup = bpy.data.groups.new(group_name)
    # else, replace existing group
    elif replaceExistingGroup:
        bpy.data.groups.remove(group=bGroup, do_unlink=True)
        bGroup = bpy.data.groups.new(group_name)

    brick_mats = []
    brick_materials_installed = hasattr(scn, "isBrickMaterialsInstalled") and scn.isBrickMaterialsInstalled
    if cm.materialType == "RANDOM" and brick_materials_installed:
        mats0 = bpy.data.materials.keys()
        brick_mats = [color for color in bpy.props.abs_plastic_materials if color in mats0 and color in getAbsPlasticMaterials]

    # initialize progress bar around cursor
    old_percent = 0
    if cursorStatus:
        wm = bpy.context.window_manager
        wm.progress_begin(0, 100)

    # initialize random states
    randS1 = np.random.RandomState(cm.mergeSeed)  # for brickSize calc
    randS2 = np.random.RandomState(0)  # for random colors, seed will be changed later
    randS3 = np.random.RandomState(cm.mergeSeed+1)
    randS4 = np.random.RandomState(cm.mergeSeed+2)

    mats = []
    allBrickMeshes = []
    lowestLoc = -1
    # set up internal material for this object
    internalMat = bpy.data.materials.get(cm.internalMatName) or bpy.data.materials.get("Rebrickr_%(n)s_internal" % locals()) or bpy.data.materials.new("Rebrickr_%(n)s_internal" % locals())
    if cm.materialType == "SOURCE" and cm.matShellDepth < cm.shellThickness:
        mats.append(internalMat)
    # initialize supportBrickDs
    supportBrickDs = []
    bricksCreated = []
    keysNotChecked = keys.copy()
    if printStatus:
        update_progress("Building", 0.0)
    # set number of times to run through all keys
    numIters = 2 if "PLATES" in cm.brickType else 1
    for timeThrough in range(numIters):
        # iterate through locations in bricksDict from bottom to top
        for i, key in enumerate(keys):
            brickD = bricksDict[key]
            # skip keys that are already drawn or have attempted merge
            if not brickD["draw"] or brickD["parent_brick"] not in [None, "self"] or brickD["attempted_merge"]:
                # remove ignored keys from keysNotChecked (for attemptMerge)
                if key in keysNotChecked:
                    keysNotChecked.remove(key)
                continue

            # initialize vars
            loc = strToList(key)
            brickSizes = [[1, 1, zStep]]

            # skip second and third rows on first time through
            if "PLATES" in cm.brickType and cm.alignBricks:
                # initialize lowestLoc if not done already
                if lowestLoc == -1:
                    lowestLoc = loc[2]
                # check if row should be skipped
                if skipThisRow(timeThrough, lowestLoc, loc):
                    continue

            # merge current brick with available adjacent bricks
            brickSize = mergeWithAdjacentBricks(cm, brickD, bricksDict, key, keysNotChecked, brickSizes, zStep, randS1, mergeVertical=mergeVertical)
            # add brickSize to cm.brickSizesUsed if not already there
            brickSizeStr = listToStr(sorted(brickSize[:2]) + [brickSize[2]])
            cm.brickSizesUsed += brickSizeStr if cm.brickSizesUsed == "" else ("|" + brickSizeStr if brickSizeStr not in cm.brickSizesUsed.split("|") else "")
            cm.brickTypesUsed += brickD["type"] if cm.brickTypesUsed == "" else ("|" + str(brickD["type"]) if brickD["type"] not in cm.brickTypesUsed.split("|") else "")


            # create brick based on the current brickD information
            lastBricksDict = bricksDict
            drawBrick(cm, bricksDict, brickD, key, loc, keys, i, dimensions, brickSize, split, customData, customObj_details, brickScale, keysNotChecked, bricksCreated, supportBrickDs, allBrickMeshes, logo, logo_details, mats, brick_mats, internalMat, randS1, randS2, randS3, randS4)

            # print build status to terminal
            old_percent = printBuildStatus(keys, printStatus, cursorStatus, keysNotChecked, old_percent)

            # remove keys in new brick from keysNotChecked (for attemptMerge)
            updateKeysNotChecked(brickSize, loc, zStep, keysNotChecked, key)

    # remove duplicate of original logoDetail
    if cm.logoDetail != "LEGO" and logo is not None:
        bpy.data.objects.remove(logo)
    # end progress bar in terminal
    if printStatus:
        update_progress("Building", 1)
    # end progress bar on cursor
    if cursorStatus:
        wm.progress_end()

    # combine meshes, link to scene, and add relevant data to the new Blender MESH object
    if split:
        # set origins of created bricks
        if cm.originSet:
            for brick in bricksCreated:
                scn.objects.link(brick)
            select(bricksCreated)
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
            select(bricksCreated, deselect=True)
            for brick in bricksCreated:
                scn.objects.unlink(brick)
        # iterate through keys
        old_percent = 0
        for i, key in enumerate(keys):
            if printStatus:
                # print status to terminal
                percent = i/len(bricksDict)
                if percent - old_percent > 0.001 and percent < 1:
                    update_progress("Linking to Scene", percent)
                    old_percent = percent

            if bricksDict[key]["parent_brick"] == "self" and bricksDict[key]["draw"]:
                name = bricksDict[key]["name"]
                brick = bpy.data.objects.get(name)
                # create vert group for bevel mod (assuming only logo verts are selected):
                vg = brick.vertex_groups.new("%(name)s_bevel" % locals())
                vertList = [v.index for v in brick.data.vertices if not v.select]
                vg.add(vertList, 1, "ADD")
                # set up remaining brick info
                bGroup.objects.link(brick)
                brick.parent = parent
                scn.objects.link(brick)
                brick.isBrick = True
        if printStatus:
            update_progress("Linking to Scene", 1)
    else:
        m = combineMeshes(allBrickMeshes)
        name = 'Rebrickr_%(n)s_bricks_combined' % locals()
        if frameNum:
            name = "%(name)s_frame_%(frameNum)s" % locals()
        allBricksObj = bpy.data.objects.new(name, m)
        allBricksObj.cmlist_id = cm.id
        # create vert group for bevel mod (assuming only logo verts are selected):
        vg = allBricksObj.vertex_groups.new("%(name)s_bevel" % locals())
        vertList = [v.index for v in allBricksObj.data.vertices if not v.select]
        # vertList = []
        # for v in allBricksObj.data.vertices:
        #     if not v.select:
        #         vertList.append(v.index)
        vg.add(vertList, 1, "ADD")
        # add edge split modifier
        addEdgeSplitMod(allBricksObj)
        bGroup.objects.link(allBricksObj)
        allBricksObj.parent = parent
        if cm.materialType == "CUSTOM":
            mat = bpy.data.materials.get(cm.materialName)
            if mat is not None:
                allBricksObj.data.materials.append(mat)
        elif cm.materialType == "SOURCE" or (cm.materialType == "RANDOM" and len(brick_mats) > 0):
            for mat in mats:
                allBricksObj.data.materials.append(mat)
        scn.objects.link(allBricksObj)
        # protect allBricksObj from being deleted
        allBricksObj.isBrickifiedObject = True
        bricksCreated.append(allBricksObj)

    # reset 'attempted_merge' for all items in bricksDict
    for key0 in bricksDict:
        bricksDict[key0]["attempted_merge"] = False

    return bricksCreated, bricksDict
