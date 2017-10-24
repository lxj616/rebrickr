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
from ..functions import *
from ..functions.wrappers import *
from .__init__ import bounds
from ..lib.caches import rebrickr_bm_cache

def brickAvail(sourceBrick, brick):
    """ check brick is available to merge """
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    n = cm.source_name
    Rebrickr_internal_mn = "Rebrickr_%(n)s_internal" % locals()
    if brick is not None:
        # This if statement ensures brick is present, brick isn't connected already, and checks that brick materials match, or mergeInconsistentMats is True, or one of the mats is "" (internal)
        if brick["name"] != "DNE" and not brick["connected"] and (sourceBrick["matName"] == brick["matName"] or sourceBrick["matName"] == "" or brick["matName"] == "" or cm.mergeInconsistentMats):
            return True
    return False

def getNextBrick(bricks, loc, x, y, z=0):
    """ get next brick at loc + (x,y,z) """
    try:
        return bricks[str(loc[0] + x) + "," + str(loc[1] + y) + "," + str(loc[2] + z)]
    except KeyError:
        return None

def plateIsBrick(brickD, bricksD, loc, x, y, h=3):
    for i in range(1,h):
        if not brickAvail(brickD, getNextBrick(bricksD, loc, x, y, i)):
            return False
    return True

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

def randomizeRot(rand, center, brickType, bm):
    """ rotate 'bm' around 'center' randomized by cm.randomRot """
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    if max(brickType) == 0:
        denom = 0.75
    else:
        denom = brickType[0]*brickType[1]
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

def getBrickMesh(cm, rand, dimensions, brickType, undersideDetail, logoToUse, logo_type, logo_details, logo_scale, logo_inset, useStud, numStudVerts):
    useCaching = bpy.context.user_preferences.addons[bpy.props.rebrickr_module_name].preferences.useCaching
    if useCaching:
        # get bm_cache_string
        bm_cache_string = ""
        if cm.brickType in ["Bricks", "Plates", "Bricks and Plates"]:
            custom_logo_used = logoToUse is not None and logo_type == "Custom Logo"
            bm_cache_string = json.dumps((cm.brickHeight, brickType, undersideDetail, cm.logoResolution if logoToUse is not None else None, hash_object(logoToUse) if custom_logo_used else None, logo_scale if custom_logo_used else None, logo_inset if custom_logo_used else None, cm.studVerts if useStud else None))
        # check for bmesh in cache
        if bm_cache_string in rebrickr_bm_cache.keys():
            bms = rebrickr_bm_cache[bm_cache_string]
            if len(bms) > 1:
                bm = bms[rand.randint(0,len(bms))]
            else:
                bm = bms[0]
            return bm
    # if not found in rebrickr_bm_cache, create new brick mesh(es) and store to cache
    writeMultiple = useCaching and logoToUse is not None
    bms = Bricks.new_mesh(dimensions=dimensions, type=brickType, undersideDetail=undersideDetail, logo=logoToUse, logo_type=logo_type, all_vars=writeMultiple, logo_details=logo_details, logo_scale=cm.logoScale, logo_inset=cm.logoInset, stud=useStud, numStudVerts=cm.studVerts)
    if useCaching and cm.brickType in ["Bricks", "Plates", "Bricks and Plates"]:
        rebrickr_bm_cache[bm_cache_string] = bms
    bm = bms[rand.randint(0,len(bms))]
    return bm

@timed_call('Time Elapsed')
def makeBricks(parent, logo, dimensions, bricksD, split=False, R=None, customData=None, customObj_details=None, group_name=None, frameNum=None, cursorStatus=False):
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

    # get brick dicts in seeded order
    keysOrig = list(bricksD.keys())
    keysOrig.sort()
    random.seed(cm.mergeSeed)
    random.shuffle(keysOrig)
    # init new keys list
    keys = []
    # split the keys into lists and convert to integers
    for i in range(len(keysOrig)):
        curKeyL = keysOrig[i].split(",")
        keys[int(curKeyL[0])][int(curKeyL[1])][int(curKeyL[2])]


    # sort the list by the first character only
    keys.sort(key=lambda x: x[2])

    # create group for bricks
    if group_name:
        Rebrickr_bricks = group_name
    else:
        Rebrickr_bricks = 'Rebrickr_%(n)s_bricks' % locals()
    if groupExists(Rebrickr_bricks):
        bpy.data.groups.remove(group=bpy.data.groups[Rebrickr_bricks], do_unlink=True)
    bGroup = bpy.data.groups.new(Rebrickr_bricks)

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
    randS1 = np.random.RandomState(cm.mergeSeed) # for brickType calc
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
    # iterate through locations in bricksD from bottom to top
    for i,key in enumerate(keys):
        ct = time.time()
        brickD = bricksD[key]
        if brickD["name"] != "DNE" and not brickD["connected"]:
            loc = key.split(",")
            for j in range(len(loc)):
                loc[j] = int(loc[j])
            if lowestRow == -1:
                lowestRow = loc[2]

            # Set up brick types
            isBrick = False
            if cm.brickType == "Bricks and Plates" and (loc[2] - lowestRow) % 3 == cm.offsetBrickLayers:
                if plateIsBrick(brickD, bricksD, loc, 0, 0):
                    isBrick = True
                    brickTypes = [[1,1,3]]
                else:

                    brickTypes = [[1,1,1]]
            else:
                brickTypes = [[1,1,bt2]]
            nextBrick0 = getNextBrick(bricksD, loc, 1, 0)
            canBeBrick = not isBrick or plateIsBrick(brickD, bricksD, loc, 1, 0)
            if brickAvail(brickD, nextBrick0) and canBeBrick and cm.maxBrickScale1 > 1 and cm.brickType != "Custom":
                nextBrick = getNextBrick(bricksD, loc, 2, 0)
                canBeBrick = not isBrick or plateIsBrick(brickD, bricksD, loc, 2, 0)
                if brickAvail(brickD, nextBrick) and canBeBrick and cm.maxBrickScale1 > 2:
                    if isBrick:
                        brickTypes.append([3,1,3])
                    else:
                        brickTypes.append([3,1,bt2])
                    nextBrick = getNextBrick(bricksD, loc, 3, 0)
                    canBeBrick = not isBrick or plateIsBrick(brickD, bricksD, loc, 3, 0)
                    if brickAvail(brickD, nextBrick) and canBeBrick and cm.maxBrickScale1 > 3:
                        if isBrick:
                            brickTypes.append([4,1,3])
                        else:
                            brickTypes.append([4,1,bt2])
                        nextBrick0 = getNextBrick(bricksD, loc, 4, 0)
                        nextBrick1 = getNextBrick(bricksD, loc, 5, 0)
                        canBeBrick = not isBrick or plateIsBrick(brickD, bricksD, loc, 4, 0) and plateIsBrick(brickD, bricksD, loc, 5, 0)
                        if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and canBeBrick and cm.maxBrickScale1 > 5:
                            if isBrick:
                                brickTypes.append([6,1,3])
                            else:
                                brickTypes.append([6,1,bt2])
                            nextBrick0 = getNextBrick(bricksD, loc, 6, 0)
                            nextBrick1 = getNextBrick(bricksD, loc, 7, 0)
                            canBeBrick = not isBrick or plateIsBrick(brickD, bricksD, loc, 6, 0) and plateIsBrick(brickD, bricksD, loc, 7, 0)
                            if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and canBeBrick and cm.maxBrickScale1 > 7:
                                if isBrick:
                                    brickTypes.append([8,1,3])
                                else:
                                    brickTypes.append([8,1,bt2])
            nextBrick1 = getNextBrick(bricksD, loc, 0, 1)
            canBeBrick = not isBrick or plateIsBrick(brickD, bricksD, loc, 0, 1)
            if brickAvail(brickD, nextBrick1) and canBeBrick and cm.maxBrickScale1 > 1 and cm.brickType != "Custom":
                if isBrick:
                    brickTypes.append([1,2,3])
                else:
                    brickTypes.append([1,2,bt2])
                nextBrick = getNextBrick(bricksD, loc, 0, 2)
                canBeBrick = not isBrick or plateIsBrick(brickD, bricksD, loc, 0, 2)
                if brickAvail(brickD, nextBrick) and canBeBrick and cm.maxBrickScale1 > 2:
                    if isBrick:
                        brickTypes.append([1,3,3])
                    else:
                        brickTypes.append([1,3,bt2])
                    nextBrick = getNextBrick(bricksD, loc, 0, 3)
                    canBeBrick = not isBrick or plateIsBrick(brickD, bricksD, loc, 0, 3)
                    if brickAvail(brickD, nextBrick) and canBeBrick and cm.maxBrickScale1 > 3:
                        if isBrick:
                            brickTypes.append([1,4,3])
                        else:
                            brickTypes.append([1,4,bt2])
                        nextBrick0 = getNextBrick(bricksD, loc, 0, 4)
                        nextBrick1 = getNextBrick(bricksD, loc, 0, 5)
                        canBeBrick = not isBrick or (plateIsBrick(brickD, bricksD, loc, 0, 4) and plateIsBrick(brickD, bricksD, loc, 0, 5))
                        if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and canBeBrick and cm.maxBrickScale1 > 5:
                            if isBrick:
                                brickTypes.append([1,6,3])
                            else:
                                brickTypes.append([1,6,bt2])
                            nextBrick0 = getNextBrick(bricksD, loc, 0, 6)
                            nextBrick1 = getNextBrick(bricksD, loc, 0, 7)
                            canBeBrick = not isBrick or (plateIsBrick(brickD, bricksD, loc, 0, 6) and plateIsBrick(brickD, bricksD, loc, 0, 7))
                            if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and canBeBrick and cm.maxBrickScale1 > 7:
                                if isBrick:
                                    brickTypes.append([1,8,3])
                                else:
                                    brickTypes.append([1,8,bt2])
            nextBrick2 = getNextBrick(bricksD, loc, 1, 1)
            canBeBrick = not isBrick or plateIsBrick(brickD, bricksD, loc, 1, 1)
            if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and brickAvail(brickD, nextBrick2) and canBeBrick and cm.maxBrickScale2 > 1 and cm.brickType != "Custom":
                if isBrick:
                    brickTypes.append([2,2,3])
                else:
                    brickTypes.append([2,2,bt2])
                nextBrick0 = getNextBrick(bricksD, loc, 0, 2)
                nextBrick1 = getNextBrick(bricksD, loc, 1, 2)
                canBeBrick = not isBrick or (plateIsBrick(brickD, bricksD, loc, 0, 2) and plateIsBrick(brickD, bricksD, loc, 1, 2))
                if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and canBeBrick and cm.maxBrickScale2 > 2:
                    if isBrick:
                        brickTypes.append([2,3,3])
                    else:
                        brickTypes.append([2,3,bt2])
                    nextBrick0 = getNextBrick(bricksD, loc, 0, 3)
                    nextBrick1 = getNextBrick(bricksD, loc, 1, 3)
                    canBeBrick = not isBrick or (plateIsBrick(brickD, bricksD, loc, 0, 3) and plateIsBrick(brickD, bricksD, loc, 1, 3))
                    if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and canBeBrick and cm.maxBrickScale2 > 3:
                        if isBrick:
                            brickTypes.append([2,4,3])
                        else:
                            brickTypes.append([2,4,bt2])
                        nextBrick0 = getNextBrick(bricksD, loc, 0, 4)
                        nextBrick1 = getNextBrick(bricksD, loc, 1, 4)
                        nextBrick2 = getNextBrick(bricksD, loc, 0, 5)
                        nextBrick3 = getNextBrick(bricksD, loc, 1, 5)
                        canBeBrick = not isBrick or (plateIsBrick(brickD, bricksD, loc, 0, 4) and plateIsBrick(brickD, bricksD, loc, 1, 4) and plateIsBrick(brickD, bricksD, loc, 0, 5) and plateIsBrick(brickD, bricksD, loc, 1, 5))
                        if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and brickAvail(brickD, nextBrick2) and brickAvail(brickD, nextBrick3) and canBeBrick and cm.maxBrickScale2 > 5:
                            if isBrick:
                                brickTypes.append([2,6,3])
                            else:
                                brickTypes.append([2,6,bt2])
                            nextBrick0 = getNextBrick(bricksD, loc, 0, 6)
                            nextBrick1 = getNextBrick(bricksD, loc, 1, 6)
                            nextBrick2 = getNextBrick(bricksD, loc, 0, 7)
                            nextBrick3 = getNextBrick(bricksD, loc, 1, 7)
                            canBeBrick = not isBrick or (plateIsBrick(brickD, bricksD, loc, 0, 6) and plateIsBrick(brickD, bricksD, loc, 1, 6) and plateIsBrick(brickD, bricksD, loc, 0, 7) and plateIsBrick(brickD, bricksD, loc, 1, 7))
                            if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and brickAvail(brickD, nextBrick2) and brickAvail(brickD, nextBrick3) and canBeBrick and cm.maxBrickScale2 > 7:
                                if isBrick:
                                    brickTypes.append([2,8,3])
                                else:
                                    brickTypes.append([2,8,bt2])
                                nextBrick0 = getNextBrick(bricksD, loc, 0, 8)
                                nextBrick1 = getNextBrick(bricksD, loc, 1, 8)
                                nextBrick2 = getNextBrick(bricksD, loc, 0, 9)
                                nextBrick3 = getNextBrick(bricksD, loc, 1, 9)
                                canBeBrick = not isBrick or (plateIsBrick(brickD, bricksD, loc, 0, 8) and plateIsBrick(brickD, bricksD, loc, 1, 8) and plateIsBrick(brickD, bricksD, loc, 0, 9) and plateIsBrick(brickD, bricksD, loc, 1, 9))
                                if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and brickAvail(brickD, nextBrick2) and brickAvail(brickD, nextBrick3) and canBeBrick and cm.maxBrickScale2 > 9:
                                    if isBrick:
                                        brickTypes.append([2,10,3])
                                    else:
                                        brickTypes.append([2,10,bt2])
                nextBrick0 = getNextBrick(bricksD, loc, 2, 0)
                nextBrick1 = getNextBrick(bricksD, loc, 2, 1)
                canBeBrick = not isBrick or (plateIsBrick(brickD, bricksD, loc, 2, 0) and plateIsBrick(brickD, bricksD, loc, 2, 1))
                if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and canBeBrick and cm.maxBrickScale2 > 2:
                    if isBrick:
                        brickTypes.append([3,2,3])
                    else:
                        brickTypes.append([3,2,bt2])
                    nextBrick0 = getNextBrick(bricksD, loc, 3, 0)
                    nextBrick1 = getNextBrick(bricksD, loc, 3, 1)
                    canBeBrick = not isBrick or (plateIsBrick(brickD, bricksD, loc, 3, 0) and plateIsBrick(brickD, bricksD, loc, 3, 1))
                    if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and canBeBrick and cm.maxBrickScale2 > 3:
                        if isBrick:
                            brickTypes.append([4,2,3])
                        else:
                            brickTypes.append([4,2,bt2])
                        nextBrick0 = getNextBrick(bricksD, loc, 4, 0)
                        nextBrick1 = getNextBrick(bricksD, loc, 4, 1)
                        nextBrick2 = getNextBrick(bricksD, loc, 5, 0)
                        nextBrick3 = getNextBrick(bricksD, loc, 5, 1)
                        canBeBrick = not isBrick or (plateIsBrick(brickD, bricksD, loc, 4, 0) and plateIsBrick(brickD, bricksD, loc, 4, 1) and plateIsBrick(brickD, bricksD, loc, 5, 0) and plateIsBrick(brickD, bricksD, loc, 5, 1))
                        if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and brickAvail(brickD, nextBrick2) and brickAvail(brickD, nextBrick3) and canBeBrick and cm.maxBrickScale2 > 5:
                            if isBrick:
                                brickTypes.append([6,2,3])
                            else:
                                brickTypes.append([6,2,bt2])
                            nextBrick0 = getNextBrick(bricksD, loc, 6, 0)
                            nextBrick1 = getNextBrick(bricksD, loc, 6, 1)
                            nextBrick2 = getNextBrick(bricksD, loc, 7, 0)
                            nextBrick3 = getNextBrick(bricksD, loc, 7, 1)
                            canBeBrick = not isBrick or (plateIsBrick(brickD, bricksD, loc, 6, 0) and plateIsBrick(brickD, bricksD, loc, 6, 1) and plateIsBrick(brickD, bricksD, loc, 7, 0) and plateIsBrick(brickD, bricksD, loc, 7, 1))
                            if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and brickAvail(brickD, nextBrick2) and brickAvail(brickD, nextBrick3) and canBeBrick and cm.maxBrickScale2 > 7:
                                if isBrick:
                                    brickTypes.append([8,2,3])
                                else:
                                    brickTypes.append([8,2,bt2])
                                nextBrick0 = getNextBrick(bricksD, loc, 8, 0)
                                nextBrick1 = getNextBrick(bricksD, loc, 8, 1)
                                nextBrick2 = getNextBrick(bricksD, loc, 9, 0)
                                nextBrick3 = getNextBrick(bricksD, loc, 9, 1)
                                canBeBrick = not isBrick or (plateIsBrick(brickD, bricksD, loc, 8, 0) and plateIsBrick(brickD, bricksD, loc, 8, 1) and plateIsBrick(brickD, bricksD, loc, 9, 0) and plateIsBrick(brickD, bricksD, loc, 9, 1))
                                if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and brickAvail(brickD, nextBrick2) and brickAvail(brickD, nextBrick3) and canBeBrick and cm.maxBrickScale2 > 9:
                                    if isBrick:
                                        brickTypes.append([10,2,3])
                                    else:
                                        brickTypes.append([10,2,bt2])

            # sort brick types from smallest to largest
            order = randS1.randint(1,2)
            if cm.brickType == "Bricks and Plates":
                brickTypes.sort(key=lambda x: (x[2], x[order-1]))
            else:
                brickTypes.sort(key=lambda x: x[order-1])
            # grab the biggest brick type
            brickType = brickTypes[-1]

            topExposed = False
            botExposed = False

            # Iterate through merged bricks
            idxZb = str(loc[2] - 1)
            if cm.brickType == "Bricks and Plates" and brickType[2] == 3:
                idxZa = str(loc[2] + 3)
            else:
                idxZa = str(loc[2] + 1)
            for x in range(brickType[0]):
                idxX = str(loc[0] + x)
                for y in range(brickType[1]):
                    idxY = str(loc[1] + y)
                    for z in range(brickType[2]):
                        if cm.brickType in ["Bricks", "Custom"] and z > 0:
                            continue
                        idxZ = str(loc[2] + z)
                        # get brick at x,y location
                        curBrick = bricksD["%(idxX)s,%(idxY)s,%(idxZ)s" % locals()]
                        # check if brick top or bottom is exposed
                        if curBrick["val"] == 2 and z == 0:
                            try:
                                valKeysChecked1 = []
                                val = bricksD["%(idxX)s,%(idxY)s,%(idxZa)s" % locals()]["val"]
                                if val == 0:
                                    topExposed = True
                                # Check bricks on Z axis above this brick until shell (2) hit. If ouside (0) hit first, top is exposed
                                elif val < 1 and val > 0:
                                    idxZab = idxZa
                                    while val < 1 and val > 0:
                                        idxZab = str(int(idxZab)+1)
                                        # NOTE: if key does not exist, we will be sent to 'except'
                                        valKeysChecked1.append("%(idxX)s,%(idxY)s,%(idxZab)s" % locals())
                                        val = bricksD[valKeysChecked1[-1]]["val"]
                                        if val == 0:
                                            topExposed = True
                            except KeyError:
                                topExposed = True
                            # if outside (0) hit before shell (2) above exposed brick, set all inside (0 < x < 1) values in-between to ouside (0)
                            if topExposed and len(valKeysChecked1) > 0:
                                for k in valKeysChecked1:
                                    val = bricksD[k]["val"] = 0

                            try:
                                valKeysChecked2 = []
                                val = bricksD["%(idxX)s,%(idxY)s,%(idxZb)s" % locals()]["val"]
                                if val == 0:
                                    botExposed = True
                                # Check bricks on Z axis below this brick until shell (2) hit. If ouside (0) hit first, bottom is exposed
                                elif val < 1 and val > 0:
                                    idxZbb = idxZb
                                    while val < 1 and val > 0:
                                        idxZbb = str(int(idxZbb)+1)
                                        # NOTE: if key does not exist, we will be sent to 'except'
                                        valKeysChecked2.append("%(idxX)s,%(idxY)s,%(idxZbb)s" % locals())
                                        val = bricksD[valKeysChecked2[-1]]["val"]
                                        if val == 0:
                                            botExposed = True
                            except KeyError:
                                botExposed = True
                            # if outside (0) hit before shell (2) below exposed brick, set all inside (0 < x < 1) values in-between to ouside (0)
                            if botExposed and len(valKeysChecked2) > 0:
                                for k in valKeysChecked2:
                                    val = bricksD[k]["val"] = 0
                        # skip the original brick
                        if (x + y + z) == 0: # checks that x,y,z are all 0
                            brickD["connected"] = True
                            continue
                        # add brick to connected bricks
                        curBrick["connected"] = True
                        # set name of deleted brick to 'DNE'
                        curBrick["name"] = "DNE"


            if topExposed:
                logoToUse = logo
            else:
                logoToUse = None
            if (topExposed and cm.studDetail != "None") or cm.studDetail == "On All Bricks":
                useStud = True
            else:
                useStud = False
            if botExposed:
                undersideDetail = cm.exposedUndersideDetail
            else:
                undersideDetail = cm.hiddenUndersideDetail

            # get closest material
            mat = None
            highestVal = 0
            matsL = []
            if cm.materialType == "Use Source Materials":
                for x in range(brickType[0]):
                    for y in range(brickType[1]):
                        idcs = key.split(",")
                        curBrickD = bricksD[str(int(idcs[0])+x) + "," + str(int(idcs[1])+y) + "," + idcs[2]]
                        if curBrickD["val"] >= highestVal:
                            highestVal = curBrickD["val"]
                            matName = curBrickD["matName"]
                            if curBrickD["val"] == 2:
                                matsL.append(matName)
                # if multiple shell materials, use the most frequent one
                if len(matsL) > 1:
                    matName = most_common(matsL)
                mat = bpy.data.materials.get(matName)
            elif cm.materialType == "Random" and len(brick_mats) > 0:
                randS2.seed(cm.randomMatSeed + k)
                k += 1
                if len(brick_mats) == 1:
                    randIdx = 0
                else:
                    randIdx = randS2.randint(0, len(brick_mats))
                matName = brick_mats[randIdx]
                mat = bpy.data.materials.get(matName)

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
                    # bm = Bricks.new_mesh(dimensions=dimensions, type=brickType, undersideDetail=undersideDetail, logo=logoToUse, logo_details=logo_details, logo_scale=cm.logoScale, logo_inset=cm.logoInset, stud=useStud, numStudVerts=cm.studVerts)
                    bm = getBrickMesh(cm, randS4, dimensions, brickType, undersideDetail, logoToUse, cm.logoDetail, logo_details, cm.logoScale, cm.logoInset, useStud, cm.studVerts)
                # apply random rotation to BMesh according to parameters
                if cm.randomRot > 0:
                    d = dimensions["width"]/2
                    sX = (brickType[0] * 2) - 1
                    sY = (brickType[1] * 2) - 1
                    center = ( ((d*sX)-d) / 2, ((d*sY)-d) / 2, 0.0 )
                    randRot = randomizeRot(randS3, center, brickType, bm)
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
                if brickType[2] == 3 and cm.brickType == "Bricks and Plates":
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
                    # bm = Bricks.new_mesh(dimensions=dimensions, type=brickType, undersideDetail=undersideDetail, logo=logoToUse, logo_details=logo_details, logo_scale=cm.logoScale, logo_inset=cm.logoInset, stud=useStud, numStudVerts=cm.studVerts)
                    bm = getBrickMesh(cm, randS4, dimensions, brickType, undersideDetail, logoToUse, cm.logoDetail, logo_details, cm.logoScale, cm.logoInset, useStud, cm.studVerts)
                # apply random rotation to BMesh according to parameters
                if cm.randomRot > 0:
                    d = dimensions["width"]/2
                    sX = (brickType[0] * 2) - 1
                    sY = (brickType[1] * 2) - 1
                    center = ( ((d*sX)-d) / 2, ((d*sY)-d) / 2, 0)
                    randRot = randomizeRot(randS3, center, brickType, bm)
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
                if brickType[2] == 3 and cm.brickType == "Bricks and Plates":
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

    # combine meshes, link to scene, and add relevant data to the new Blender MESH object
    if split:
        for i,key in enumerate(bricksD):
            # print status to terminal
            percent = i/len(bricksD)
            if percent < 1:
                update_progress("Linking to Scene", percent)
            if bricksD[key]["name"] != "DNE":
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
