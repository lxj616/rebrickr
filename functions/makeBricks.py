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
from ..functions import *
from ..functions.wrappers import *
from .__init__ import bounds
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
    if bm is not None:
        verts = bm.verts
    else:
        verts = mesh.vertices
    for v in verts:
        v.co = (v.co[0] + co[0], v.co[1] + co[1], v.co[2] + co[2])

def randomizeLoc(rand, width, height, bm=None, mesh=None):
    """ translate bm/mesh location by (width,width,height) randomized by cm.randomLoc """
    assert bm is not None or mesh is not None # one or the other must not be None!
    if bm is not None:
        verts = bm.verts
    else:
        verts = mesh.vertices
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
        denom = brickSize[0]*brickSize[1]
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
        scn.layers = logo.layers
        logo.hide = False
        select(logo, active=logo)
        bpy.ops.object.duplicate()
        logo = scn.objects.active
        for mod in logo.modifiers:
            mod.show_viewport = False
        logo.parent = None
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        scn.layers = oldLayers
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
    if bm_cache_string in rebrickr_bm_cache.keys():
        bms = rebrickr_bm_cache[bm_cache_string]
        if len(bms) > 1:
            bm = bms[rand.randint(0,len(bms))]
        else:
            bm = bms[0]
        return bm
    # if not found in rebrickr_bm_cache, create new brick mesh(es) and store to cache
    bms = Bricks.new_mesh(dimensions=dimensions, size=brickSize, undersideDetail=undersideDetail, logo=logoToUse, logo_type=logo_type, all_vars=logoToUse is not None, logo_details=logo_details, logo_scale=cm.logoScale, logo_inset=cm.logoInset, stud=useStud, numStudVerts=cm.studVerts)
    if logoToUse is not None and cm.brickType in ["Bricks", "Plates", "Bricks and Plates"]:
        rebrickr_bm_cache[bm_cache_string] = bms
    bm = bms[rand.randint(0,len(bms))]
    return bm

def getClosestMaterial(cm, bricksD, key, brickSize, randState, brick_mats, k):
    mat = None
    highestVal = 0
    matsL = []
    if cm.materialType == "Use Source Materials":
        for x in range(brickSize[0]):
            for y in range(brickSize[1]):
                idcs = key.split(",")
                curBrickD = bricksD[str(int(idcs[0])+x) + "," + str(int(idcs[1])+y) + "," + idcs[2]]
                if curBrickD["val"] >= highestVal:
                    highestVal = curBrickD["val"]
                    matName = curBrickD["mat_name"]
                    if curBrickD["val"] == 2:
                        matsL.append(matName)
        # if multiple shell materials, use the most frequent one
        if len(matsL) > 1:
            matName = most_common(matsL)
        mat = bpy.data.materials.get(matName)
    elif cm.materialType == "Random" and len(brick_mats) > 0:
        randState.seed(cm.randomMatSeed + k)
        k += 1
        if len(brick_mats) == 1:
            randIdx = 0
        else:
            randIdx = randState.randint(0, len(brick_mats))
        matName = brick_mats[randIdx]
        mat = bpy.data.materials.get(matName)
    return mat


@timed_call('Time Elapsed')
def makeBricks(parent, logo, dimensions, bricksD, split=False, R=None, customData=None, customObj_details=None, group_name=None, frameNum=None, cursorStatus=False, keys="ALL", createGroup=True):
    # set up variables
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    n = cm.source_name
    z1,z2,z3,z4,z5,z6,z7,z8,z9,z10,z11,z12,z13,z14,z15,z16,z17,z18,z19,z20,z21,z22,z23 = (False,)*23
    if cm.brickType in ["Bricks", "Custom"]:
        testZ = False
        bt2 = 3
    elif cm.brickType == "Plates":
        testZ = False
        bt2 = 1
    else:
        testZ = True
        bt2 = 1

    # apply transformation to logo duplicate and get bounds(logo)
    logo_details, logo = prepareLogoAndGetDetails(logo)

    # get bricksD dicts in seeded order
    if keys == "ALL":
        keys = list(bricksD.keys())
    keys.sort()
    random.seed(cm.mergeSeed)
    random.shuffle(keys)
    # sort the list by the first character only
    keys.sort(key=lambda x: int(x.split(",")[2]))

    # create group for bricks
    if group_name is not None:
        Rebrickr_bricks = group_name
    else:
        Rebrickr_bricks = 'Rebrickr_%(n)s_bricks' % locals()
    if createGroup:
        if groupExists(Rebrickr_bricks):
            bpy.data.groups.remove(group=bpy.data.groups[Rebrickr_bricks], do_unlink=True)
        bGroup = bpy.data.groups.new(Rebrickr_bricks)
    else:
        bGroup = bpy.data.groups.get(Rebrickr_bricks)


    tempMesh = bpy.data.meshes.new("tempMesh")

    if not split:
        allBrickMeshes = []

    brick_mats = []
    try:
        brick_materials_installed = scn.isBrickMaterialsInstalled
    except AttributeError:
        brick_materials_installed = False
    if cm.materialType == "Random" and brick_materials_installed:
        mats = bpy.data.materials.keys()
        for color in bpy.props.abs_plastic_materials:
            if color in mats and color in bpy.props.abs_plastic_materials_for_random:
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
    lowestRow = -1
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
    update_progress("Building", 0.0)
    for timeThrough in range(1, 3):
        # if second time through this for loop, go through keys left behind if "Bricks and Plates"
        if timeThrough == 2: # second time
            if cm.brickType == "Bricks and Plates":
                keys = keysLeftBehind
            else:
                break
        else: # first time
            keysLeftBehind = []

        # iterate through locations in bricksD from bottom to top
        for i,key in enumerate(keys):
            brickD = bricksD[key]
            if brickD["draw"] and brickD["parent_brick"] in [None, "self"]:

                # get location of brick
                loc = key.split(",")
                for j in range(len(loc)):
                    loc[j] = int(loc[j])

                # initialize lowestRow (only set for first valid brick's row)
                if lowestRow == -1:
                    lowestRow = loc[2]

                # Set up brick types
                isBrick = False
                if cm.brickType == "Bricks and Plates" and (loc[2] - lowestRow) % 3 == cm.offsetBrickLayers:
                    if plateIsBrick(brickD, bricksD, loc, 0, 0):
                        isBrick = True
                        brickSizes = [[1,1,3]]
                    else:
                        if timeThrough == 1:
                            keysLeftBehind.append(key)
                            continue
                        else:
                            brickSizes = [[1,1,1]]
                else:
                    brickSizes = [[1,1,bt2]]

                # attempt to merge current brick with surrounding bricks, according to available brick types
                if brickD["size"] is None or cm.buildIsDirty:
                    brickSize = attemptMerge(cm, bricksD, key, loc, isBrick, brickSizes, bt2, randS1)
                else:
                    brickSize = brickD["size"]

                # check exposure of current [merged] brick
                if brickD["top_exposed"] is None or brickD["bot_exposed"] is None or cm.buildIsDirty:
                    topExposed, botExposed = getBrickExposure(cm, bricksD, key, loc)
                    brickD["top_exposed"] = topExposed
                    brickD["bot_exposed"] = botExposed
                else:
                    topExposed = brickD["top_exposed"]
                    botExposed = brickD["bot_exposed"]

                # set 'logoToUse'
                if topExposed:
                    logoToUse = logo
                else:
                    logoToUse = None
                # set 'useStud'
                if (topExposed and cm.studDetail != "None") or cm.studDetail == "On All Bricks":
                    useStud = True
                else:
                    useStud = False
                # set 'undersideDetail'
                if botExposed:
                    undersideDetail = cm.exposedUndersideDetail
                else:
                    undersideDetail = cm.hiddenUndersideDetail

                # get closest material
                mat = getClosestMaterial(cm, bricksD, key, brickSize, randS2, brick_mats, k)

                # add brick with new mesh data at original location
                if split:
                    if cm.brickType == "Custom":
                        bm = bmesh.new()
                        bm.from_mesh(customData)
                        addToMeshLoc((-customObj_details.x.mid, -customObj_details.y.mid, -customObj_details.z.mid), bm=bm)
                        maxDist = max(customObj_details.x.distance, customObj_details.y.distance, customObj_details.z.distance)
                        bmesh.ops.scale(bm, vec=Vector(((R[0]-dimensions["gap"]) / customObj_details.x.distance, (R[1]-dimensions["gap"]) / customObj_details.y.distance, (R[2]-dimensions["gap"]) / customObj_details.z.distance)), verts=bm.verts)
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
                    # create new object with mesh data
                    brick = bpy.data.objects.new(brickD["name"], m)
                    brick.cmlist_id = cm.id
                    if brickSize[2] == 3 and cm.brickType == "Bricks and Plates":
                        brickLoc = Vector(brickD["co"])
                        brickLoc[2] = brickLoc[2] + dimensions["height"] + dimensions["gap"]
                    else:
                        brickLoc = Vector(brickD["co"])
                    brick.location = brickLoc
                    if cm.materialType == "Custom":
                        mat = bpy.data.materials.get(cm.materialName)
                        if mat is not None:
                            brick.data.materials.append(mat)
                    elif mat is not None:
                        brick.data.materials.append(mat)
                    else:
                        brick.data.materials.append(internalMat)

                    if cm.originSet:
                        scn.objects.link(brick)
                        select(brick)
                        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
                        select(brick, deselect=True)
                        scn.objects.unlink(brick)

                    # Add edge split modifier
                    addEdgeSplitMod(brick)
                else:
                    if cm.brickType == "Custom":
                        bm = bmesh.new()
                        bm.from_mesh(customData)
                        addToMeshLoc((-customObj_details.x.mid, -customObj_details.y.mid, -customObj_details.z.mid), bm=bm)

                        maxDist = max(customObj_details.x.distance, customObj_details.y.distance, customObj_details.z.distance)
                        bmesh.ops.scale(bm, vec=Vector(((R[0]-dimensions["gap"]) / customObj_details.x.distance, (R[1]-dimensions["gap"]) / customObj_details.y.distance, (R[2]-dimensions["gap"]) / customObj_details.z.distance)), verts=bm.verts)
                    else:
                        # get brick mesh
                        # bm = Bricks.new_mesh(dimensions=dimensions, size=brickSize, undersideDetail=undersideDetail, logo=logoToUse, logo_details=logo_details, logo_scale=cm.logoScale, logo_inset=cm.logoInset, stud=useStud, numStudVerts=cm.studVerts)
                        bm = getBrickMesh(cm, randS4, dimensions, brickSize, undersideDetail, logoToUse, cm.logoDetail, logo_details, cm.logoScale, cm.logoInset, useStud, cm.studVerts)
                    # apply random rotation to BMesh according to parameters
                    if cm.randomRot > 0:
                        d = dimensions["width"]/2
                        sX = (brickSize[0] * 2) - 1
                        sY = (brickSize[1] * 2) - 1
                        center = ( ((d*sX)-d) / 2, ((d*sY)-d) / 2, 0)
                        randRot = randomizeRot(randS3, center, brickSize, bm)
                    # create new mesh and send bm to it
                    tempMesh = bpy.data.meshes.new(brickD["name"])
                    bm.to_mesh(tempMesh)
                    # apply random location to edit mesh according to parameters
                    if cm.randomLoc > 0:
                        randomizeLoc(randS3, dimensions["width"], dimensions["height"], mesh=tempMesh)
                    if cm.brickType != "Custom":
                        # undo bm rotation if not custom, since 'bm' points to bmesh used by all other similar bricks
                        if cm.randomRot > 0:
                            rotateBack(bm, center, randRot)
                    # transform brick mesh to coordinate on matrix
                    if brickSize[2] == 3 and cm.brickType == "Bricks and Plates":
                        brickLoc = Vector(brickD["co"])
                        brickLoc[2] = brickLoc[2] + dimensions["height"] + dimensions["gap"]
                    else:
                        brickLoc = Vector(brickD["co"])
                    addToMeshLoc(brickLoc, mesh=tempMesh)
                    # set up materials for tempMesh
                    if mat in mats:
                        matIdx = mats.index(mat)
                    elif mat is not None:
                        mats.append(mat)
                        matIdx = len(mats) - 1
                    if mat is not None:
                        tempMesh.materials.append(mat)
                        for p in tempMesh.polygons:
                            p.material_index = matIdx
                    else:
                        for p in tempMesh.polygons:
                            p.material_index = 0
                    allBrickMeshes.append(tempMesh)

                # print status to terminal
                if i % denom < 1:
                    percent = i/len(keys)
                    if percent < 1:
                        update_progress("Building", percent)
                        if cursorStatus:
                            wm.progress_update(percent*100)

    # remove duplicate of original logoDetail
    if cm.logoDetail != "LEGO Logo" and logo is not None:
        bpy.data.objects.remove(logo)

    # end progress bar around cursor
    update_progress("Building", 1)
    if cursorStatus:
        wm.progress_end()

    bricksCreated = []
    # combine meshes, link to scene, and add relevant data to the new Blender MESH object
    if split:
        for i,key in enumerate(keys):
            # print status to terminal
            percent = i/len(bricksD)
            if percent < 1:
                update_progress("Linking to Scene", percent)

            if bricksD[key]["parent_brick"] == "self" and bricksD[key]["draw"]:
                name = bricksD[key]["name"]
                brick = bpy.data.objects[name]
                # create vert group for bevel mod (assuming only logo verts are selected):
                vg = brick.vertex_groups.new("%(name)s_bevel" % locals())
                vertList = []
                for v in brick.data.vertices:
                    if not v.select:
                        vertList.append(v.index)
                vg.add(vertList, 1, "ADD")
                bGroup.objects.link(brick)
                brick.parent = parent
                scn.objects.link(brick)
                brick.isBrick = True
                bricksCreated.append(brick)
        update_progress("Linking to Scene", 1)
    else:
        m = combineMeshes(allBrickMeshes)
        if frameNum:
            frameNum = str(frameNum)
            fn = "_frame_%(frameNum)s" % locals()
        else:
            fn = ""
        name = 'Rebrickr_%(n)s_bricks_combined%(fn)s' % locals()
        allBricksObj = bpy.data.objects.new(name, m)
        allBricksObj.cmlist_id = cm.id
        # create vert group for bevel mod (assuming only logo verts are selected):
        vg = allBricksObj.vertex_groups.new("%(name)s_bevel" % locals())
        vertList = []
        for v in allBricksObj.data.vertices:
            if not v.select:
                vertList.append(v.index)
        vg.add(vertList, 1, "ADD")
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

    # reset 'attempted_merge' for all items in bricksD
    for key0 in keys:
        bricksD[key0]["attempted_merge"] = False

    return bricksCreated
