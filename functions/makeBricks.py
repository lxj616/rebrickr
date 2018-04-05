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

# Addon imports
from .hashObject import hash_object
from ..lib.Brick import Bricks
from ..lib.bricksDict import *
from .common import *
from .wrappers import *
from .general import bounds
from ..lib.caches import bricker_bm_cache
from ..lib.abs_plastic_materials import getAbsPlasticMaterialNames
from .makeBricks_utils import *


@timed_call('Time Elapsed')
def makeBricks(source, parent, logo, logo_details, dimensions, bricksDict, cm=None, split=False, brickScale=None, customData=None, customObj_details=None, group_name=None, replaceExistingGroup=True, frameNum=None, cursorStatus=False, keys="ALL", printStatus=True):
    # set up variables
    scn = bpy.context.scene
    cm = cm or scn.cmlist[scn.cmlist_index]
    n = cm.source_name
    zStep = getZStep(cm)

    # initialize progress bar around cursor
    old_percent = updateProgressBars(printStatus, cursorStatus, 0, -1, "Merging")

    # reset brickSizes/TypesUsed
    if keys == "ALL":
        cm.brickSizesUsed = ""
        cm.brickTypesUsed = ""

    mergeVertical = keys != "ALL" or cm.brickType == "BRICKS AND PLATES"

    # get bricksDict keys in sorted order
    if keys == "ALL":
        keys = list(bricksDict.keys())
    keys.sort()
    # get dictionary of keys based on z value
    keysDict = {}
    for k0 in keys:
        z = strToList(k0)[2]
        if bricksDict[k0]["draw"]:
            if z in keysDict:
                keysDict[z].append(k0)
            else:
                keysDict[z] = [k0]
    denom = sum([len(keysDict[z0]) for z0 in keysDict.keys()])

    # get brick group
    group_name = group_name or 'Bricker_%(n)s_bricks' % locals()
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
        brick_mats = [color for color in bpy.props.abs_plastic_materials if color in mats0 and color in getAbsPlasticMaterialNames()]

    # initialize random states
    randS1 = np.random.RandomState(cm.mergeSeed)  # for brickSize calc
    randS2 = np.random.RandomState(cm.mergeSeed+1)
    randS3 = np.random.RandomState(cm.mergeSeed+2)

    mats = []
    allBrickMeshes = []
    lowestZ = -1
    availableKeys = []
    maxBrickHeight = 1 if zStep == 3 else max(legalBricks.keys())
    connectThresh = 1 if cm.brickType == "CUSTOM" else cm.connectThresh
    # set up internal material for this object
    internalMat = None if len(source.data.materials) == 0 else bpy.data.materials.get(cm.internalMatName) or bpy.data.materials.get("Bricker_%(n)s_internal" % locals()) or bpy.data.materials.new("Bricker_%(n)s_internal" % locals())
    if internalMat is not None and cm.materialType == "SOURCE" and cm.matShellDepth < cm.shellThickness:
        mats.append(internalMat)
    # initialize bricksCreated
    bricksCreated = []
    # set number of times to run through all keys
    numIters = 2 if "PLATES" in cm.brickType else 1
    i = 0
    for timeThrough in range(numIters):
        # iterate through z locations in bricksDict (bottom to top)
        for z in sorted(keysDict.keys()):
            # skip second and third rows on first time through
            if numIters == 2 and cm.alignBricks:
                # initialize lowestZ if not done already
                if lowestZ == -0.1:
                    lowestZ = z
                if skipThisRow(cm, timeThrough, lowestZ, z):
                    continue
            # get availableKeys for attemptMerge
            availableKeysBase = [keysDict[z + ii] for ii in range(maxBrickHeight) if ii + z in keysDict]
            # get small duplicate of bricksDict for variations
            if connectThresh > 1:
                bricksDictsBase = {}
                for k4 in availableKeysBase:
                    bricksDictsBase[k4] = deepcopy(bricksDict[k4])
                bricksDicts = [deepcopy(bricksDictsBase) for j in range(connectThresh)]
                numAlignedEdges = [0 for idx in range(connectThresh)]
            else:
                bricksDicts = [bricksDict]
            # calculate build variations for current z level
            for j in range(connectThresh):
                availableKeys = availableKeysBase.copy()
                numBricks = 0
                random.seed(cm.mergeSeed + i)
                random.shuffle(keysDict[z])
                # iterate through keys on current z level
                for key in keysDict[z]:
                    i += 1 / connectThresh
                    brickD = bricksDicts[j][key]
                    # skip keys that are already drawn or have attempted merge
                    if brickD["attempted_merge"] or brickD["parent"] not in [None, "self"]:
                        # remove ignored keys from availableKeys (for attemptMerge)
                        if key in availableKeys:
                            availableKeys.remove(key)
                        continue

                    # initialize loc
                    loc = strToList(key)

                    # merge current brick with available adjacent bricks
                    brickSize = mergeWithAdjacentBricks(cm, brickD, bricksDicts[j], key, availableKeys, [1, 1, zStep], zStep, randS1, mergeVertical=mergeVertical)
                    brickD["size"] = brickSize
                    # iterate number aligned edges and bricks if generating multiple variations
                    if connectThresh > 1:
                        numAlignedEdges[j] += getNumAlignedEdges(cm, bricksDict, brickSize, key, loc, zStep)
                        numBricks += 1
                    # add brickSize to cm.brickSizesUsed if not already there
                    brickSizeStr = listToStr(sorted(brickSize[:2]) + [brickSize[2]])
                    cm.brickSizesUsed += brickSizeStr if cm.brickSizesUsed == "" else ("|" + brickSizeStr if brickSizeStr not in cm.brickSizesUsed.split("|") else "")
                    cm.brickTypesUsed += brickD["type"] if cm.brickTypesUsed == "" else ("|" + str(brickD["type"]) if brickD["type"] not in cm.brickTypesUsed.split("|") else "")

                    # print status to terminal and cursor
                    cur_percent = (i / denom)
                    old_percent = updateProgressBars(printStatus, cursorStatus, cur_percent, old_percent, "Merging")

                    # remove keys in new brick from availableKeys (for attemptMerge)
                    updateKeysLists(cm, brickSize, loc, availableKeys, key)

                if connectThresh > 1:
                    # if no aligned edges / bricks found, skip to next z level
                    if numAlignedEdges[j] == 0:
                        i += (len(keysDict[z]) * connectThresh - 1) / connectThresh
                        break
                    # add double the number of bricks so connectivity threshold is weighted towards larger bricks
                    numAlignedEdges[j] += numBricks * 2

            # choose optimal variation from above for current z level
            if connectThresh > 1:
                optimalTest = numAlignedEdges.index(min(numAlignedEdges))
                for k3 in bricksDicts[optimalTest]:
                    bricksDict[k3] = bricksDicts[optimalTest][k3]

    # switch progress bars to 'Building'
    updateProgressBars(printStatus, cursorStatus, 1, 0, "Merging", end=True)
    old_percent = updateProgressBars(printStatus, cursorStatus, 0, -1, "Building")

    # draw merged bricks
    for i, k2 in enumerate(keys):
        if bricksDict[k2]["draw"] and bricksDict[k2]["parent"] == "self":
            loc = strToList(k2)
            # create brick based on the current brick info
            drawBrick(cm, bricksDict, k2, loc, i, dimensions, zStep, bricksDict[k2]["size"], split, customData, customObj_details, brickScale, bricksCreated, allBrickMeshes, logo, logo_details, mats, brick_mats, internalMat, randS1, randS2, randS3)
            # print status to terminal and cursor
            old_percent = updateProgressBars(printStatus, cursorStatus, i/len(bricksDict.keys()), old_percent, "Building")

    # end progress bars
    updateProgressBars(printStatus, cursorStatus, 1, 0, "Building", end=True)

    # remove duplicate of original logoDetail
    if cm.logoDetail != "LEGO" and logo is not None:
        bpy.data.objects.remove(logo)

    # combine meshes, link to scene, and add relevant data to the new Blender MESH object
    if split:
        # iterate through keys
        old_percent = 0
        for i, key in enumerate(keys):
            # print status to terminal and cursor
            old_percent = updateProgressBars(printStatus, cursorStatus, i/len(bricksDict), old_percent, "Linking to Scene")

            if bricksDict[key]["parent"] == "self" and bricksDict[key]["draw"]:
                name = bricksDict[key]["name"]
                brick = bpy.data.objects.get(name)
                # create vert group for bevel mod (assuming only logo verts are selected):
                vg = brick.vertex_groups.new("%(name)s_bvl" % locals())
                vertList = [v.index for v in brick.data.vertices if not v.select]
                vg.add(vertList, 1, "ADD")
                # set up remaining brick info
                bGroup.objects.link(brick)
                brick.parent = parent
                scn.objects.link(brick)
                brick.isBrick = True
        # end progress bars
        updateProgressBars(printStatus, cursorStatus, 1, 0, "Linking to Scene", end=True)
    else:
        m = combineMeshes(allBrickMeshes, printStatus)
        name = 'Bricker_%(n)s_bricks_combined' % locals()
        if frameNum:
            name = "%(name)s_f_%(frameNum)s" % locals()
        allBricksObj = bpy.data.objects.new(name, m)
        allBricksObj.cmlist_id = cm.id
        if cm.brickType != "CUSTOM":
            # create vert group for bevel mod (assuming only logo verts are selected):
            vg = allBricksObj.vertex_groups.new("%(name)s_bvl" % locals())
            vertList = [v.index for v in allBricksObj.data.vertices if not v.select]
            vg.add(vertList, 1, "ADD")
            # add edge split modifier
            addEdgeSplitMod(allBricksObj)
        if cm.materialType == "CUSTOM":
            mat = bpy.data.materials.get(cm.materialName)
            if mat is not None:
                allBricksObj.data.materials.append(mat)
        elif cm.materialType == "SOURCE" or (cm.materialType == "RANDOM" and len(brick_mats) > 0):
            for mat in mats:
                allBricksObj.data.materials.append(mat)
        # set parent
        allBricksObj.parent = parent
        # add bricks obj to scene, bGroup, and bricksCreated
        bGroup.objects.link(allBricksObj)
        scn.objects.link(allBricksObj)
        bricksCreated.append(allBricksObj)
        # protect allBricksObj from being deleted
        allBricksObj.isBrickifiedObject = True

    # reset 'attempted_merge' for all items in bricksDict
    for key0 in bricksDict:
        bricksDict[key0]["attempted_merge"] = False

    return bricksCreated, bricksDict
