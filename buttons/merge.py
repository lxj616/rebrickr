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
from ..functions import *
props = bpy.props

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

class legoizerMergeBricks(bpy.types.Operator):
    """Reduces poly count by merging bricks"""                                  # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "scene.legoizer_merge"                                          # unique identifier for buttons and menu items to reference.
    bl_label = "Merge Bricks"                                                   # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}                                           # enable undo for the operator.

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns false) """
        scn = context.scene
        if scn.cmlist_index == -1:
            return False
        n = scn.cmlist[scn.cmlist_index].source_name
        if groupExists("LEGOizer_%(n)s_bricks" % locals()) and groupExists("LEGOizer_%(n)s" % locals()) and groupExists("LEGOizer_%(n)s_refBricks" % locals()):
            return True
        return False

    def execute(self, context):
        # set up variables
        scn = context.scene
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name

        # get start time
        startTime = time.time()

        # get source brick
        source = bpy.data.groups["LEGOizer_%(n)s" % locals()].objects[0]
        if groupExists("LEGOizer_refLogo"):
            logo = bpy.data.groups["LEGOizer_refLogo"].objects[0]
        else:
            logo = None
        bricks = source["bricks"]
        dimensions = Bricks.get_dimensions(cm.brickHeight, cm.gap)

        # TODO: Write merge bricks code
        for key in bricks:
            brickD = bricks[key]
            if brickD["name"] != "DNE" and len(brickD["connected"]) == 0:
                loc = key.split(",")
                for i in range(len(loc)):
                    loc[i] = int(loc[i])

                brick0 = bpy.data.objects[brickD["name"]]
                brickTypes = []
                nextBrick = getNextBrick(bricks, loc, 1, 0)
                if brickAvail(nextBrick):
                    brickTypes.append([2,1])
                    nextBrick = getNextBrick(bricks, loc, 2, 0)
                    if brickAvail(nextBrick):
                        brickTypes.append([3,1])
                        nextBrick = getNextBrick(bricks, loc, 3, 0)
                        if brickAvail(nextBrick):
                            brickTypes.append([4,1])
                            nextBrick0 = getNextBrick(bricks, loc, 4, 0)
                            nextBrick1 = getNextBrick(bricks, loc, 5, 0)
                            if brickAvail(nextBrick0) and brickAvail(nextBrick1):
                                brickTypes.append([6,1])
                                nextBrick0 = getNextBrick(bricks, loc, 6, 0)
                                nextBrick1 = getNextBrick(bricks, loc, 7, 0)
                                if brickAvail(nextBrick0) and brickAvail(nextBrick1):
                                    brickTypes.append([8,1])
                nextBrick = getNextBrick(bricks, loc, 0, 1)
                if brickAvail(nextBrick):
                    brickTypes.append([1,2])
                    nextBrick = getNextBrick(bricks, loc, 0, 2)
                    if brickAvail(nextBrick):
                        brickTypes.append([1,3])
                        nextBrick = getNextBrick(bricks, loc, 0, 3)
                        if brickAvail(nextBrick):
                            brickTypes.append([1,4])
                            nextBrick0 = getNextBrick(bricks, loc, 0, 4)
                            nextBrick1 = getNextBrick(bricks, loc, 0, 5)
                            if brickAvail(nextBrick0) and brickAvail(nextBrick1):
                                brickTypes.append([1,6])
                                nextBrick0 = getNextBrick(bricks, loc, 0, 6)
                                nextBrick1 = getNextBrick(bricks, loc, 0, 7)
                                if brickAvail(nextBrick0) and brickAvail(nextBrick1):
                                    brickTypes.append([1,8])
                nextBrick0 = getNextBrick(bricks, loc, 0, 1)
                nextBrick1 = getNextBrick(bricks, loc, 1, 0)
                nextBrick2 = getNextBrick(bricks, loc, 1, 1)
                if brickAvail(nextBrick0) and brickAvail(nextBrick1) and brickAvail(nextBrick2):
                    brickTypes.append([2,2])
                    nextBrick0 = getNextBrick(bricks, loc, 0, 2)
                    nextBrick1 = getNextBrick(bricks, loc, 1, 2)
                    if brickAvail(nextBrick0) and brickAvail(nextBrick1):
                        brickTypes.append([2,3])
                        nextBrick0 = getNextBrick(bricks, loc, 0, 3)
                        nextBrick1 = getNextBrick(bricks, loc, 1, 3)
                        if brickAvail(nextBrick0) and brickAvail(nextBrick1):
                            brickTypes.append([2,4])
                            nextBrick0 = getNextBrick(bricks, loc, 0, 4)
                            nextBrick1 = getNextBrick(bricks, loc, 1, 4)
                            nextBrick2 = getNextBrick(bricks, loc, 0, 5)
                            nextBrick3 = getNextBrick(bricks, loc, 1, 5)
                            if brickAvail(nextBrick0) and brickAvail(nextBrick1) and brickAvail(nextBrick2) and brickAvail(nextBrick3):
                                brickTypes.append([2,6])
                                nextBrick0 = getNextBrick(bricks, loc, 0, 6)
                                nextBrick1 = getNextBrick(bricks, loc, 1, 6)
                                nextBrick2 = getNextBrick(bricks, loc, 0, 7)
                                nextBrick3 = getNextBrick(bricks, loc, 1, 7)
                                if brickAvail(nextBrick0) and brickAvail(nextBrick1) and brickAvail(nextBrick2) and brickAvail(nextBrick3):
                                    brickTypes.append([2,8])
                    nextBrick0 = getNextBrick(bricks, loc, 2, 0)
                    nextBrick1 = getNextBrick(bricks, loc, 2, 1)
                    if brickAvail(nextBrick0) and brickAvail(nextBrick1):
                        brickTypes.append([3,2])
                        nextBrick0 = getNextBrick(bricks, loc, 3, 0)
                        nextBrick1 = getNextBrick(bricks, loc, 3, 1)
                        if brickAvail(nextBrick0) and brickAvail(nextBrick1):
                            brickTypes.append([4,2])
                            nextBrick0 = getNextBrick(bricks, loc, 4, 0)
                            nextBrick1 = getNextBrick(bricks, loc, 4, 1)
                            nextBrick2 = getNextBrick(bricks, loc, 5, 0)
                            nextBrick3 = getNextBrick(bricks, loc, 5, 1)
                            if brickAvail(nextBrick0) and brickAvail(nextBrick1) and brickAvail(nextBrick2) and brickAvail(nextBrick3):
                                brickTypes.append([6,2])
                                nextBrick0 = getNextBrick(bricks, loc, 6, 0)
                                nextBrick1 = getNextBrick(bricks, loc, 6, 1)
                                nextBrick2 = getNextBrick(bricks, loc, 7, 0)
                                nextBrick3 = getNextBrick(bricks, loc, 7, 1)
                                if brickAvail(nextBrick0) and brickAvail(nextBrick1) and brickAvail(nextBrick2) and brickAvail(nextBrick3):
                                    brickTypes.append([8,2])

                if len(brickTypes) == 0:
                    continue
                brickTypes.sort()
                print(brickTypes)

                # ranInt = random.randint(1,len(brickTypes)*6)
                # if ranInt > len(brickTypes):
                #     brickType = brickTypes[-1]
                # else:
                #     brickType = brickTypes[ranInt-1]
                brickType = brickTypes[-1]

                for x in range(brickType[0]):
                    for y in range(brickType[1]):
                        if x == 0 and y == 0:
                            continue
                        curBrick = bricks[str(loc[0] + x) + "," + str(loc[1] + y) + "," + str(loc[2])]
                        l0 = list(brickD["connected"])
                        l0.append(key)
                        brickD["connected"] = l0
                        l1 = list(curBrick["connected"])
                        l1.append(key)
                        curBrick["connected"] = l1
                        brick1 = bpy.data.objects[curBrick["name"]]
                        bpy.data.objects.remove(brick1, do_unlink=True)
                        curBrick["name"] = "DNE"

                m = Bricks().new_mesh(name=brick0.name, height=dimensions["height"], type=brickType, undersideDetail=cm.exposedUndersideDetail, logo=logo, stud=True)
                brick0.data = m

        scn.cmlist[scn.cmlist_index].changesToCommit = True

        # STOPWATCH CHECK
        stopWatch("Time Elapsed", time.time()-startTime)

        return{"FINISHED"}
