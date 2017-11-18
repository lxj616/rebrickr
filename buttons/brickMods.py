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
# NONE!

# Blender imports
import bpy
from bpy.props import *

# Rebrickr imports
from ..functions import *
from .brickify import *
from ..lib.bricksDict import getDictKey


def runCreateNewBricks2(cm, bricksDict, keysToUpdate, selectCreated=True):
    # get arguments for createNewBricks
    n = cm.source_name
    source = bpy.data.objects.get(n + " (DO NOT RENAME)")
    source_details, dimensions = getDetailsAndBounds(source)
    Rebrickr_parent_on = "Rebrickr_%(n)s_parent" % locals()
    parent = bpy.data.objects.get(Rebrickr_parent_on)
    refLogo = RebrickrBrickify.getLogo(cm)
    action = "UPDATE_MODEL"
    # actually draw the bricks
    RebrickrBrickify.createNewBricks(source, parent, source_details, dimensions, refLogo, action, bricksDict=bricksDict, keys=keysToUpdate, createGroup=False, selectCreated=selectCreated)


class RebrickrRevertSettings(bpy.types.Operator):
    """Revert Matrix settings to save brick mods"""                             # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "rebrickr.revert_matrix_settings"                               # unique identifier for buttons and menu items to reference.
    bl_label = "Revert Matrix Settings"                                         # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns False) """
        scn = bpy.context.scene
        if scn.cmlist_index == -1:
            return False
        cm = scn.cmlist[scn.cmlist_index]
        # check that matrix settings have changed
        if cm.sourceIsDirty or (cm.matrixIsDirty and cm.lastMatrixSettings != getMatrixSettings()):
            return True
        return False

    def execute(self, context):
        try:
            revertMatrixSettings()
        except:
            handle_exception()
        return{"FINISHED"}

class splitBricks(bpy.types.Operator):
    """Split selected bricks into 1x1 bricks"""                                 # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "rebrickr.split_bricks"                                         # unique identifier for buttons and menu items to reference.
    bl_label = "Split Brick(s)"                                                 # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns False) """
        scn = bpy.context.scene
        objs = bpy.context.selected_objects
        # check that at least 1 selected object is a brick
        for obj in objs:
            if obj.isBrick:
                # get cmlist item referred to by object
                cm = getItemByID(scn.cmlist, obj.cmlist_id)
                if cm.lastBrickType != "Custom":
                    return True
        return False

    def execute(self, context):
        try:
            scn = bpy.context.scene
            selected_objects = bpy.context.selected_objects
            bricksDicts = {}

            for obj in selected_objects:
                if not obj.isBrick:
                    continue

                # get cmlist item referred to by object
                cm = getItemByID(scn.cmlist, obj.cmlist_id)
                # get bricksDict for current cm
                if cm.idx not in bricksDicts.keys():
                    # get bricksDict from cache
                    bricksDict,_ = getBricksDict("UPDATE_MODEL", cm=cm)
                    bricksDicts[cm.idx] = {"dict":bricksDict, "keys_to_update":[]}
                else:
                    # get bricksDict from bricksDicts
                    bricksDict = bricksDicts[cm.idx]["dict"]

                # get dict key details of current obj
                dictKey, dictLoc = getDictKey(obj.name)
                x0,y0,z0 = dictLoc
                # get size of current brick (e.g. [2, 4, 1])
                objSize = bricksDict[dictKey]["size"]

                # skip 1x1 bricks
                if objSize[0] + objSize[1] == 2:
                    continue

                # delete the current object
                delete(obj)

                zStep = getZStep(cm)
                # set size of active brick's bricksDict entries to 1x1x[lastZSize]
                zType = bricksDict[dictKey]["size"][2]
                for x in range(x0, x0 + objSize[0]):
                    for y in range(y0, y0 + objSize[1]):
                        for z in range(z0, z0 + objSize[2], zStep):
                            curKey = listToStr([x,y,z])
                            bricksDict[curKey]["size"] = [1, 1, zType]
                            bricksDict[curKey]["parent_brick"] = "self"
                            # add curKey to simple bricksDict for drawing
                            bricksDicts[cm.idx]["keys_to_update"].append(curKey)
            for cm_idx in bricksDicts.keys():
                # store bricksDicts to cache
                cm = scn.cmlist[cm_idx]
                bricksDict = bricksDicts[cm_idx]["dict"]
                keysToUpdate = bricksDicts[cm_idx]["keys_to_update"]
                cacheBricksDict("UPDATE_MODEL", cm, bricksDict)
                # draw modified bricks
                if len(keysToUpdate) > 0:
                    runCreateNewBricks2(cm, bricksDict, keysToUpdate)
        except:
            handle_exception()
        return{"FINISHED"}


class mergeBricks(bpy.types.Operator):
    """Merge selected bricks"""                                                 # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "rebrickr.merge_bricks"                                         # unique identifier for buttons and menu items to reference.
    bl_label = "Merge Bricks"                                                   # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns False) """
        scn = bpy.context.scene
        objs = bpy.context.selected_objects
        i = 0
        # check that at least 2 objects are selected and are bricks
        for obj in objs:
            if obj.isBrick:
                # get cmlist item referred to by object
                cm = getItemByID(scn.cmlist, obj.cmlist_id)
                if cm.lastBrickType != "Custom":
                    i += 1
                    if i == 2:
                        return True
        return False

    def execute(self, context):
        try:
            scn = bpy.context.scene
            selected_objects = bpy.context.selected_objects
            bricks_to_merge = {}
            bricksDicts = {}

            for obj in selected_objects:
                if obj.isBrick:
                    # get cmlist item referred to by object
                    cm = getItemByID(scn.cmlist, obj.cmlist_id)
                    # add object to cm key in bricks_to_merge
                    if cm.idx not in bricks_to_merge.keys():
                        bricks_to_merge[cm.idx] = [obj]
                    else:
                        bricks_to_merge[cm.idx].append(obj)

            # iterate through keys in bricks_to_merge
            for cm_idx in bricks_to_merge.keys():
                cm = scn.cmlist[cm_idx]
                # sort bricks in bricks_to_merge[cm_idx] by (x+y) location
                bricks_to_merge[cm_idx].sort(key=lambda obj: int(obj.name.split("__")[1].split(",")[0]) + int(obj.name.split("__")[1].split(",")[1]))
                # get bricksDict from cache
                bricksDict,_ = getBricksDict("UPDATE_MODEL", cm=cm)
                keysToUpdate = []
                # initialize parentObjSize
                parent_brick = None

                # iterate through objects in bricks_to_merge[cm_idx]
                for obj in bricks_to_merge[cm_idx]:
                    # get dict key details of current obj
                    dictKey, dictLoc = getDictKey(obj.name)
                    x0,y0,z0 = dictLoc
                    # get size of current brick (e.g. [2, 4, 1])
                    objSize = bricksDict[dictKey]["size"]

                    if objSize[0] == 1 or objSize[1] == 1:
                        if parent_brick is not None:
                            # NOTE: [0] is x, [1] is y
                            if (parentObjSize[0] in [1, objSize[0]] and
                               (x0 == x1 and y0 == y1 + 1)):

                                bricksDict[dictKey]["parent_brick"] = parent_brick["dictKey"]
                                parentObjSize[1] += objSize[1]
                                curBrickD = bricksDict[parent_brick["dictKey"]]
                                curBrickD["size"][1] = parentObjSize[1]
                                curBrickD["top_exposed"] = bricksDict[dictKey]["top_exposed"]
                                curBrickD["bot_exposed"] = bricksDict[dictKey]["bot_exposed"]
                                curBrickD["type"] = None
                                delete(obj)
                            # TODO: change to elif when above is uncommented
                            if (parentObjSize[1] in [1, objSize[1]] and
                                 (x0 == x1 + 1 and y0 == y1)):

                                bricksDict[dictKey]["parent_brick"] = parent_brick["dictKey"]
                                parentObjSize[0] += objSize[0]
                                curBrickD = bricksDict[parent_brick["dictKey"]]
                                curBrickD["size"][0] = parentObjSize[0]
                                curBrickD["top_exposed"] = bricksDict[dictKey]["top_exposed"]
                                curBrickD["bot_exposed"] = bricksDict[dictKey]["bot_exposed"]
                                curBrickD["type"] = None
                                delete(obj)
                        else:
                            # store parent_brick object size
                            parent_brick = {"obj":obj, "dictKey":dictKey, "dictLoc":dictLoc}
                            parentObjSize = objSize
                            keysToUpdate.append(dictKey)
                            delete(obj)

                    # store lastdictLoc
                    lastdictLoc = dictLoc
                    for i in range(3):
                        lastdictLoc[i] += objSize[i] - 1
                    x1,y1,z1 = lastdictLoc

                # store bricksDict to cache
                cacheBricksDict("UPDATE_MODEL", cm, bricksDict)
                # draw modified bricks
                if len(keysToUpdate) > 0:
                    runCreateNewBricks2(cm, bricksDict, keysToUpdate)
        except:
            handle_exception()
        return{"FINISHED"}

class setExposure(bpy.types.Operator):
    """Set exposure of bricks"""                                                # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "rebrickr.set_exposure"                                         # unique identifier for buttons and menu items to reference.
    bl_label = "Set Exposure"                                                   # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns False) """
        scn = bpy.context.scene
        objs = bpy.context.selected_objects
        # check that at least 1 selected object is a brick
        for obj in objs:
            if obj.isBrick:
                # get cmlist item referred to by object
                cm = getItemByID(scn.cmlist, obj.cmlist_id)
                if cm.lastBrickType != "Custom":
                    return True
        return False

    side = bpy.props.EnumProperty(
        items=(
            ("TOP", "Top", ""),
            ("BOTTOM", "Bottom", ""),
            ("BOTH", "Both", ""),
        ),
        default="TOP"
    )

    def execute(self, context):
        try:
            scn = bpy.context.scene
            selected_objects = bpy.context.selected_objects
            active_obj = scn.objects.active
            if active_obj is not None:
                initial_active_obj_name = active_obj.name
            else:
                initial_active_obj_name = ""

            bricksDicts = {}

            for obj in selected_objects:
                if obj.isBrick:
                    # get cmlist item referred to by object
                    cm = getItemByID(scn.cmlist, obj.cmlist_id)
                    # get bricksDict for current cm
                    if cm.idx not in bricksDicts.keys():
                        # get bricksDict from cache
                        bricksDict,_ = getBricksDict("UPDATE_MODEL", cm=cm)
                        bricksDicts[cm.idx] = {"dict":bricksDict, "keys_to_update":[]}
                    else:
                        # get bricksDict from bricksDicts
                        bricksDict = bricksDicts[cm.idx]["dict"]

                    # get dict key details of current obj
                    dictKey, dictLoc = getDictKey(obj.name)
                    # get size of current brick (e.g. [2, 4, 1])
                    objSize = bricksDict[dictKey]["size"]

                    # delete the current object
                    delete(obj)

                    # set top as exposed
                    if self.side in ["TOP", "BOTH"]:
                        bricksDict[dictKey]["top_exposed"] = not bricksDict[dictKey]["top_exposed"]
                    # set bottom as exposed
                    if self.side in ["BOTTOM", "BOTH"]:
                        bricksDict[dictKey]["bot_exposed"] = not bricksDict[dictKey]["bot_exposed"]
                    # add curKey to simple bricksDict for drawing
                    bricksDicts[cm.idx]["keys_to_update"].append(dictKey)

            for cm_idx in bricksDicts.keys():
                cm = scn.cmlist[cm_idx]
                bricksDict = bricksDicts[cm_idx]["dict"]
                keysToUpdate = bricksDicts[cm_idx]["keys_to_update"]
                # store bricksDict to cache
                cacheBricksDict("UPDATE_MODEL", cm, bricksDict)
                # draw modified bricks
                if len(keysToUpdate) > 0:
                    runCreateNewBricks2(cm, bricksDict, keysToUpdate)

            # select original brick
            orig_obj = bpy.data.objects.get(initial_active_obj_name)
            if orig_obj is not None: select(orig_obj, active=orig_obj, only=False)
        except:
            handle_exception()
        return {"FINISHED"}


def getAdjKeysAndBrickVals(bricksDict, loc=None, key=None):
    assert loc is not None or key is not None
    if loc is not None:
        x,y,z = loc
    else:
        x,y,z = strToList(key)
    adjKeys = [listToStr([x+1,y,z]),
               listToStr([x-1,y,z]),
               listToStr([x,y+1,z]),
               listToStr([x,y-1,z]),
               listToStr([x,y,z+1]),
               listToStr([x,y,z-1])]
    adjBrickVals = []
    for key in adjKeys:
        try:
            adjBrickVals.append(bricksDict[key]["val"])
        except KeyError:
            adjKeys.remove(key)
    return adjKeys, adjBrickVals

def setCurBrickVal(bricksDict, loc):
    _,adjBrickVals = getAdjKeysAndBrickVals(bricksDict, loc=loc)
    if 0 in adjBrickVals:
        newVal = 1
    else:
        highestAdjVal = max(adjBrickVals)
        newVal = highestAdjVal - 0.01
    bricksDict[listToStr(loc)]["val"] = newVal

class drawAdjacent(bpy.types.Operator):
    """Draw brick to one side of active brick"""                                # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "rebrickr.draw_adjacent"                                        # unique identifier for buttons and menu items to reference.
    bl_label = "Draw Adjacent Bricks"                                            # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
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

    def __init__(self):
        try:
            scn = bpy.context.scene
            obj = scn.objects.active

            # get cmlist item referred to by object
            cm = getItemByID(scn.cmlist, obj.cmlist_id)
            # get bricksDict from cache
            self.bricksDict,_ = getBricksDict("UPDATE_MODEL", cm=cm)
            self.cm_idx = cm.idx

            # initialize direction bools
            self.zPos = False
            self.zNeg = False
            self.yPos = False
            self.yNeg = False
            self.xPos = False
            self.xNeg = False

            # get dict key details of current obj
            dictKey, dictLoc = getDictKey(obj.name)
            x,y,z = dictLoc
            # get size of current brick (e.g. [2, 4, 1])
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
        except:
            handle_exception()

    # define direction bools
    zPos = bpy.props.BoolProperty(name="Top    (+Z)", default=False)
    zNeg = bpy.props.BoolProperty(name="Bottom (-Z)", default=False)
    yPos = bpy.props.BoolProperty(name="Left   (+Y)", default=False)
    yNeg = bpy.props.BoolProperty(name="Right  (-Y)", default=False)
    xPos = bpy.props.BoolProperty(name="Back   (+X)", default=False)
    xNeg = bpy.props.BoolProperty(name="Front  (-X)", default=False)

    bricksDict = {}
    cm_idx = -1
    adjDKLs = []

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
            self.report({"WARNING"}, "Matrix not available at the following location: %(adjacent_key)s" % locals())
            return adjacent_key, False

    def toggleBrick(self, cm, dkl, dictKey, objSize, side, brickNum, addBrick=True):
        adjacent_key, adjBrickD = self.getBrickD(dkl)
        if not adjBrickD:
            self.setDirBool(side, False)
            return False

        # if brick exists there
        if adjBrickD["draw"] and not (addBrick and self.adjBricksCreated[side][brickNum]):
            # if attempting to add brick
            if addBrick:
                # reset direction bool if no bricks could be added
                if (brickNum == len(self.adjDKLs[side]) - 1 and
                   not any(self.adjBricksCreated[side])): # evaluates True if all values in this list are False
                    self.setDirBool(side, False)
                self.report({"INFO"}, "Brick already exists in the following location: %(adjacent_key)s" % locals())
                return False
            # if attempting to remove brick
            else:
                adjBrickD["draw"] = False
                adjBrickD["val"] = 0 # TODO: set val to 0 only if adjacent to another outside brick (else set to inside (-1?))
                # adjBrickD["size"] = None
                # adjBrickD["parent_brick"] = None
                brick = bpy.data.objects.get(adjBrickD["name"])
                if brick is not None: delete(brick)
                self.adjBricksCreated[side][brickNum] = False
                return True
        # if brick doesn't exist there
        else:
            # if attempting to add brick
            if addBrick:
                adjBrickD["draw"] = True
                adjBrickD["val"] = self.bricksDict[dictKey]["val"]
                adjBrickD["mat_name"] = self.bricksDict[dictKey]["mat_name"]
                adjBrickD["size"] = [1, 1, objSize[2]]
                adjBrickD["parent_brick"] = "self"
                topExposed, botExposed = getBrickExposure(cm, self.bricksDict, adjacent_key)
                adjBrickD["top_exposed"] = topExposed
                adjBrickD["bot_exposed"] = botExposed
                self.keysToUpdate.append(adjacent_key)
                self.adjBricksCreated[side][brickNum] = True
                return True
            # if attempting to remove brick
            else:
                self.report({"INFO"}, "Brick does not exist in the following location: %(adjacent_key)s" % locals())
                return False

    def execute(self, context):
        try:
            scn = bpy.context.scene
            cm = scn.cmlist[self.cm_idx]
            obj = scn.objects.active
            initial_active_obj_name = obj.name
            self.keysToUpdate = []

            # get dict key details of current obj
            dictKey, dictLoc = getDictKey(obj.name)
            x0,y0,z0 = dictLoc
            # get size of current brick (e.g. [2, 4, 1])
            objSize = self.bricksDict[dictKey]["size"]

            # store enabled/disabled values
            createAdjBricks = [self.xPos, self.xNeg, self.yPos, self.yNeg, self.zPos, self.zNeg]

            zStep = getZStep(cm)
            # check all 6 directions for action to be executed
            for i in range(6):
                if (createAdjBricks[i] or (not createAdjBricks[i] and self.adjBricksCreated[i][0])):
                    # add or remove bricks in all adjacent locations in current direction
                    for j,dkl in enumerate(self.adjDKLs[i]):
                        self.toggleBrick(cm, dkl, dictKey, objSize, i, j, createAdjBricks[i])

            # recalculate val for each bricksDict key in original brick
            for x in range(x0, x0 + objSize[0]):
                for y in range(y0, y0 + objSize[1]):
                    for z in range(z0, z0 + objSize[2], zStep):
                        curKeyLoc = [x, y, z]
                        setCurBrickVal(self.bricksDict, curKeyLoc)

            # if bricks created on top, set top_exposed of original brick to False
            if self.zPos:
                self.bricksDict[dictKey]["top_exposed"] = False
                self.keysToUpdate.append(dictKey)
                delete(obj)
            # if bricks created on bottom, set top_exposed of original brick to False
            if self.zNeg:
                self.bricksDict[dictKey]["bot_exposed"] = False
                self.keysToUpdate.append(dictKey)
                delete(obj)

            # draw created bricks
            if len(self.keysToUpdate) > 0:
                runCreateNewBricks2(cm, self.bricksDict, self.keysToUpdate, selectCreated=False)

            # store bricksDict to cache
            cacheBricksDict("UPDATE_MODEL", cm, self.bricksDict)

            # select original brick
            orig_obj = bpy.data.objects.get(initial_active_obj_name)
            if orig_obj is not None: select(orig_obj, active=orig_obj)
        except:
            handle_exception()
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_popup(self, event)

class changeBrickType(bpy.types.Operator):
    """change brick type of active brick"""                                     # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "rebrickr.change_brick_type"                                    # unique identifier for buttons and menu items to reference.
    bl_label = "Change Brick Type"                                              # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns False) """
        scn = bpy.context.scene
        active_obj = scn.objects.active
        # check active object is not None
        if active_obj is None:
            return False
        # check that active_object is brick
        if not active_obj.isBrick:
            return False
        # get cmlist item referred to by object
        cm = getItemByID(scn.cmlist, active_obj.cmlist_id)
        # confirm that active_obj brickType is not CUSTOM
        if cm.lastBrickType == "Custom":
            return False
        return True

    def __init__(self):
        try:
            scn = bpy.context.scene
            obj = scn.objects.active
            cm = scn.cmlist[scn.cmlist_index]
            # get cmlist item referred to by object
            cm = getItemByID(scn.cmlist, obj.cmlist_id)
            # get bricksDict from cache
            self.bricksDict,_ = getBricksDict("UPDATE_MODEL", cm=cm)
            dictKey, dictLoc = getDictKey(obj.name)
            self.cm_idx = cm.idx
            curBrickType = self.bricksDict[dictKey]["type"]
            if curBrickType is not None:
                self.brickType = curBrickType
            else:
                self.brickType = "STANDARD"
        except:
            handle_exception()

    def get_items(self, context):
        scn = bpy.context.scene
        obj = scn.objects.active
        cm = scn.cmlist[scn.cmlist_index]
        items = [("STANDARD", "Standard", "")]

        dictKey, dictLoc = getDictKey(obj.name)
        bricksDict,_ = getBricksDict("UPDATE_MODEL", cm=cm)
        objSize = bricksDict[dictKey]["size"]

        if (objSize[2] == 3 and
           (objSize[0] + objSize[1] in [3,4,5,6,7] or
           (objSize[0] == 6 and objSize[1] == 2) or
           (objSize[0] == 2 and objSize[1] == 6))):
            items.append(("SLOPE", "Slope", ""))
        if (objSize[2] == 3 and
           (objSize[0] + objSize[1] < 6 and objSize[0] + objSize[1] > 2)):
            items.append(("SLOPE_INVERTED", "Slope Inverted", ""))
        if objSize[0] + objSize[1] == 2:
            if objSize[2] == 3:
                items.append(("CYLINDER", "Cylinder", ""))
            if objSize[2] == 1:
                items.append(("STUD", "Stud", ""))
        if objSize[2] == 1:
            items.append(("TILE", "Tile", ""))
        return items

    brickType = bpy.props.EnumProperty(
        name="Brick Type",
        description="Choose what type of brick should be drawn at this location",
        items=get_items,
        default=None)

    flipBrick = bpy.props.BoolProperty(
        name="Flip Brick Orientation",
        description="Flip the brick about the non-mirrored axis",
        default=False)

    bricksDict = {}
    cm_idx = -1

    def execute(self, context):
        try:
            scn = bpy.context.scene
            cm = scn.cmlist[self.cm_idx]
            obj = scn.objects.active

            # get dict key details of current obj
            dictKey, dictLoc = getDictKey(obj.name)
            x0,y0,z0 = dictLoc
            # get size of current brick (e.g. [2, 4, 1])
            objSize = self.bricksDict[dictKey]["size"]

            # skip bricks that are already of type self.brickType
            if self.bricksDict[dictKey]["type"] == self.brickType:
                return {"CANCELLED"}

            # turn 1x1 & 1x2 plates into slopes
            if (self.brickType == "SLOPE" and
               objSize[2] == 1 and
               objSize[0] + objSize[1] in [2, 3]):
                self.report({"INFO"}, "turn 1x1 & 1x2 plates into slopes")
                pass
            # turn 1x2 & 1x3 bricks into inverted slopes
            elif (self.brickType == "SLOPE_INVERTED" and
                 objSize[2] == 3 and
                 ((objSize[0] == 1 and objSize[1] in [2, 3]) or
                  (objSize[1] == 1 and objSize[0] in [2, 3]))):
                self.report({"INFO"}, "turn 1x2 & 1x3 bricks into inverted slopes")
                pass
            # turn 1x2 & 1x3 bricks into slopes
            elif (self.brickType == "SLOPE" and
                 objSize[2] == 3 and
                 ((objSize[0] == 1 and objSize[1] in [2, 3, 4]) or
                  (objSize[1] == 1 and objSize[0] in [2, 3, 4]))):
                self.report({"INFO"}, "turn 1x2, 1x3 & 1x4 bricks into slopes")
                pass
            # turn plates into tiles
            elif (self.brickType == "TILE" and
                  objSize[2] == 1):
                self.report({"INFO"}, "turn plates into tiles")
                pass
            # turn 1x1 plates into studs
            elif (self.brickType == "STUD" and
                  objSize[0] + objSize[1] == 2 and
                  objSize[2] == 1):
                self.report({"INFO"}, "turn 1x1 plates into studs")
                pass
            # turn 1x1 bricks into cylinders
            elif (self.brickType == "CYLINDER" and
                  objSize[0] + objSize[1] == 2 and
                  objSize[2] == 3):
                self.report({"INFO"}, "turn 1x1 bricks into cylinders")
                pass
            # skip anything else
            else:
                return {"CANCELLED"}

            # set type of parent_brick to self.brickType
            self.bricksDict[dictKey]["type"] = self.brickType

            # store bricksDict to cache
            cacheBricksDict("UPDATE_MODEL", cm, self.bricksDict)
        except:
            handle_exception()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_popup(self, event)

class redrawBricks(bpy.types.Operator):
    """redraw selected bricks from bricksDict"""                                # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "rebrickr.redraw_bricks"                                        # unique identifier for buttons and menu items to reference.
    bl_label = "Redraw Bricks"                                                  # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    # TODO: Add support for redrawing custom objects

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns False) """
        scn = bpy.context.scene
        objs = bpy.context.selected_objects
        # check that at least 1 selected object is a brick
        for obj in objs:
            if obj.isBrick:
                return True
        return False

    def execute(self, context):
        try:
            scn = bpy.context.scene
            selected_objects = bpy.context.selected_objects
            active_obj = scn.objects.active
            if active_obj is not None:
                initial_active_obj_name = active_obj.name
            else:
                initial_active_obj_name = ""

            bricksDicts = {}

            for obj in selected_objects:
                if obj.isBrick:
                    # get cmlist item referred to by object
                    cm = getItemByID(scn.cmlist, obj.cmlist_id)
                    # get bricksDict for current cm
                    if cm.idx not in bricksDicts.keys():
                        # get bricksDict from cache
                        bricksDict,_ = getBricksDict("UPDATE_MODEL", cm=cm)
                        bricksDicts[cm.idx] = {"dict":bricksDict, "keys_to_update":[]}
                    else:
                        # get bricksDict from bricksDicts
                        bricksDict = bricksDicts[cm.idx]["dict"]

                    # get dict key details of current obj
                    dictKey, dictLoc = getDictKey(obj.name)

                    # delete the current object
                    delete(obj)

                    # add curKey to simple bricksDict for drawing
                    bricksDicts[cm.idx]["keys_to_update"].append(dictKey)

            for cm_idx in bricksDicts.keys():
                cm = scn.cmlist[cm_idx]
                bricksDict = bricksDicts[cm_idx]["dict"]
                keysToUpdate = bricksDicts[cm_idx]["keys_to_update"]
                # draw modified bricks
                if len(keysToUpdate) > 0:
                    runCreateNewBricks2(cm, bricksDict, keysToUpdate)

            # select original brick
            orig_obj = bpy.data.objects.get(initial_active_obj_name)
            if orig_obj is not None: select(orig_obj, active=orig_obj, only=False)
        except:
            handle_exception()
        return {"FINISHED"}
