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
import copy

# Blender imports
import bpy
from bpy.types import Operator

# Rebrickr imports
from .mergeBricks import *
from ..undo_stack import *
from ..functions import *
from ...brickify import *
from ...brickify import *
from ....lib.bricksDict.functions import getDictKey
from ....lib.Brick.legal_brick_sizes import *
from ....functions import *


class drawAdjacent(Operator):
    """Draw brick to one side of active brick"""
    bl_idname = "rebrickr.draw_adjacent"
    bl_label = "Draw Adjacent Bricks"
    bl_options = {"REGISTER", "UNDO"}

    ################################################
    # Blender Operator methods

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns False) """
        scn = bpy.context.scene
        active_obj = scn.objects.active
        # check active object is not None
        if active_obj is None:
            return False
        # check that active_object is brick
        if not active_obj.isBrick:
            return False
        return True

    def execute(self, context):
        try:
            # store enabled/disabled values
            createAdjBricks = [self.xPos, self.xNeg, self.yPos, self.yNeg, self.zPos, self.zNeg]
            # if no sides were and are selected, don't execute (i.e. if only brick type changed)
            if True not in [createAdjBricks[i] or self.adjBricksCreated[i][0] for i in range(6)]:
                return {"CANCELLED"}
            # push to undo stack
            self.undo_stack.matchPythonToBlenderState()
            if self.orig_undo_stack_length == self.undo_stack.getLength():
                self.undo_stack.undo_push('draw_adjacent')
            # initialize variables
            scn, cm, _ = getActiveContextInfo()
            scn.update()
            self.undo_stack.iterateStates(cm)
            obj = scn.objects.active
            initial_active_obj_name = obj.name
            keysToMerge = []

            # get dict key details of current obj
            dictKey, dictLoc = getDictKey(obj.name)
            x0,y0,z0 = dictLoc
            # get size of current brick (e.g. [2, 4, 1])
            objSize = self.bricksDict[dictKey]["size"]

            zStep = getZStep(cm)
            decriment = 0
            dimensions = Bricks.get_dimensions(cm.brickHeight, zStep, cm.gap)
            # check all 6 directions for action to be executed
            for i in range(6):
                # if checking beneath obj in 'Bricks and Plates', check 3 keys below instead of 1 key below
                if i == 5 and cm.brickType == "BRICKS AND PLATES":
                    newBrickHeight = self.getNewBrickHeight()
                    decriment = newBrickHeight - 1
                # if action should be executed (value changed in direction prop)
                if (createAdjBricks[i] or (not createAdjBricks[i] and self.adjBricksCreated[i][0])):
                    # add or remove bricks in all adjacent locations in current direction
                    for j,adjDictLoc in enumerate(self.adjDKLs[i]):
                        if decriment != 0:
                            adjDictLoc = adjDictLoc.copy()
                            adjDictLoc[2] -= decriment
                        self.toggleBrick(cm, dimensions, adjDictLoc, dictKey, objSize, i, j, keysToMerge, addBrick=createAdjBricks[i])
                    # after ALL bricks toggled, check exposure of bricks above and below new ones
                    for j,adjDictLoc in enumerate(self.adjDKLs[i]):
                        dictLoc2 = dictLoc
                        dictLoc2[2] += 1
                        self.bricksDict = verifyBrickExposureAboveAndBelow(adjDictLoc.copy(), self.bricksDict, decriment=decriment, zNeg=self.zNeg, zPos=self.zPos)

            # recalculate val for each bricksDict key in original brick
            brickLocs = [[x, y, z] for z in range(z0, z0 + objSize[2], zStep) for y in range(y0, y0 + objSize[1]) for x in range(x0, x0 + objSize[0])]
            for curLoc in brickLocs:
                setCurBrickVal(self.bricksDict, curLoc)

            # attempt to merge created bricks
            tallBandP = cm.brickType == "BRICKS AND PLATES" and self.brickType in getBrickTypes(height=3)
            keysToUpdate = mergeBricks.mergeBricks(self.bricksDict, keysToMerge, cm, mergeVertical=self.brickType in getBrickTypes(height=3), targetType=self.brickType, height3Only=tallBandP)

            # if bricks created on top, set top_exposed of original brick to False
            if self.zPos:
                self.bricksDict[dictKey]["top_exposed"] = False
                keysToUpdate.append(dictKey)
                delete(obj)
            # if bricks created on bottom, set top_exposed of original brick to False
            if self.zNeg:
                self.bricksDict[dictKey]["bot_exposed"] = False
                if not self.zPos:
                    keysToUpdate.append(dictKey)
                    delete(obj)

            # draw created bricks
            drawUpdatedBricks(cm, self.bricksDict, keysToUpdate, selectCreated=False)

            # select original brick
            orig_obj = bpy.data.objects.get(initial_active_obj_name)
            if orig_obj: select(orig_obj, active=orig_obj)

            # model is now customized
            cm.customized = True
        except:
            handle_exception()
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_popup(self, event)

    ################################################
    # initialization method

    def __init__(self):
        try:
            self.undo_stack = UndoStack.get_instance()
            self.orig_undo_stack_length = self.undo_stack.getLength()
            scn, cm, _ = getActiveContextInfo()
            obj = scn.objects.active

            # initialize self.bricksDict
            self.bricksDict, _ = getBricksDict(cm=cm)

            # initialize direction bools
            self.zPos = False
            self.zNeg = False
            self.yPos = False
            self.yNeg = False
            self.xPos = False
            self.xNeg = False

            # initialize vars for self.adjDKLs setup
            dictKey, dictLoc = getDictKey(obj.name)
            x,y,z = dictLoc
            objSize = self.bricksDict[dictKey]["size"]
            zStep = getZStep(cm)
            self.adjDKLs = [[],[],[],[],[],[]]
            # set up self.adjDKLs
            for y0 in range(y, y + objSize[1]):
                for z0 in range(z, z + (objSize[2]//zStep)):
                    dkl = [x + objSize[0], y0, z0]
                    self.adjDKLs[0].append(dkl)
            for y0 in range(y, y + objSize[1]):
                for z0 in range(z, z + (objSize[2]//zStep)):
                    dkl = [x - 1, y0, z0]
                    self.adjDKLs[1].append(dkl)
            for x0 in range(x, x + objSize[0]):
                for z0 in range(z, z + (objSize[2]//zStep)):
                    dkl = [x0, y + objSize[1], z0]
                    self.adjDKLs[2].append(dkl)
            for x0 in range(x, x + objSize[0]):
                for z0 in range(z, z + (objSize[2]//zStep)):
                    dkl = [x0, y - 1, z0]
                    self.adjDKLs[3].append(dkl)
            for x0 in range(x, x + objSize[0]):
                for y0 in range(y, y + objSize[1]):
                    if cm.brickType == "BRICKS AND PLATES":
                        dkl = [x0, y0, z + objSize[2]]
                    else:
                        dkl = [x0, y0, z + 1]
                    self.adjDKLs[4].append(dkl)
            for x0 in range(x, x + objSize[0]):
                for y0 in range(y, y + objSize[1]):
                    dkl = [x0, y0, z - 1]
                    self.adjDKLs[5].append(dkl)

            # initialize self.adjBricksCreated
            self.adjBricksCreated = []
            for i in range(6):
                self.adjBricksCreated.append([False]*len(self.adjDKLs[i]))

            # initialize self.brickType
            objType = self.bricksDict[dictKey]["type"]
            self.brickType = objType if objType is not None else ("BRICK" if objSize[2] == 3 else "PLATE")
        except:
            handle_exception()

    ###################################################
    # class variables

    # vars
    bricksDict = {}
    adjDKLs = []

    # get items for brickType prop
    def get_items1(self, context):
        items = getAvailableTypes(by="ACTIVE", includeSizes="ALL")
        return items

    # define props for popup
    brickType = bpy.props.EnumProperty(
        name="Brick Type",
        description="Type of brick to draw adjacent to current brick",
        items=get_items1,
        default=None)
    zPos = bpy.props.BoolProperty(name="+Z (Top)", default=False)
    zNeg = bpy.props.BoolProperty(name="-Z (Bottom)", default=False)
    xPos = bpy.props.BoolProperty(name="+X (Front)", default=False)
    xNeg = bpy.props.BoolProperty(name="-X (Back)", default=False)
    yPos = bpy.props.BoolProperty(name="+Y (Right)", default=False)
    yNeg = bpy.props.BoolProperty(name="-Y (Left)", default=False)

    #############################################
    # class methods

    def setDirBool(self, idx, val):
        if idx == 0: self.xPos = val
        elif idx == 1: self.xNeg = val
        elif idx == 2: self.yPos = val
        elif idx == 3: self.yNeg = val
        elif idx == 4: self.zPos = val
        elif idx == 5: self.zNeg = val

    def getBrickD(self, dkl):
        """ set up adjBrickD """
        adjacent_key = listToStr(dkl)
        try:
            brickD = self.bricksDict[adjacent_key]
            return adjacent_key, brickD
        except:
            return adjacent_key, False

    def getNewBrickHeight(self):
        newBrickHeight = 1 if self.brickType in getBrickTypes(height=1) else 3
        return newBrickHeight

    def getNewCoord(self, cm, co, dimensions, side, newBrickHeight):
        co = Vector(co)
        if side == 0:
            co.x += dimensions["width"]
        if side == 1:
            co.x -= dimensions["width"]
        if side == 2:
            co.y += dimensions["width"]
        if side == 3:
            co.y -= dimensions["width"]
        if side == 4:
            co.z += dimensions["height"]
        if side == 5:
            co.z -= dimensions["height"] * (newBrickHeight if cm.brickType == "BRICKS AND PLATES" else 1)
        return co.to_tuple()

    def isBrickAlreadyCreated(self, brickNum, side):
        return not (brickNum == len(self.adjDKLs[side]) - 1 and
                    not any(self.adjBricksCreated[side])) # evaluates True if all values in this list are False

    def toggleBrick(self, cm, dimensions, adjDictLoc, dictKey, objSize, side, brickNum, keysToMerge, addBrick=True):
        # if brick height is 3 and 'Bricks and Plates'
        newBrickHeight = self.getNewBrickHeight()
        checkTwoMoreAbove = cm.brickType == "BRICKS AND PLATES" and newBrickHeight == 3

        adjacent_key, adjBrickD = self.getBrickD(adjDictLoc)

        # if key doesn't exist in bricksDict, create it
        if not adjBrickD:
            n = cm.source_name
            cm.numBricksGenerated += 1
            j = cm.numBricksGenerated
            newDictLoc = adjDictLoc.copy()
            if side == 0:    # X+
                newDictLoc[0] = newDictLoc[0] - 1
            elif side == 1:  # X-
                newDictLoc[0] = newDictLoc[0] + 1
            elif side == 2:  # Y+
                newDictLoc[1] = newDictLoc[1] - 1
            elif side == 3:  # Y-
                newDictLoc[1] = newDictLoc[1] + 1
            elif side == 4:  # Z+
                newDictLoc[2] = newDictLoc[2] - 1
            elif side == 5:  # Z-
                newDictLoc[2] = newDictLoc[2] + (newBrickHeight if cm.brickType == "BRICKS AND PLATES" else 1)
            theKey = listToStr(newDictLoc)
            co0 = self.bricksDict[theKey]["co"]
            co = self.getNewCoord(cm, co0, dimensions, side, newBrickHeight)
            self.bricksDict[adjacent_key] = createBricksDictEntry(
                name=                 'Rebrickr_%(n)s_brick_%(j)s__%(adjacent_key)s' % locals(),
                co=                   co,
                nearest_face=         self.bricksDict[dictKey]["nearest_face"],
                nearest_intersection= self.bricksDict[dictKey]["nearest_intersection"],
                mat_name=             self.bricksDict[dictKey]["mat_name"],
            )
            adjBrickD = self.bricksDict[adjacent_key]
            # self.report({"WARNING"}, "Matrix not available at the following location: %(adjacent_key)s" % locals())
            # self.setDirBool(side, False)
            # return False

        # if brick exists there
        if adjBrickD["draw"] and not (addBrick and self.adjBricksCreated[side][brickNum]):
            # if attempting to add brick
            if addBrick:
                # reset direction bool if no bricks could be added
                if not self.isBrickAlreadyCreated(brickNum, side):
                    self.setDirBool(side, False)
                self.report({"INFO"}, "Brick already exists in the following location: %(adjacent_key)s" % locals())
                return False
            # if attempting to remove brick
            else:
                adjBrickD["draw"] = False
                setCurBrickVal(self.bricksDict, adjDictLoc, action="REMOVE")
                adjBrickD["size"] = None
                adjBrickD["parent_brick"] = None
                adjBrickD["bot_exposed"] = None
                adjBrickD["top_exposed"] = None
                brick = bpy.data.objects.get(adjBrickD["name"])
                if brick: delete(brick)
                self.adjBricksCreated[side][brickNum] = False
                return True
        # if brick doesn't exist there
        else:
            # if attempting to add brick
            if addBrick:
                if checkTwoMoreAbove:
                    # check if locs available above current
                    x0, y0, z0 = adjDictLoc
                    for z in range(1, 3):
                        newKey = listToStr([x0, y0, z0 + z])
                        # if brick drawn in next loc and not just rerunning based on new direction selection
                        if (newKey in self.bricksDict and self.bricksDict[newKey]["draw"] and
                            (not self.isBrickAlreadyCreated(brickNum, side) or
                             self.adjBricksCreated[side][brickNum] not in getBrickTypes(height=3))):
                            self.report({"INFO"}, "Brick already exists in the following location: %(newKey)s" % locals())
                            self.setDirBool(side, False)
                            # reset values at failed location, in case brick was previously drawn there
                            self.adjBricksCreated[side][brickNum] = False
                            adjBrickD["draw"] = False
                            return False
                        keysToMerge.append(listToStr([x0, y0, z0 + z]))
                # update dictionary of locations above brick
                if cm.brickType == "BRICKS AND PLATES":
                    curType = self.adjBricksCreated[side][brickNum] if self.adjBricksCreated[side][brickNum] else "PLATE"
                    updateBrickSizeAndDict(dimensions, cm, self.bricksDict, [1, 1, newBrickHeight], adjacent_key, adjDictLoc, curType=curType, targetType=self.brickType)
                # update dictionary location of adjacent brick created
                adjBrickD["draw"] = True
                adjBrickD["type"] = self.brickType
                adjBrickD["flipped"] = self.bricksDict[dictKey]["flipped"]
                adjBrickD["rotated"] = self.bricksDict[dictKey]["rotated"]
                setCurBrickVal(self.bricksDict, strToList(adjacent_key))
                adjBrickD["mat_name"] = self.bricksDict[dictKey]["mat_name"]
                adjBrickD["size"] = [1, 1, newBrickHeight]
                adjBrickD["parent_brick"] = "self"
                adjBrickD["mat_name"] = self.bricksDict[dictKey]["mat_name"] if adjBrickD["mat_name"] == "" else adjBrickD["mat_name"]
                adjBrickD["nearest_face"] = self.bricksDict[dictKey]["nearest_face"] if adjBrickD["nearest_face"] is None else adjBrickD["nearest_face"]
                adjBrickD["nearest_intersection"] = self.bricksDict[dictKey]["nearest_intersection"] if adjBrickD["nearest_intersection"] is None else adjBrickD["nearest_intersection"]
                topExposed, botExposed = getBrickExposure(cm, self.bricksDict, adjacent_key)
                adjBrickD["top_exposed"] = topExposed
                adjBrickD["bot_exposed"] = botExposed
                keysToMerge.append(adjacent_key)
                # set adjBricksCreated to target brick type for current side
                self.adjBricksCreated[side][brickNum] = self.brickType

                return True
            # if attempting to remove brick
            else:
                self.report({"INFO"}, "Brick does not exist in the following location: %(adjacent_key)s" % locals())
                return False

    #############################################
