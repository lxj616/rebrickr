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

# system imports
import bpy
import bmesh
import math
import time
import sys
import random
from mathutils import Vector, Matrix
from ..classes.Brick import Bricks
from ..functions import *
from ..functions.wrappers import *
from .__init__ import bounds

def brickAvail(sourceBrick, brick):
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    n = cm.source_name
    Rebrickr_internal_mn = "Rebrickr_%(n)s_internal" % locals()
    if brick != None:
        # This if statement ensures brick is present, brick isn't connected already, and checks that brick materials match, or mergeInconsistentMats is True, or one of the mats is "" (internal)
        if brick["name"] != "DNE" and not brick["connected"] and (sourceBrick["matName"] == brick["matName"] or sourceBrick["matName"] == "" or brick["matName"] == "" or cm.mergeInconsistentMats):
            return True
    return False

def getNextBrick(bricks, loc, x, y, z=0):
    try:
        return bricks[str(loc[0] + x) + "," + str(loc[1] + y) + "," + str(loc[2] + z)]
    except:
        return None

def addEdgeSplitMod(obj):
    """ Add edge split modifier """
    eMod = obj.modifiers.new('Edge Split', 'EDGE_SPLIT')

def combineMeshes(meshes):
    bm = bmesh.new()
    # add meshes to bmesh
    for m in meshes:
        bm.from_mesh( m )
    finalMesh = bpy.data.meshes.new( "newMesh" )
    bm.to_mesh( finalMesh )
    return finalMesh

def randomizeLoc(width, height, bm):
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    x = random.uniform(-(width/2) * cm.randomLoc, (width/2) * cm.randomLoc)
    y = random.uniform(-(width/2) * cm.randomLoc, (width/2) * cm.randomLoc)
    z = random.uniform(-(height/2) * cm.randomLoc, (height/2) * cm.randomLoc)
    for v in bm.verts:
        v.co.x += x
        v.co.y += y
        v.co.z += z


def randomizeRot(center, brickType, bm):
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    if max(brickType) == 0:
        denom = 0.75
    else:
        denom = brickType[0]*brickType[1]
    x=random.uniform(-0.1963495 * cm.randomRot / denom, 0.1963495 * cm.randomRot / denom)
    y=random.uniform(-0.1963495 * cm.randomRot / denom, 0.1963495 * cm.randomRot / denom)
    z=random.uniform(-0.785398 * cm.randomRot / denom, 0.785398 * cm.randomRot / denom)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=center, matrix=Matrix.Rotation(x, 3, 'X'))
    bmesh.ops.rotate(bm, verts=bm.verts, cent=center, matrix=Matrix.Rotation(y, 3, 'Y'))
    bmesh.ops.rotate(bm, verts=bm.verts, cent=center, matrix=Matrix.Rotation(z, 3, 'Z'))

def prepareLogoAndGetDetails(logo):
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

@timed_call('Time Elapsed')
def makeBricks(parent, logo, dimensions, bricksD, split=False, R=None, customData=None, customObj_details=None, group_name=None, frameNum=None, cursorStatus=False):
    # set up variables
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    n = cm.source_name
    z1,z2,z3,z4,z5,z6,z7,z8,z9,z10,z11,z12,z13,z14,z15,z16,z17,z18,z19,z20,z21,z22,z23 = (False,)*23
    if cm.brickType in ["Bricks", 'Custom']:
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
    keys = list(bricksD.keys())
    random.seed(a=cm.mergeSeed)
    random.shuffle(keys)

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
    if cm.materialType == "Random" and "brick_materials" in bpy.context.user_preferences.addons.keys():
        mats = bpy.data.materials.keys()
        for color in bpy.props.brick_materials:
            if color in mats and color in bpy.props.brick_materials_for_random:
                brick_mats.append(color)

    # initialize progress bar around cursor
    denom = len(keys)/1000
    if cursorStatus:
        wm = bpy.context.window_manager
        wm.progress_begin(0, 100)

    mats = []
    # set up internal material for this object
    if cm.materialType == "Use Source Materials" and cm.matShellDepth < cm.shellThickness:
        internalMat = bpy.data.materials.get(cm.internalMatName)
        if internalMat is None:
            internalMat = bpy.data.materials.get("Rebrickr_%(n)s_internal" % locals())
            if internalMat is None:
                internalMat = bpy.data.materials.new("Rebrickr_%(n)s_internal" % locals())
        mats.append(internalMat)
    # initialize supportBrickDs
    supportBrickDs = []
    update_progress("Building", 0.0)
    for i,key in enumerate(keys):
        brickD = bricksD[key]
        if brickD["name"] != "DNE" and not brickD["connected"]:
            loc = key.split(",")
            for i in range(len(loc)):
                loc[i] = int(loc[i])

            # Set up brick types
            brickTypes = [[1,1,bt2]]
            nextBrick = getNextBrick(bricksD, loc, 1, 0)
            if brickAvail(brickD, nextBrick) and cm.maxBrickScale1 > 1 and cm.brickType != "Custom":
                brickTypes.append([2,1,bt2])
                nextBrick = getNextBrick(bricksD, loc, 2, 0)
                if brickAvail(brickD, nextBrick) and cm.maxBrickScale1 > 2:
                    brickTypes.append([3,1,bt2])
                    nextBrick = getNextBrick(bricksD, loc, 3, 0)
                    if brickAvail(brickD, nextBrick) and cm.maxBrickScale1 > 3:
                        brickTypes.append([4,1,bt2])
                        nextBrick0 = getNextBrick(bricksD, loc, 4, 0)
                        nextBrick1 = getNextBrick(bricksD, loc, 5, 0)
                        if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and cm.maxBrickScale1 > 5:
                            brickTypes.append([6,1,bt2])
                            nextBrick0 = getNextBrick(bricksD, loc, 6, 0)
                            nextBrick1 = getNextBrick(bricksD, loc, 7, 0)
                            if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and cm.maxBrickScale1 > 7:
                                brickTypes.append([8,1,bt2])
            nextBrick = getNextBrick(bricksD, loc, 0, 1)
            if brickAvail(brickD, nextBrick) and cm.maxBrickScale1 > 1 and cm.brickType != "Custom":
                brickTypes.append([1,2,bt2])
                nextBrick = getNextBrick(bricksD, loc, 0, 2)
                if brickAvail(brickD, nextBrick) and cm.maxBrickScale1 > 2:
                    brickTypes.append([1,3,bt2])
                    nextBrick = getNextBrick(bricksD, loc, 0, 3)
                    if brickAvail(brickD, nextBrick) and cm.maxBrickScale1 > 3:
                        brickTypes.append([1,4,bt2])
                        nextBrick0 = getNextBrick(bricksD, loc, 0, 4)
                        nextBrick1 = getNextBrick(bricksD, loc, 0, 5)
                        if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and cm.maxBrickScale1 > 5:
                            brickTypes.append([1,6,bt2])
                            nextBrick0 = getNextBrick(bricksD, loc, 0, 6)
                            nextBrick1 = getNextBrick(bricksD, loc, 0, 7)
                            if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and cm.maxBrickScale1 > 7:
                                brickTypes.append([1,8,bt2])
            nextBrick0 = getNextBrick(bricksD, loc, 0, 1)
            nextBrick1 = getNextBrick(bricksD, loc, 1, 0)
            nextBrick2 = getNextBrick(bricksD, loc, 1, 1)
            if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and brickAvail(brickD, nextBrick2) and cm.maxBrickScale2 > 1 and cm.brickType != "Custom":
                brickTypes.append([2,2,bt2])
                nextBrick0 = getNextBrick(bricksD, loc, 0, 2)
                nextBrick1 = getNextBrick(bricksD, loc, 1, 2)
                if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and cm.maxBrickScale2 > 2:
                    brickTypes.append([2,3,bt2])
                    nextBrick0 = getNextBrick(bricksD, loc, 0, 3)
                    nextBrick1 = getNextBrick(bricksD, loc, 1, 3)
                    if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and cm.maxBrickScale2 > 3:
                        brickTypes.append([2,4,bt2])
                        nextBrick0 = getNextBrick(bricksD, loc, 0, 4)
                        nextBrick1 = getNextBrick(bricksD, loc, 1, 4)
                        nextBrick2 = getNextBrick(bricksD, loc, 0, 5)
                        nextBrick3 = getNextBrick(bricksD, loc, 1, 5)
                        if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and brickAvail(brickD, nextBrick2) and brickAvail(brickD, nextBrick3) and cm.maxBrickScale2 > 5:
                            brickTypes.append([2,6,bt2])
                            nextBrick0 = getNextBrick(bricksD, loc, 0, 6)
                            nextBrick1 = getNextBrick(bricksD, loc, 1, 6)
                            nextBrick2 = getNextBrick(bricksD, loc, 0, 7)
                            nextBrick3 = getNextBrick(bricksD, loc, 1, 7)
                            if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and brickAvail(brickD, nextBrick2) and brickAvail(brickD, nextBrick3) and cm.maxBrickScale2 > 7:
                                brickTypes.append([2,8,bt2])
                                nextBrick0 = getNextBrick(bricksD, loc, 0, 8)
                                nextBrick1 = getNextBrick(bricksD, loc, 1, 8)
                                nextBrick2 = getNextBrick(bricksD, loc, 0, 9)
                                nextBrick3 = getNextBrick(bricksD, loc, 1, 9)
                                if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and brickAvail(brickD, nextBrick2) and brickAvail(brickD, nextBrick3) and cm.maxBrickScale2 > 9:
                                    brickTypes.append([2,10,bt2])
                nextBrick0 = getNextBrick(bricksD, loc, 2, 0)
                nextBrick1 = getNextBrick(bricksD, loc, 2, 1)
                if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and cm.maxBrickScale2 > 2:
                    brickTypes.append([3,2,bt2])
                    nextBrick0 = getNextBrick(bricksD, loc, 3, 0)
                    nextBrick1 = getNextBrick(bricksD, loc, 3, 1)
                    if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and cm.maxBrickScale2 > 3:
                        brickTypes.append([4,2,bt2])
                        nextBrick0 = getNextBrick(bricksD, loc, 4, 0)
                        nextBrick1 = getNextBrick(bricksD, loc, 4, 1)
                        nextBrick2 = getNextBrick(bricksD, loc, 5, 0)
                        nextBrick3 = getNextBrick(bricksD, loc, 5, 1)
                        if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and brickAvail(brickD, nextBrick2) and brickAvail(brickD, nextBrick3) and cm.maxBrickScale2 > 5:
                            brickTypes.append([6,2,bt2])
                            nextBrick0 = getNextBrick(bricksD, loc, 6, 0)
                            nextBrick1 = getNextBrick(bricksD, loc, 6, 1)
                            nextBrick2 = getNextBrick(bricksD, loc, 7, 0)
                            nextBrick3 = getNextBrick(bricksD, loc, 7, 1)
                            if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and brickAvail(brickD, nextBrick2) and brickAvail(brickD, nextBrick3) and cm.maxBrickScale2 > 7:
                                brickTypes.append([8,2,bt2])
                                nextBrick0 = getNextBrick(bricksD, loc, 8, 0)
                                nextBrick1 = getNextBrick(bricksD, loc, 8, 1)
                                nextBrick2 = getNextBrick(bricksD, loc, 9, 0)
                                nextBrick3 = getNextBrick(bricksD, loc, 9, 1)
                                if brickAvail(brickD, nextBrick0) and brickAvail(brickD, nextBrick1) and brickAvail(brickD, nextBrick2) and brickAvail(brickD, nextBrick3) and cm.maxBrickScale2 > 9:
                                    brickTypes.append([10,2,bt2])

            # sort brick types from smallest to largest
            order = random.randint(1,2)
            if order == 2:
                for idx in range(len(brickTypes)):
                    brickTypes[idx] = brickTypes[idx][::-1]
            brickTypes.sort()

            brickType = brickTypes[-1]
            if order == 2:
                brickType = brickType[::-1]

            topExposed = False
            botExposed = False

            # Iterate through merged bricks
            idxZa = str(loc[2] + 1)
            idxZb = str(loc[2] - 1)
            idxZc = str(loc[2])
            for x in range(brickType[0]):
                for y in range(brickType[1]):
                    idxX = str(loc[0] + x)
                    idxY = str(loc[1] + y)

                    # get brick at x,y location
                    curBrick = bricksD["%(idxX)s,%(idxY)s,%(idxZc)s" % locals()]

                    if curBrick["val"] == 2:
                        # check if brick top or bottom is exposed
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
                        except:
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
                        except:
                            botExposed = True
                        # if outside (0) hit before shell (2) below exposed brick, set all inside (0 < x < 1) values in-between to ouside (0)
                        if botExposed and len(valKeysChecked2) > 0:
                            for k in valKeysChecked2:
                                val = bricksD[k]["val"] = 0
                    # skip the original brick
                    if x == 0 and y == 0:
                        brickD["connected"] = True
                        continue
                    # add brick to connected bricks
                    curBrick["connected"] = True
                    # set name of deleted brick to 'DNE'
                    curBrick["name"] = "DNE"

            if topExposed:
                logoDetail = logo
            else:
                logoDetail = None
            if (topExposed and cm.studDetail != "None") or cm.studDetail == "On All Bricks":
                studDetail = True
            else:
                studDetail = False
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
                randIdx = random.randint(0, len(brick_mats)-1)
                matName = brick_mats[randIdx]
                mat = bpy.data.materials.get(matName)

            # add brick with new mesh data at original location
            if split:
                if cm.brickType == "Custom":
                    bm = bmesh.new()
                    bm.from_mesh(customData)
                    for v in bm.verts:
                        v.co = (v.co[0] - customObj_details.x.mid, v.co[1] - customObj_details.y.mid, v.co[2] - customObj_details.z.mid)
                    maxDist = max(customObj_details.x.distance, customObj_details.y.distance, customObj_details.z.distance)
                    bmesh.ops.scale(bm, vec=Vector(((R[0]-dimensions["gap"]) / customObj_details.x.distance, (R[1]-dimensions["gap"]) / customObj_details.y.distance, (R[2]-dimensions["gap"]) / customObj_details.z.distance)), verts=bm.verts)
                    # for v in bm.verts:
                    #     v.co = (v.co[0] + brickD["co"][0], v.co[1] + brickD["co"][1], v.co[2] + brickD["co"][2])
                    m = bpy.data.meshes.new(brickD["name"])
                    bm.to_mesh(m)
                else:
                    # create new brick mesh
                    bm = Bricks.new_mesh(dimensions=dimensions, name=brickD["name"], gap_percentage=cm.gap, type=brickType, undersideDetail=undersideDetail, logo=logoDetail, logo_details=logo_details, stud=studDetail, returnType="bmesh")
                    # create new mesh
                    m = bpy.data.meshes.new(brickD["name"] + 'Mesh')
                    # apply random location/rotation according to parameters
                    if cm.randomLoc > 0:
                        randomizeLoc(dimensions["width"], dimensions["height"], bm)
                    if cm.randomRot > 0:
                        d = dimensions["width"]/2
                        sX = (brickType[0] * 2) - 1
                        sY = (brickType[1] * 2) - 1
                        center = ( ((d*sX)-d) / 2, ((d*sY)-d) / 2, 0.0 )
                        randomizeRot(center, brickType, bm)
                    # send mesh to bm
                    bm.to_mesh(m)
                    # return updated brick object
                brick = bpy.data.objects.new(brickD["name"], m)
                brick.location = Vector(brickD["co"])
                if mat is not None:
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
                    for v in bm.verts:
                        v.co = (v.co[0] - customObj_details.x.mid, v.co[1] - customObj_details.y.mid, v.co[2] - customObj_details.z.mid)

                    maxDist = max(customObj_details.x.distance, customObj_details.y.distance, customObj_details.z.distance)
                    bmesh.ops.scale(bm, vec=Vector(((R[0]-dimensions["gap"]) / customObj_details.x.distance, (R[1]-dimensions["gap"]) / customObj_details.y.distance, (R[2]-dimensions["gap"]) / customObj_details.z.distance)), verts=bm.verts)
                    for v in bm.verts:
                        v.co = (v.co[0] + brickD["co"][0], v.co[1] + brickD["co"][1], v.co[2] + brickD["co"][2])
                else:
                    # create new brick mesh
                    bm = Bricks.new_mesh(dimensions=dimensions, name=brickD["name"], gap_percentage=cm.gap, type=brickType, transform=brickD["co"], undersideDetail=undersideDetail, logo=logoDetail, logo_details=logo_details, stud=studDetail, returnType="bmesh")
                # apply random location/rotation according to parameters
                if cm.randomLoc > 0:
                    randomizeLoc(dimensions["width"], dimensions["height"], bm)
                if cm.randomRot > 0:
                    d = dimensions["width"]/2
                    sX = (brickType[0] * 2) - 1
                    sY = (brickType[1] * 2) - 1
                    center = ( (((d*sX)-d) / 2) + brickD["co"][0], (((d*sY)-d) / 2) + brickD["co"][1], brickD["co"][2] )
                    randomizeRot(center, brickType, bm)
                # create new mesh and send to bm
                tempMesh = bpy.data.meshes.new(brickD["name"])
                bm.to_mesh(tempMesh)
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
                for v in brick.data.vertices:
                    if not v.select:
                        vg.add([v.index], 1, "ADD")
                bGroup.objects.link(brick)
                brick.parent = parent
                if cm.materialType == "Custom":
                    mat = bpy.data.materials.get(cm.materialName)
                    if mat is not None:
                        brick.data.materials.append(mat)
                scn.objects.link(brick)
                brick.isBrick = True
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
        for i,v in enumerate(allBricksObj.data.vertices):
            if not v.select:
                vg.add([v.index], 1, "ADD")
            # print status to terminal
            percent = i/len(bricksD)
            if percent < 1:
                update_progress("Linking to Scene", percent)
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
    update_progress("Linking to Scene", 1)
