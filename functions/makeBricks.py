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

def addEdgeSplitMod(obj):
    """ Add edge split modifier """
    eMod = obj.modifiers.new('Edge Split', 'EDGE_SPLIT')

def combineMeshes(meshes):
    """ return combined mesh from 'meshes' """
    bm = bmesh.new()
    # add meshes to bmesh
    for m in meshes:
        bm.from_mesh( m )
    finalMesh = bpy.data.meshes.new( "newMesh" )
    bm.to_mesh( finalMesh )
    return finalMesh

def addToMeshLoc(co, bm=None, mesh=None):
    """ add 'co' to bm/mesh location """
    assert bm is not None or mesh is not None # one or the other must not be None!
    verts = bm.verts if bm is not None else mesh.vertices
    for v in verts:
        v.co = (v.co[0] + co[0], v.co[1] + co[1], v.co[2] + co[2])

def randomizeLoc(rand, width, height, bm=None, mesh=None):
    """ translate bm/mesh location by (width,width,height) randomized by cm.randomLoc """
    assert bm is not None or mesh is not None # one or the other must not be None!
    verts = bm.verts if bm is not None else mesh.vertices
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]

    x = rand.uniform(-(width/2) * cm.randomLoc, (width/2) * cm.randomLoc)
    y = rand.uniform(-(width/2) * cm.randomLoc, (width/2) * cm.randomLoc)
    z = rand.uniform(-(height/2) * cm.randomLoc, (height/2) * cm.randomLoc)
    for v in verts:
        v.co.x += x
        v.co.y += y
        v.co.z += z
    return (x,y,z)
def translateBack(bm, loc):
    """ translate bm location by -loc """
    for v in bm.verts:
        v.co.x -= loc[0]
        v.co.y -= loc[1]
        v.co.z -= loc[2]

def randomizeRot(rand, center, brickSize, bm):
    """ rotate 'bm' around 'center' randomized by cm.randomRot """
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    if max(brickSize) == 0:
        denom = 0.75
    else:
        denom = brickSize[0] * brickSize[1]
    x=rand.uniform(-0.1963495 * cm.randomRot / denom, 0.1963495 * cm.randomRot / denom)
    y=rand.uniform(-0.1963495 * cm.randomRot / denom, 0.1963495 * cm.randomRot / denom)
    z=rand.uniform(-0.785398 * cm.randomRot / denom, 0.785398 * cm.randomRot / denom)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=center, matrix=Matrix.Rotation(x, 3, 'X'))
    bmesh.ops.rotate(bm, verts=bm.verts, cent=center, matrix=Matrix.Rotation(y, 3, 'Y'))
    bmesh.ops.rotate(bm, verts=bm.verts, cent=center, matrix=Matrix.Rotation(z, 3, 'Z'))
    return (x,y,z)
def rotateBack(bm, center, rot):
    """ rotate bm around center -rot """
    for i,axis in enumerate(['Z', 'Y', 'X']):
        bmesh.ops.rotate(bm, verts=bm.verts, cent=center, matrix=Matrix.Rotation(-rot[2-i], 3, axis))

def prepareLogoAndGetDetails(logo):
    """ duplicate and normalize custom logo object; return logo and bounds(logo) """
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    if cm.logoDetail != "LEGO Logo" and logo is not None:
        oldLayers = list(scn.layers)
        setLayers(scn, logo.layers)
        logo.hide = False
        select(logo, active=logo)
        bpy.ops.object.duplicate()
        logo = scn.objects.active
        for mod in logo.modifiers:
            mod.show_viewport = False
        logo.parent = None
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        setLayers(scn, oldLayers)
        logo_details = bounds(logo)
    else:
        logo_details = None
    return logo_details, logo

def getBrickMesh(cm, rand, dimensions, brickSize, undersideDetail, logoToUse, logo_type, logo_details, logo_scale, logo_inset, useStud, numStudVerts):
    # get bm_cache_string
    bm_cache_string = ""
    if cm.brickType in ["Bricks", "Plates", "Bricks and Plates"]:
        custom_logo_used = logoToUse is not None and logo_type == "Custom Logo"
        bm_cache_string = json.dumps((cm.brickHeight, brickSize, undersideDetail, cm.logoResolution if logoToUse is not None else None, hash_object(logoToUse) if custom_logo_used else None, logo_scale if custom_logo_used else None, logo_inset if custom_logo_used else None, cm.studVerts if useStud else None))

    # check for bmesh in cache
    bms = rebrickr_bm_cache.get(bm_cache_string)
    # if bmesh in cache
    if bms is not None:
        bm = bms[rand.randint(0,len(bms))] if len(bms) > 1 else bms[0]
    # if not found in rebrickr_bm_cache, create new brick mesh(es) and store to cache
    else:
        bms = Bricks.new_mesh(dimensions=dimensions, size=brickSize, undersideDetail=undersideDetail, logo=logoToUse, logo_type=logo_type, all_vars=logoToUse is not None, logo_details=logo_details, logo_scale=cm.logoScale, logo_inset=cm.logoInset, stud=useStud, numStudVerts=cm.studVerts)
        if cm.brickType in ["Bricks", "Plates", "Bricks and Plates"]:
            rebrickr_bm_cache[bm_cache_string] = bms
        bm = bms[rand.randint(0,len(bms))]

    return bm

def getMaterial(cm, bricksDict, key, brickSize, randState, brick_mats, k):
    mat = None
    highestVal = 0
    matsL = []
    if cm.materialType == "Custom":
        mat = bpy.data.materials.get(cm.materialName)
    elif cm.materialType == "Use Source Materials":
        for x in range(brickSize[0]):
            for y in range(brickSize[1]):
                loc = strToList(key)
                x0,y0,z0 = loc
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
        k += 1
        randIdx = randState.randint(0, len(brick_mats)) if len(brick_mats > 1) else 0
        matName = brick_mats[randIdx]
        mat = bpy.data.materials.get(matName)
    return mat


@timed_call('Time Elapsed')
def makeBricks(parent, logo, dimensions, bricksDict, cm=None, split=False, R=None, customData=None, customObj_details=None, group_name=None, replaceExistingGroup=True, frameNum=None, cursorStatus=False, keys="ALL", printStatus=True):
    # set up variables
    scn = bpy.context.scene
    if cm is None: cm = scn.cmlist[scn.cmlist_index]
    n = cm.source_name
    zStep = getZStep(cm)
    BandP = cm.brickType == "Bricks and Plates"

    # apply transformation to logo duplicate and get bounds(logo)
    logo_details, logo = prepareLogoAndGetDetails(logo)

    # get bricksDict dicts in seeded order
    if keys == "ALL": keys = list(bricksDict.keys())
    keys.sort()
    random.seed(cm.mergeSeed)
    random.shuffle(keys)
    # sort the list by the first character only
    keys.sort(key=lambda x: strToList(x)[2])

    # get brick group
    if group_name is None: group_name = 'Rebrickr_%(n)s_bricks' % locals()
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
    if cm.materialType == "Random" and brick_materials_installed:
        mats0 = bpy.data.materials.keys()
        for color in bpy.props.abs_plastic_materials:
            if color in mats0 and color in bpy.props.abs_plastic_materials_for_random:
                brick_mats.append(color)

    # initialize progress bar around cursor
    denom = len(keys)/1000
    if cursorStatus:
        wm = bpy.context.window_manager
        wm.progress_begin(0, 100)

    # initialize random states
    randS1 = np.random.RandomState(cm.mergeSeed) # for brickSize calc
    randS2 = np.random.RandomState(0) # for random colors, seed will be changed later
    randS3 = np.random.RandomState(cm.mergeSeed+1)
    randS4 = np.random.RandomState(cm.mergeSeed+2)
    k = 0

    mats = []
    allBrickMeshes = []
    lowestLoc = -1
    # set up internal material for this object
    internalMat = bpy.data.materials.get(cm.internalMatName)
    if internalMat is None:
        internalMat = bpy.data.materials.get("Rebrickr_%(n)s_internal" % locals())
        if internalMat is None:
            internalMat = bpy.data.materials.new("Rebrickr_%(n)s_internal" % locals())
    if cm.materialType == "Use Source Materials" and cm.matShellDepth < cm.shellThickness:
        mats.append(internalMat)
    # initialize supportBrickDs
    supportBrickDs = []
    bricksCreated = []
    keysNotChecked = keys.copy()
    if printStatus: update_progress("Building", 0.0)
    # set number of times to run through all keys
    numIters = 2 if BandP else 1
    for timeThrough in range(numIters):
        # iterate through locations in bricksDict from bottom to top
        for i,key in enumerate(keys):
            brickD = bricksDict[key]
            if brickD["draw"] and brickD["parent_brick"] in [None, "self"] and not brickD["attempted_merge"]:
                ct = time.time()
                # initialize vars
                loc = strToList(key)
                brickSizes = [[1,1,zStep]]

                # for bricks and plates, skip second and third rows on first time through
                if BandP and cm.alignBricks:
                    if timeThrough == 0: # first time
                        if lowestLoc == -1: lowestLoc = loc[2] # initializes value once
                        if (loc[2] - cm.offsetBrickLayers - lowestLoc) % 3 in [1,2]: continue
                    else: # second time
                        if (loc[2] - cm.offsetBrickLayers - lowestLoc) % 3 == 0: continue

                # attempt to merge current brick with surrounding bricks, according to available brick types
                if brickD["size"] is None or (cm.buildIsDirty):
                    preferLargest = brickD["val"] > 0 and brickD["val"] < 1
                    brickSize = attemptMerge(cm, bricksDict, key, keysNotChecked, loc, brickSizes, zStep, randS1, preferLargest=preferLargest, mergeVertical=True)
                else:
                    brickSize = brickD["size"]

                # check exposure of current [merged] brick
                if brickD["top_exposed"] is None or brickD["bot_exposed"] is None or cm.buildIsDirty:
                    topExposed, botExposed = getBrickExposure(cm, bricksDict, key, loc)
                    brickD["top_exposed"] = topExposed
                    brickD["bot_exposed"] = botExposed
                else:
                    topExposed = brickD["top_exposed"]
                    botExposed = brickD["bot_exposed"]

                # set 'logoToUse'
                logoToUse = logo if topExposed else None
                # set 'useStud'
                useStud = (topExposed and cm.studDetail != "None") or cm.studDetail == "On All Bricks"
                # set 'undersideDetail'
                undersideDetail = cm.exposedUndersideDetail if botExposed else cm.hiddenUndersideDetail
                # get brick material
                mat = getMaterial(cm, bricksDict, key, brickSize, randS2, brick_mats, k)

                ### CREATE BRICK ###

                # add brick with new mesh data at original location
                if cm.brickType == "Custom":
                    bm = bmesh.new()
                    bm.from_mesh(customData)
                    addToMeshLoc((-customObj_details.x.mid, -customObj_details.y.mid, -customObj_details.z.mid), bm=bm)

                    maxDist = max(customObj_details.x.dist, customObj_details.y.dist, customObj_details.z.dist)
                    bmesh.ops.scale(bm, vec=Vector(((R[0]-dimensions["gap"]) / customObj_details.x.dist, (R[1]-dimensions["gap"]) / customObj_details.y.dist, (R[2]-dimensions["gap"]) / customObj_details.z.dist)), verts=bm.verts)
                else:
                    # get brick mesh
                    # bm = Bricks.new_mesh(dimensions=dimensions, size=brickSize, undersideDetail=undersideDetail, logo=logoToUse, logo_details=logo_details, logo_scale=cm.logoScale, logo_inset=cm.logoInset, stud=useStud, numStudVerts=cm.studVerts)
                    bm = getBrickMesh(cm, randS4, dimensions, brickSize, undersideDetail, logoToUse, cm.logoDetail, logo_details, cm.logoScale, cm.logoInset, useStud, cm.studVerts)
                # apply random rotation to BMesh according to parameters
                if cm.randomRot > 0:
                    d = dimensions["width"]/2
                    sX = (brickSize[0] * 2) - 1
                    sY = (brickSize[1] * 2) - 1
                    center = ( ((d*sX)-d) / 2, ((d*sY)-d) / 2, 0.0 )
                    randRot = randomizeRot(randS3, center, brickSize, bm)
                # create new mesh and send bm to it
                m = bpy.data.meshes.new(brickD["name"] + 'Mesh')
                bm.to_mesh(m)
                # apply random location to edit mesh according to parameters
                if cm.randomLoc > 0:
                    randomizeLoc(randS3, dimensions["width"], dimensions["height"], mesh=m)
                if cm.brickType != "Custom":
                    # undo bm rotation if not custom, since 'bm' points to bmesh used by all other similar bricks
                    if cm.randomRot > 0:
                        rotateBack(bm, center, randRot)
                # get brick's location
                if brickSize[2] == 3 and BandP:
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

                if printStatus:
                    # print status to terminal
                    if i % denom < 1:
                        percent = i/len(keys)
                        if percent < 1:
                            update_progress("Building", percent)
                            if cursorStatus: wm.progress_update(percent*100)
            # remove key from keysNotChecked (for attemptMerge)
            try:
                keysNotChecked.remove(key)
            except:
                pass


    # remove duplicate of original logoDetail
    if cm.logoDetail != "LEGO Logo" and logo is not None:
        bpy.data.objects.remove(logo)

    if printStatus:
        update_progress("Building", 1)
    # end progress bar around cursor
    if cursorStatus: wm.progress_end()

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
        for i,key in enumerate(keys):
            if printStatus:
                # print status to terminal
                percent = i/len(bricksDict)
                if percent < 1:
                    update_progress("Linking to Scene", percent)

            if bricksDict[key]["parent_brick"] == "self" and bricksDict[key]["draw"]:
                name = bricksDict[key]["name"]
                brick = bpy.data.objects[name]
                # create vert group for bevel mod (assuming only logo verts are selected):
                vg = brick.vertex_groups.new("%(name)s_bevel" % locals())
                vertList = []
                for v in brick.data.vertices:
                    if not v.select:
                        vertList.append(v.index)
                vg.add(vertList, 1, "ADD")
                # set up remaining brick info
                bGroup.objects.link(brick)
                brick.parent = parent
                scn.objects.link(brick)
                brick.isBrick = True
        if printStatus: update_progress("Linking to Scene", 1)
    else:
        m = combineMeshes(allBrickMeshes)
        name = 'Rebrickr_%(n)s_bricks_combined' % locals()
        if frameNum: name = "%(name)s_frame_%(frameNum)s" % locals()
        allBricksObj = bpy.data.objects.new(name, m)
        allBricksObj.cmlist_id = cm.id
        # create vert group for bevel mod (assuming only logo verts are selected):
        vg = allBricksObj.vertex_groups.new("%(name)s_bevel" % locals())
        vertList = []
        for v in allBricksObj.data.vertices:
            if not v.select:
                vertList.append(v.index)
        vg.add(vertList, 1, "ADD")
        # add edge split modifier
        addEdgeSplitMod(allBricksObj)
        bGroup.objects.link(allBricksObj)
        allBricksObj.parent = parent
        if cm.materialType == "Custom":
            mat = bpy.data.materials.get(cm.materialName)
            if mat is not None:
                allBricksObj.data.materials.append(mat)
        elif cm.materialType == "Use Source Materials" or (cm.materialType == "Random" and len(brick_mats) > 0):
            for mat in mats:
                allBricksObj.data.materials.append(mat)
        scn.objects.link(allBricksObj)
        # protect allBricksObj from being deleted
        allBricksObj.isBrickifiedObject = True
        bricksCreated.append(allBricksObj)

    # reset 'attempted_merge' for all items in bricksDict
    for key0 in bricksDict: bricksDict[key0]["attempted_merge"] = False

    return bricksCreated, bricksDict
