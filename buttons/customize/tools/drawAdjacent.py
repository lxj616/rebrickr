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

# Bricker imports
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
    bl_idname = "bricker.draw_adjacent"
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
            if [False]*6 == [createAdjBricks[i] or self.adjBricksCreated[i][0] for i in range(6)]:
                return {"CANCELLED"}
            # push to undo stack
            self.undo_stack.matchPythonToBlenderState()
            if self.orig_undo_stack_length == self.undo_stack.getLength():
                self.undo_stack.undo_push('draw_adjacent')
            scn, cm, _ = getActiveContextInfo()
            scn.update()
            self.undo_stack.iterateStates(cm)
            # get fresh copy of self.bricksDict
            self.bricksDict, _ = getBricksDict(cm=cm)
            # initialize vars
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
                # if checking beneath obj, check 3 keys below instead of 1 key below
                if i == 5 and "PLATES" in cm.brickType:
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
                        self.bricksDict = verifyBrickExposureAboveAndBelow(adjDictLoc.copy(), self.bricksDict, decriment=decriment + 1, zNeg=self.zNeg, zPos=self.zPos)

            # recalculate val for each bricksDict key in original brick
            brickLocs = [[x, y, z] for z in range(z0, z0 + objSize[2], zStep) for y in range(y0, y0 + objSize[1]) for x in range(x0, x0 + objSize[0])]
            for curLoc in brickLocs:
                setCurBrickVal(self.bricksDict, curLoc)

            # attempt to merge created bricks
            tallBandP = "PLATES" in cm.brickType and self.brickType in getBrickTypes(height=3)
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
            self.zPos, self.zNeg, self.yPos, self.yNeg, self.xPos, self.xNeg = [False] * 6

            # initialize vars for self.adjDKLs setup
            dictKey, dictLoc = getDictKey(obj.name)
            objSize = self.bricksDict[dictKey]["size"]
            x,y,z = dictLoc
            sX, sY, sZ = objSize[0], objSize[1], objSize[2] // getZStep(cm)
            self.adjDKLs = [[],[],[],[],[],[]]
            # initialize ranges
            rgs = [range(x, x + sX),
                   range(y, y + sY),
                   range(z, z + sZ)]
            # set up self.adjDKLs
            self.adjDKLs[0] += [[x + sX, y0, z0] for z0 in rgs[2] for y0 in rgs[1]]
            self.adjDKLs[1] += [[x - 1, y0, z0]  for z0 in rgs[2] for y0 in rgs[1]]
            self.adjDKLs[2] += [[x0, y + sY, z0] for z0 in rgs[2] for x0 in rgs[0]]
            self.adjDKLs[3] += [[x0, y - 1, z0]  for z0 in rgs[2] for x0 in rgs[0]]
            self.adjDKLs[4] += [[x0, y0, z + sZ] for y0 in rgs[1] for x0 in rgs[0]]
            self.adjDKLs[5] += [[x0, y0, z - 1]  for y0 in rgs[1] for x0 in rgs[0]]

            # initialize self.adjBricksCreated
            self.adjBricksCreated = [[False] * len(self.adjDKLs[i]) for i in range(6)]

            # initialize self.brickType
            objType = self.bricksDict[dictKey]["type"]
            try:
                self.brickType = objType or ("BRICK" if objSize[2] == 3 else "PLATE")
            except TypeError:
                pass
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
        full_d = [dimensions["width"], dimensions["width"], dimensions["height"]]
        co = list(co)
        if side in [0, 2, 4]:  # positive directions
            co[side//2] += full_d[side//2]
        else:                  # negative directions
            co[side//2] -= full_d[side//2] * (newBrickHeight if side == 5 and "PLATES" in cm.brickType else 1)
        return tuple(co)

    def isBrickAlreadyCreated(self, brickNum, side):
        return not (brickNum == len(self.adjDKLs[side]) - 1 and
                    not any(self.adjBricksCreated[side])) # evaluates True if all values in this list are False

    def toggleBrick(self, cm, dimensions, adjDictLoc, dictKey, objSize, side, brickNum, keysToMerge, addBrick=True):
        # if brick height is 3 and 'Plates' in cm.brickType
        newBrickHeight = self.getNewBrickHeight()
        checkTwoMoreAbove = "PLATES" in cm.brickType and newBrickHeight == 3

        adjacent_key, adjBrickD = self.getBrickD(adjDictLoc)

        # if key doesn't exist in bricksDict, create it
        if not adjBrickD:
            n = cm.source_name
            cm.numBricksGenerated += 1
            j = cm.numBricksGenerated
            newDictLoc = adjDictLoc.copy()
            if side in [0, 2, 4]:  # positive directions
                newDictLoc[side//2] -= 1
            else:                  # negative directions
                newDictLoc[side//2] += (newBrickHeight if side == 5 and "PLATES" in cm.brickType else 1)
            theKey = listToStr(newDictLoc)
            co0 = self.bricksDict[theKey]["co"]
            co = self.getNewCoord(cm, co0, dimensions, side, newBrickHeight)
            self.bricksDict[adjacent_key] = createBricksDictEntry(
                name=                 'Bricker_%(n)s_brick_%(j)s__%(adjacent_key)s' % locals(),
                co=                   co,
                near_face=         self.bricksDict[dictKey]["near_face"],
                near_intersection= self.bricksDict[dictKey]["near_intersection"],
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
            elif adjBrickD["created_from"] == dictKey:
                # update bricksDict values for brick being removed
                x0, y0, z0 = adjDictLoc
                brickKeys = [listToStr([x0, y0, z0 + z]) for z in range(3 if side in [4, 5] else 1)]
                for k in brickKeys:
                    self.bricksDict[k]["draw"] = False
                    setCurBrickVal(self.bricksDict, strToList(k), action="REMOVE")
                    self.bricksDict[k]["size"] = None
                    self.bricksDict[k]["parent"] = None
                    self.bricksDict[k]["bot_exposed"] = None
                    self.bricksDict[k]["top_exposed"] = None
                    self.bricksDict[k]["created_from"] = None
                self.adjBricksCreated[side][brickNum] = False
                return True
        # if brick doesn't exist there
        else:
            # if attempting to remove brick
            if not addBrick:
                self.report({"INFO"}, "Brick does not exist in the following location: %(adjacent_key)s" % locals())
                return False
            # check if locs above current are available
            if checkTwoMoreAbove:
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
                    elif side in [4, 5]:
                        keysToMerge.append(newKey)
            # update dictionary of locations above brick
            if "PLATES" in cm.brickType and side in [4, 5]:
                curType = self.adjBricksCreated[side][brickNum] if self.adjBricksCreated[side][brickNum] else "PLATE"
                updateBrickSizeAndDict(dimensions, cm, self.bricksDict, [1, 1, newBrickHeight], adjacent_key, adjDictLoc, curType=curType, targetType=self.brickType, createdFrom=dictKey)
            # update dictionary location of adjacent brick created
            adjBrickD["draw"] = True
            adjBrickD["type"] = self.brickType
            adjBrickD["flipped"] = self.bricksDict[dictKey]["flipped"]
            adjBrickD["rotated"] = self.bricksDict[dictKey]["rotated"]
            setCurBrickVal(self.bricksDict, strToList(adjacent_key))
            adjBrickD["mat_name"] = self.bricksDict[dictKey]["mat_name"]
            adjBrickD["size"] = [1, 1, newBrickHeight if side in [4, 5] else getZStep(cm)]
            adjBrickD["parent"] = "self"
            adjBrickD["mat_name"] = self.bricksDict[dictKey]["mat_name"] if adjBrickD["mat_name"] == "" else adjBrickD["mat_name"]
            adjBrickD["near_face"] = adjBrickD["near_face"] or self.bricksDict[dictKey]["near_face"]
            adjBrickD["near_intersection"] = adjBrickD["near_intersection"] or self.bricksDict[dictKey]["near_intersection"]
            topExposed, botExposed = getBrickExposure(cm, self.bricksDict, adjacent_key)
            adjBrickD["top_exposed"] = topExposed
            adjBrickD["bot_exposed"] = botExposed
            adjBrickD["created_from"] = dictKey
            keysToMerge.append(adjacent_key)
            # set adjBricksCreated to target brick type for current side
            self.adjBricksCreated[side][brickNum] = self.brickType

            return True

    #############################################
