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
import random
import time
from ..classes.Brick import Bricks
from ..functions.common_functions import stopWatch

def brickAvail(brick):
    if brick != None:
        if brick["name"] != "DNE" and len(brick["connected"]) == 0:
            return True
    return False

def getNextBrick(bricks, loc, x, y):
    try:
        return bricks[str(loc[0] + x) + "," + str(loc[1] + y) + "," + str(loc[2])]
    except:
        return None

def makeBricks(source, logo, dimensions, bricks):
    # set up variables
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    n = cm.source_name
    ct = time.time()

    # get bricks in seeded order
    keys = list(bricks.keys())
    random.seed(a=cm.mergeSeed)
    random.shuffle(keys)

    denom = len(keys)/20
    for i,key in enumerate(keys):
        brickD = bricks[key]
        if brickD["name"] != "DNE" and len(brickD["connected"]) == 0:
            loc = key.split(",")
            for i in range(len(loc)):
                loc[i] = int(loc[i])

            # Set up brick types
            brick0 = bpy.data.objects[brickD["name"]]
            brickTypes = [[1,1]]
            nextBrick = getNextBrick(bricks, loc, 1, 0)
            if brickAvail(nextBrick) and cm.maxBrickScale > 1:
                brickTypes.append([2,1])
                nextBrick = getNextBrick(bricks, loc, 2, 0)
                if brickAvail(nextBrick) and cm.maxBrickScale > 2:
                    brickTypes.append([3,1])
                    nextBrick = getNextBrick(bricks, loc, 3, 0)
                    if brickAvail(nextBrick) and cm.maxBrickScale > 3:
                        brickTypes.append([4,1])
                        nextBrick0 = getNextBrick(bricks, loc, 4, 0)
                        nextBrick1 = getNextBrick(bricks, loc, 5, 0)
                        if brickAvail(nextBrick0) and brickAvail(nextBrick1) and cm.maxBrickScale > 5:
                            brickTypes.append([6,1])
                            nextBrick0 = getNextBrick(bricks, loc, 6, 0)
                            nextBrick1 = getNextBrick(bricks, loc, 7, 0)
                            if brickAvail(nextBrick0) and brickAvail(nextBrick1) and cm.maxBrickScale > 7:
                                brickTypes.append([8,1])
            nextBrick = getNextBrick(bricks, loc, 0, 1)
            if brickAvail(nextBrick) and cm.maxBrickScale > 1:
                brickTypes.append([1,2])
                nextBrick = getNextBrick(bricks, loc, 0, 2)
                if brickAvail(nextBrick) and cm.maxBrickScale > 2:
                    brickTypes.append([1,3])
                    nextBrick = getNextBrick(bricks, loc, 0, 3)
                    if brickAvail(nextBrick) and cm.maxBrickScale > 3:
                        brickTypes.append([1,4])
                        nextBrick0 = getNextBrick(bricks, loc, 0, 4)
                        nextBrick1 = getNextBrick(bricks, loc, 0, 5)
                        if brickAvail(nextBrick0) and brickAvail(nextBrick1) and cm.maxBrickScale > 5:
                            brickTypes.append([1,6])
                            nextBrick0 = getNextBrick(bricks, loc, 0, 6)
                            nextBrick1 = getNextBrick(bricks, loc, 0, 7)
                            if brickAvail(nextBrick0) and brickAvail(nextBrick1) and cm.maxBrickScale > 7:
                                brickTypes.append([1,8])
            nextBrick0 = getNextBrick(bricks, loc, 0, 1)
            nextBrick1 = getNextBrick(bricks, loc, 1, 0)
            nextBrick2 = getNextBrick(bricks, loc, 1, 1)
            if brickAvail(nextBrick0) and brickAvail(nextBrick1) and brickAvail(nextBrick2) and cm.maxBrickScale > 3:
                brickTypes.append([2,2])
                nextBrick0 = getNextBrick(bricks, loc, 0, 2)
                nextBrick1 = getNextBrick(bricks, loc, 1, 2)
                if brickAvail(nextBrick0) and brickAvail(nextBrick1) and cm.maxBrickScale > 5:
                    brickTypes.append([2,3])
                    nextBrick0 = getNextBrick(bricks, loc, 0, 3)
                    nextBrick1 = getNextBrick(bricks, loc, 1, 3)
                    if brickAvail(nextBrick0) and brickAvail(nextBrick1) and cm.maxBrickScale > 7:
                        brickTypes.append([2,4])
                        nextBrick0 = getNextBrick(bricks, loc, 0, 4)
                        nextBrick1 = getNextBrick(bricks, loc, 1, 4)
                        nextBrick2 = getNextBrick(bricks, loc, 0, 5)
                        nextBrick3 = getNextBrick(bricks, loc, 1, 5)
                        if brickAvail(nextBrick0) and brickAvail(nextBrick1) and brickAvail(nextBrick2) and brickAvail(nextBrick3) and cm.maxBrickScale > 11:
                            brickTypes.append([2,6])
                            nextBrick0 = getNextBrick(bricks, loc, 0, 6)
                            nextBrick1 = getNextBrick(bricks, loc, 1, 6)
                            nextBrick2 = getNextBrick(bricks, loc, 0, 7)
                            nextBrick3 = getNextBrick(bricks, loc, 1, 7)
                            if brickAvail(nextBrick0) and brickAvail(nextBrick1) and brickAvail(nextBrick2) and brickAvail(nextBrick3) and cm.maxBrickScale > 15:
                                brickTypes.append([2,8])
                nextBrick0 = getNextBrick(bricks, loc, 2, 0)
                nextBrick1 = getNextBrick(bricks, loc, 2, 1)
                if brickAvail(nextBrick0) and brickAvail(nextBrick1) and cm.maxBrickScale > 5:
                    brickTypes.append([3,2])
                    nextBrick0 = getNextBrick(bricks, loc, 3, 0)
                    nextBrick1 = getNextBrick(bricks, loc, 3, 1)
                    if brickAvail(nextBrick0) and brickAvail(nextBrick1) and cm.maxBrickScale > 7:
                        brickTypes.append([4,2])
                        nextBrick0 = getNextBrick(bricks, loc, 4, 0)
                        nextBrick1 = getNextBrick(bricks, loc, 4, 1)
                        nextBrick2 = getNextBrick(bricks, loc, 5, 0)
                        nextBrick3 = getNextBrick(bricks, loc, 5, 1)
                        if brickAvail(nextBrick0) and brickAvail(nextBrick1) and brickAvail(nextBrick2) and brickAvail(nextBrick3) and cm.maxBrickScale > 11:
                            brickTypes.append([6,2])
                            nextBrick0 = getNextBrick(bricks, loc, 6, 0)
                            nextBrick1 = getNextBrick(bricks, loc, 6, 1)
                            nextBrick2 = getNextBrick(bricks, loc, 7, 0)
                            nextBrick3 = getNextBrick(bricks, loc, 7, 1)
                            if brickAvail(nextBrick0) and brickAvail(nextBrick1) and brickAvail(nextBrick2) and brickAvail(nextBrick3) and cm.maxBrickScale > 15:
                                brickTypes.append([8,2])

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
                        if bricks[str(loc[0] + x) + "," + str(loc[1] + y) + "," + str(loc[2] + 1)]["val"] == 0:
                            topExposed = True
                    except:
                        topExposed = True
                    try:
                        if bricks[str(loc[0] + x) + "," + str(loc[1] + y) + "," + str(loc[2] - 1)]["val"] == 0:
                            botExposed = True
                    except:
                        botExposed = True
                    # skip the original brick
                    if x == 0 and y == 0:
                        continue
                    # get brick at x,y location
                    curBrick = bricks[str(loc[0] + x) + "," + str(loc[1] + y) + "," + str(loc[2])]
                    # add brick to connected bricks
                    l0 = list(brickD["connected"])
                    l0.append(key)
                    brickD["connected"] = l0
                    l1 = list(curBrick["connected"])
                    l1.append(key)
                    curBrick["connected"] = l1
                    # delete brick object
                    brick1 = bpy.data.objects[curBrick["name"]]
                    bpy.data.objects.remove(brick1, do_unlink=True)
                    # set name of deleted brick to 'DNE'
                    curBrick["name"] = "DNE"

            if topExposed or cm.logoDetail == "On All Bricks":
                logoDetail = logo
            else:
                logoDetail = None
            if (topExposed and cm.studDetail != "None") or cm.studDetail == "On All Studs":
                studDetail = True
            else:
                studDetail = False
            if botExposed:
                undersideDetail = cm.exposedUndersideDetail
            else:
                undersideDetail = cm.hiddenUndersideDetail

            # Remesh brick at original location
            m = Bricks().new_mesh(name=brick0.name, height=dimensions["height"], type=brickType, undersideDetail=undersideDetail, logo=logoDetail, stud=studDetail)
            brick0.data = m

        # print status to terminal
        if i % denom < 1:
            if i == len(keys):
                print("building... 100%")
            else:
                percent = i*100//len(keys)+5
                if percent > 100:
                    percent = 100
                print("building... " + str(percent) + "%")

    cm.bricksMerged = True

    stopWatch("Time Elapsed (merge)", time.time()-ct)
