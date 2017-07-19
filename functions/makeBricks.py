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
import time
import bmesh
import random
import time
from mathutils import Vector, Matrix
from ..classes.Brick import Bricks
from ..functions.common_functions import stopWatch, groupExists

def brickAvail(brick):
    if brick != None:
        if brick["name"] != "DNE" and not brick["connected"]:
            return True
    return False

def getNextBrick(bricks, loc, x, y):
    try:
        return bricks[str(loc[0] + x) + "," + str(loc[1] + y) + "," + str(loc[2])]
    except:
        return None

def addEdgeSplitMod(obj):
    """ Add edge split modifier """
    eMod = obj.modifiers.new('Edge Split', 'EDGE_SPLIT')
    # eMod.use_edge_angle = False
    for p in obj.data.polygons:
        p.use_smooth = True

def combineMeshes(meshes):
    bm = bmesh.new()
    # add meshes to bmesh
    for m in meshes:
        bm.from_mesh( m )
    finalMesh = bpy.data.meshes.new( "newMesh" )
    bm.to_mesh( finalMesh )
    return finalMesh

def makeBricks(parent, logo, dimensions, bricksD, split=False):
    # set up variables
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    n = cm.source_name
    ct = time.time()

    # get brick dicts in seeded order
    keys = list(bricksD.keys())
    random.seed(a=cm.mergeSeed)
    random.shuffle(keys)

    # create group for lego bricks
    LEGOizer_bricks = 'LEGOizer_%(n)s_bricks' % locals()
    if groupExists(LEGOizer_bricks):
        bpy.data.groups.remove(group=bpy.data.groups[LEGOizer_bricks], do_unlink=True)
    bGroup = bpy.data.groups.new(LEGOizer_bricks)

    if not split:
        allBrickMeshes = []

    denom = len(keys)/20
    j = 0
    for i,key in enumerate(keys):
        brickD = bricksD[key]
        if brickD["name"] != "DNE" and not brickD["connected"]:
            loc = key.split(",")
            for i in range(len(loc)):
                loc[i] = int(loc[i])

            # Set up brick types
            brickTypes = [[1,1]]
            nextBrick = getNextBrick(bricksD, loc, 1, 0)
            if brickAvail(nextBrick) and cm.maxBrickScale > 1:
                brickTypes.append([2,1])
                nextBrick = getNextBrick(bricksD, loc, 2, 0)
                if brickAvail(nextBrick) and cm.maxBrickScale > 2:
                    brickTypes.append([3,1])
                    nextBrick = getNextBrick(bricksD, loc, 3, 0)
                    if brickAvail(nextBrick) and cm.maxBrickScale > 3:
                        brickTypes.append([4,1])
                        nextBrick0 = getNextBrick(bricksD, loc, 4, 0)
                        nextBrick1 = getNextBrick(bricksD, loc, 5, 0)
                        if brickAvail(nextBrick0) and brickAvail(nextBrick1) and cm.maxBrickScale > 5:
                            brickTypes.append([6,1])
                            nextBrick0 = getNextBrick(bricksD, loc, 6, 0)
                            nextBrick1 = getNextBrick(bricksD, loc, 7, 0)
                            if brickAvail(nextBrick0) and brickAvail(nextBrick1) and cm.maxBrickScale > 7:
                                brickTypes.append([8,1])
            nextBrick = getNextBrick(bricksD, loc, 0, 1)
            if brickAvail(nextBrick) and cm.maxBrickScale > 1:
                brickTypes.append([1,2])
                nextBrick = getNextBrick(bricksD, loc, 0, 2)
                if brickAvail(nextBrick) and cm.maxBrickScale > 2:
                    brickTypes.append([1,3])
                    nextBrick = getNextBrick(bricksD, loc, 0, 3)
                    if brickAvail(nextBrick) and cm.maxBrickScale > 3:
                        brickTypes.append([1,4])
                        nextBrick0 = getNextBrick(bricksD, loc, 0, 4)
                        nextBrick1 = getNextBrick(bricksD, loc, 0, 5)
                        if brickAvail(nextBrick0) and brickAvail(nextBrick1) and cm.maxBrickScale > 5:
                            brickTypes.append([1,6])
                            nextBrick0 = getNextBrick(bricksD, loc, 0, 6)
                            nextBrick1 = getNextBrick(bricksD, loc, 0, 7)
                            if brickAvail(nextBrick0) and brickAvail(nextBrick1) and cm.maxBrickScale > 7:
                                brickTypes.append([1,8])
            nextBrick0 = getNextBrick(bricksD, loc, 0, 1)
            nextBrick1 = getNextBrick(bricksD, loc, 1, 0)
            nextBrick2 = getNextBrick(bricksD, loc, 1, 1)
            if brickAvail(nextBrick0) and brickAvail(nextBrick1) and brickAvail(nextBrick2) and cm.maxBrickScale > 3:
                brickTypes.append([2,2])
                nextBrick0 = getNextBrick(bricksD, loc, 0, 2)
                nextBrick1 = getNextBrick(bricksD, loc, 1, 2)
                if brickAvail(nextBrick0) and brickAvail(nextBrick1) and cm.maxBrickScale > 5:
                    brickTypes.append([2,3])
                    nextBrick0 = getNextBrick(bricksD, loc, 0, 3)
                    nextBrick1 = getNextBrick(bricksD, loc, 1, 3)
                    if brickAvail(nextBrick0) and brickAvail(nextBrick1) and cm.maxBrickScale > 7:
                        brickTypes.append([2,4])
                        nextBrick0 = getNextBrick(bricksD, loc, 0, 4)
                        nextBrick1 = getNextBrick(bricksD, loc, 1, 4)
                        nextBrick2 = getNextBrick(bricksD, loc, 0, 5)
                        nextBrick3 = getNextBrick(bricksD, loc, 1, 5)
                        if brickAvail(nextBrick0) and brickAvail(nextBrick1) and brickAvail(nextBrick2) and brickAvail(nextBrick3) and cm.maxBrickScale > 11:
                            brickTypes.append([2,6])
                            nextBrick0 = getNextBrick(bricksD, loc, 0, 6)
                            nextBrick1 = getNextBrick(bricksD, loc, 1, 6)
                            nextBrick2 = getNextBrick(bricksD, loc, 0, 7)
                            nextBrick3 = getNextBrick(bricksD, loc, 1, 7)
                            if brickAvail(nextBrick0) and brickAvail(nextBrick1) and brickAvail(nextBrick2) and brickAvail(nextBrick3) and cm.maxBrickScale > 15:
                                brickTypes.append([2,8])
                                nextBrick0 = getNextBrick(bricksD, loc, 0, 8)
                                nextBrick1 = getNextBrick(bricksD, loc, 1, 8)
                                nextBrick2 = getNextBrick(bricksD, loc, 0, 9)
                                nextBrick3 = getNextBrick(bricksD, loc, 1, 9)
                                if brickAvail(nextBrick0) and brickAvail(nextBrick1) and brickAvail(nextBrick2) and brickAvail(nextBrick3) and cm.maxBrickScale > 19:
                                    brickTypes.append([2,10])
                nextBrick0 = getNextBrick(bricksD, loc, 2, 0)
                nextBrick1 = getNextBrick(bricksD, loc, 2, 1)
                if brickAvail(nextBrick0) and brickAvail(nextBrick1) and cm.maxBrickScale > 5:
                    brickTypes.append([3,2])
                    nextBrick0 = getNextBrick(bricksD, loc, 3, 0)
                    nextBrick1 = getNextBrick(bricksD, loc, 3, 1)
                    if brickAvail(nextBrick0) and brickAvail(nextBrick1) and cm.maxBrickScale > 7:
                        brickTypes.append([4,2])
                        nextBrick0 = getNextBrick(bricksD, loc, 4, 0)
                        nextBrick1 = getNextBrick(bricksD, loc, 4, 1)
                        nextBrick2 = getNextBrick(bricksD, loc, 5, 0)
                        nextBrick3 = getNextBrick(bricksD, loc, 5, 1)
                        if brickAvail(nextBrick0) and brickAvail(nextBrick1) and brickAvail(nextBrick2) and brickAvail(nextBrick3) and cm.maxBrickScale > 11:
                            brickTypes.append([6,2])
                            nextBrick0 = getNextBrick(bricksD, loc, 6, 0)
                            nextBrick1 = getNextBrick(bricksD, loc, 6, 1)
                            nextBrick2 = getNextBrick(bricksD, loc, 7, 0)
                            nextBrick3 = getNextBrick(bricksD, loc, 7, 1)
                            if brickAvail(nextBrick0) and brickAvail(nextBrick1) and brickAvail(nextBrick2) and brickAvail(nextBrick3) and cm.maxBrickScale > 15:
                                brickTypes.append([8,2])
                                nextBrick0 = getNextBrick(bricksD, loc, 8, 0)
                                nextBrick1 = getNextBrick(bricksD, loc, 8, 1)
                                nextBrick2 = getNextBrick(bricksD, loc, 9, 0)
                                nextBrick3 = getNextBrick(bricksD, loc, 9, 1)
                                if brickAvail(nextBrick0) and brickAvail(nextBrick1) and brickAvail(nextBrick2) and brickAvail(nextBrick3) and cm.maxBrickScale > 19:
                                    brickTypes.append([10,2])

            # # if it's only going to be a 1x1, skip merging for this brick
            # if len(brickTypes) == 0:
            #     continue
            # sort brick types from smallest to largest
            brickTypes.sort()

            # ranInt = random.randint(1,len(brickTypes)*cm.maxBrickScale)
            # if ranInt > len(brickTypes):
            #     brickType = brickTypes[-1]
            # else:
            #     brickType = brickTypes[ranInt-1]
            brickType = brickTypes[-1]

            topExposed = False
            botExposed = False

            # Iterate through merged bricks
            for x in range(brickType[0]):
                for y in range(brickType[1]):
                    # check if brick top or bottom is exposed
                    try:
                        if bricksD[str(loc[0] + x) + "," + str(loc[1] + y) + "," + str(loc[2] + 1)]["val"] == 0:
                            topExposed = True
                    except:
                        topExposed = True
                    try:
                        if bricksD[str(loc[0] + x) + "," + str(loc[1] + y) + "," + str(loc[2] - 1)]["val"] == 0:
                            botExposed = True
                    except:
                        botExposed = True
                    # skip the original brick
                    if x == 0 and y == 0:
                        brickD["connected"] = True
                        continue
                    # get brick at x,y location
                    curBrick = bricksD[str(loc[0] + x) + "," + str(loc[1] + y) + "," + str(loc[2])]
                    # add brick to connected bricks
                    curBrick["connected"] = True
                    # set name of deleted brick to 'DNE'
                    curBrick["name"] = "DNE"

            if topExposed or cm.logoDetail == "On All Studs":
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

            # Remesh brick at original location
            if split or j == 0:
                m = Bricks().new_mesh(name=brickD["name"], height=dimensions["height"], gap_percentage=cm.gap, type=brickType, undersideDetail=undersideDetail, logo=logoDetail, stud=studDetail)
                brick = bpy.data.objects.new(brickD["name"], m)
                brick.location = Vector(brickD["co"])

                # Add edge split modifier
                if cm.smoothCylinders and cm.studVerts > 12:
                    addEdgeSplitMod(brick)
            else:
                bm = Bricks().new_mesh(name=brickD["name"], height=dimensions["height"], gap_percentage=cm.gap, type=brickType, undersideDetail=undersideDetail, logo=logoDetail, stud=studDetail, returnType="bmesh")
                bmesh.ops.transform(bm, matrix=Matrix.Translation(brickD["co"]), verts=bm.verts)
                tempMesh = bpy.data.meshes.new(brickD["name"])
                bm.to_mesh(tempMesh)
                allBrickMeshes.append(tempMesh)
            j += 1


        # print status to terminal
        if i % denom < 1:
            if i == len(keys):
                print("building... 100%")
            else:
                percent = i*100//len(keys)+5
                if percent > 100:
                    percent = 100
                print("building... " + str(percent) + "%")

    # allBricksObj.data.update(calc_edges=True)

    if not split:
        m = combineMeshes(allBrickMeshes)
        allBricksObj = bpy.data.objects.new('LEGOizer_%(n)s_bricks_combined' % locals(), m)
        if cm.smoothCylinders and cm.studVerts > 12:
            addEdgeSplitMod(allBricksObj)
        bGroup.objects.link(allBricksObj)
        scn.objects.link(allBricksObj)
        allBricksObj.parent = parent
    else:
        for key in bricksD:
            if bricksD[key]["name"] != "DNE":
                brick = bpy.data.objects[bricksD[key]["name"]]
                bGroup.objects.link(brick)
                scn.objects.link(brick)
                brick.parent = parent

    stopWatch("Time Elapsed (merge)", time.time()-ct)
