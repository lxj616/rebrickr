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

# Rebrickr imports
from ..functions import *
from .brickify import getBricksDict, cacheBricksDict


def getDictKeyDetails(brick):
    """ get dict key details of brick """
    dictKey = brick.name.split("__")[1]
    dictKeyLoc = dictKey.split(",")
    dictKeyLoc = list(map(int, dictKeyLoc))
    return dictKey, dictKeyLoc


class splitBrick(bpy.types.Operator):
    """Split selected bricks into 1x1 bricks"""                                 # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "rebrickr.split_bricks"                                         # unique identifier for buttons and menu items to reference.
    bl_label = "Split Brick(s)"                                                 # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns False) """
        scn = bpy.context.scene
        objs = bpy.context.selected_objects
        # check that at least 1 object is selected
        if len(objs) == 0:
            return False
        # check that at least 1 selected object is a brick
        for obj in objs:
            if obj.isBrick:
                return True
        return False

    def execute(self, context):
        scn = bpy.context.scene
        selected_objects = bpy.context.selected_objects
        bricksDicts = {}

        for obj in selected_objects:
            if not obj.isBrick:
                continue

            # get cmlist item referred to by object
            for cm in scn.cmlist:
                if cm.id == obj.cmlist_id:
                    # get bricksDict for current cm
                    if cm.idx not in bricksDicts.keys():
                        # get bricksDict from cache
                        bricksDict,_ = getBricksDict("UPDATE_MODEL", cm=cm)
                        bricksDicts[cm.idx] = bricksDict
                    else:
                        # get bricksDict from bricksDicts
                        bricksDict = bricksDicts[cm.idx]

                    # get dict key details of current obj
                    dictKey, dictKeyLoc = getDictKeyDetails(obj)
                    x0,y0,z0 = dictKeyLoc
                    # get size of current brick (e.g. [2, 4, 1])
                    objSize = bricksDict[dictKey]["size"]

                    # set size of active brick's bricksDict entries to 1x1x[lastZSize]
                    zType = bricksDict[dictKey]["size"][2]
                    for x in range(x0, x0 + objSize[0]):
                        for y in range(y0, y0 + objSize[1]):
                            for z in range(z0, z0 + objSize[2]):
                                curKey = "%(x)s,%(y)s,%(z)s" % locals()
                                bricksDict[curKey]["size"] = [1, 1, zType]
                                bricksDict[curKey]["parent_brick"] = "self"
                    break

        for cm_idx in bricksDicts.keys():
            # store bricksDicts to cache
            cm = scn.cmlist[cm_idx]
            bricksDict = bricksDicts[cm_idx]
            cacheBricksDict("UPDATE_MODEL", cm, bricksDict)
            # set modelIsDirty for all changed cmlist items
            cm.modelIsDirty = True

        self.report({"INFO"}, "Brick split successful! Update model to reflect changes.")

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
        # check that at least 2 objects are selected
        if len(objs) <= 1:
            return False
        # check that at least 2 selected objects are bricks
        i = 0
        for obj in objs:
            if obj.isBrick:
                i += 1
                if i == 2:
                    return True
        return False

    def execute(self, context):
        scn = bpy.context.scene
        selected_objects = bpy.context.selected_objects
        bricks_to_merge = {}
        bricksDicts = {}

        for obj in selected_objects:
            if obj.isBrick:
                # get cmlist item referred to by object
                for cm in scn.cmlist:
                    if cm.id == obj.cmlist_id:
                        # add object to cm key in bricks_to_merge
                        if cm.idx not in bricks_to_merge.keys():
                            bricks_to_merge[cm.idx] = [obj]
                        else:
                            bricks_to_merge[cm.idx].append(obj)
                        break

        # iterate through keys in bricks_to_merge
        for cm_idx in bricks_to_merge.keys():
            cm = scn.cmlist[cm_idx]
            # sort bricks in bricks_to_merge[cm_idx] by (x+y) location
            bricks_to_merge[cm_idx].sort(key=lambda obj: int(obj.name.split("__")[1].split(",")[0]) + int(obj.name.split("__")[1].split(",")[1]))
            # get bricksDict from cache
            bricksDict,_ = getBricksDict("UPDATE_MODEL", cm=cm)
            # initialize parentObjSize
            parent_brick = None

            # iterate through objects in bricks_to_merge[cm_idx]
            for obj in bricks_to_merge[cm_idx]:
                # get dict key details of current obj
                dictKey, dictKeyLoc = getDictKeyDetails(obj)
                x0,y0,z0 = dictKeyLoc
                # get size of current brick (e.g. [2, 4, 1])
                objSize = bricksDict[dictKey]["size"]

                if objSize[0] == 1 or objSize[1] == 1:
                    if parent_brick is not None:
                        # NOTE: [0] is x, [1] is y
                        if (parentObjSize[0] in [1, objSize[0]] and
                           (x0 == x1 and y0 == y1 + 1)):

                            bricksDict[dictKey]["parent_brick"] = parent_brick["dictKey"]
                            parentObjSize[1] += objSize[1]
                            bricksDict[parent_brick["dictKey"]]["size"][1] = parentObjSize[1]
                        # TODO: change to elif when above is uncommented
                        if (parentObjSize[1] in [1, objSize[1]] and
                             (x0 == x1 + 1 and y0 == y1)):

                            bricksDict[dictKey]["parent_brick"] = parent_brick["dictKey"]
                            parentObjSize[0] += objSize[0]
                            bricksDict[parent_brick["dictKey"]]["size"][0] = parentObjSize[0]
                    else:
                        # store parent_brick object size
                        parent_brick = {"obj":obj, "dictKey":dictKey, "dictKeyLoc":dictKeyLoc}
                        parentObjSize = objSize

                # store lastDictKeyLoc
                lastDictKeyLoc = dictKeyLoc
                for i in range(3):
                    lastDictKeyLoc[i] += objSize[i] - 1
                x1,y1,z1 = lastDictKeyLoc

            # set modelIsDirty so model can be updated
            cm.modelIsDirty = True
            # store bricksDict to cache
            cacheBricksDict("UPDATE_MODEL", cm, bricksDict)

        self.report({"INFO"}, "Brick merge successful! Update model to reflect changes.")

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
        # check that at least 1 object is selected
        if len(objs) == 0:
            return False
        # check that at least 1 selected object is a brick
        for obj in objs:
            if obj.isBrick:
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
        scn = bpy.context.scene
        selected_objects = bpy.context.selected_objects
        bricksDicts = {}

        for obj in selected_objects:
            if obj.isBrick:
                # get cmlist item referred to by object
                for cm in scn.cmlist:
                    if cm.id == obj.cmlist_id:
                        # get bricksDict for current cm
                        if cm.idx not in bricksDicts.keys():
                            # get bricksDict from cache
                            bricksDict,_ = getBricksDict("UPDATE_MODEL", cm=cm)
                            bricksDicts[cm.idx] = bricksDict
                        else:
                            # get bricksDict from bricksDicts
                            bricksDict = bricksDicts[cm.idx]

                        # get dict key details of current obj
                        dictKey, dictKeyLoc = getDictKeyDetails(obj)
                        # get size of current brick (e.g. [2, 4, 1])
                        objSize = bricksDict[dictKey]["size"]

                        # set top as exposed
                        if self.side in ["TOP", "BOTH"]:
                            bricksDict[dictKey]["top_exposed"] = not bricksDict[dictKey]["top_exposed"]
                        # set bottom as exposed
                        if self.side in ["BOTTOM", "BOTH"]:
                            bricksDict[dictKey]["bot_exposed"] = not bricksDict[dictKey]["bot_exposed"]
                        break

        for cm_idx in bricksDicts.keys():
            # store bricksDicts to cache
            cm = scn.cmlist[cm_idx]
            bricksDict = bricksDicts[cm_idx]
            cacheBricksDict("UPDATE_MODEL", cm, bricksDict)
            # set modelIsDirty for all changed cmlist items
            cm.modelIsDirty = True

        self.report({"INFO"}, "Brick exposure set successfully! Update model to reflect changes.")

        return {"FINISHED"}


class drawAdjacent(bpy.types.Operator):
    """Draw brick to one side of active brick"""                                # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "rebrickr.draw_adjacent"                                        # unique identifier for buttons and menu items to reference.
    bl_label = "Draw Adjacent Bricks"                                            # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns False) """
        scn = bpy.context.scene
        objs = bpy.context.selected_objects
        # check that at least 1 object is selected
        if len(objs) == 0:
            return False
        # check that at least 1 selected object is a brick
        for obj in objs:
            if obj.isBrick:
                return True
        return True

    def __init__(self):
        scn = bpy.context.scene
        objs = bpy.context.selected_objects

        self.xPos = False
        self.xNeg = False
        self.yPos = False
        self.yNeg = False
        self.zPos = False
        self.zNeg = False

        # cycle through objects until first object that isBrick
        for obj in objs:
            if obj.isBrick:
                # get cmlist item referred to by object
                for cm in scn.cmlist:
                    if cm.id == obj.cmlist_id:
                        # get bricksDict from cache
                        self.bricksDict,_ = getBricksDict("UPDATE_MODEL", cm=cm)
                        self.cm_idx = cm.idx
                        return

    # define xPos, yPos, etc.
    zPos = bpy.props.BoolProperty(name="Top    (+Z)", default=False)
    zNeg = bpy.props.BoolProperty(name="Bottom (-Z)", default=False)
    yPos = bpy.props.BoolProperty(name="Left   (+Y)", default=False)
    yNeg = bpy.props.BoolProperty(name="Right  (-Y)", default=False)
    xPos = bpy.props.BoolProperty(name="Back   (+X)", default=False)
    xNeg = bpy.props.BoolProperty(name="Front  (-X)", default=False)

    bricksDict = {}
    cm_idx = -1

    def addBrick(self, cm, dkl, dictKey, objSize):
        adjacent_key = str(dkl).replace(" ","")[1:-1]
        try:
            adjBrickD = self.bricksDict[adjacent_key]
        except:
            self.report({"WARNING"}, "Matrix not available at the following location: " + str(dkl))
            return False
        if not adjBrickD["draw"]:
            adjBrickD["draw"] = True
            adjBrickD["val"] = 2
            adjBrickD["matName"] = self.bricksDict[dictKey]["matName"]
            adjBrickD["size"] = [1, 1, objSize[2]]
            adjBrickD["parent_brick"] = "self"
            topExposed, botExposed = getBrickExposure(cm, self.bricksDict, adjacent_key)
            adjBrickD["top_exposed"] = topExposed
            adjBrickD["bot_exposed"] = botExposed
        return True

    def execute(self, context):
        scn = bpy.context.scene
        cm = scn.cmlist[self.cm_idx]
        objs = bpy.context.selected_objects

        # iterate through objects and only operate on bricks in current model
        for obj in objs:
            if obj.isBrick and obj.cmlist_id == cm.id:
                # get dict key details of current obj
                dictKey, dictKeyLoc = getDictKeyDetails(obj)
                x,y,z = dictKeyLoc
                # get size of current brick (e.g. [2, 4, 1])
                objSize = self.bricksDict[dictKey]["size"]

                newLocs = []

                if cm.brickType in ["Bricks", "Custom"]:
                    zStep = 3
                else:
                    zStep = 1

                if self.xPos:
                    for y0 in range(y, y + objSize[1]):
                        for z0 in range(z, z + objSize[2], zStep):
                            dkl = [x + objSize[0], y0, z0]
                            returnVal = self.addBrick(cm, dkl, dictKey, objSize)
                            self.xPos = returnVal
                if self.xNeg:
                    for y0 in range(y, y + objSize[1]):
                        for z0 in range(z, z + objSize[2], zStep):
                            dkl = [x - 1, y0, z0]
                            returnVal = self.addBrick(cm, dkl, dictKey, objSize)
                            self.xNeg = returnVal
                if self.yPos:
                    for x0 in range(x, x + objSize[0]):
                        for z0 in range(z, z + objSize[2], zStep):
                            dkl = [x0, y + objSize[1], z0]
                            returnVal = self.addBrick(cm, dkl, dictKey, objSize)
                            self.yPos = returnVal
                if self.yNeg:
                    for x0 in range(x, x + objSize[0]):
                        for z0 in range(z, z + objSize[2], zStep):
                            dkl = [x0, y - 1, z0]
                            returnVal = self.addBrick(cm, dkl, dictKey, objSize)
                            self.yNeg = returnVal
                if self.zPos:
                    for x0 in range(x, x + objSize[0]):
                        for y0 in range(y, y + objSize[1]):
                            dkl = [x0, y0, z + 1]
                            returnVal = self.addBrick(cm, dkl, dictKey, objSize)
                            self.zPos = returnVal
                if self.zNeg:
                    for x0 in range(x, x + objSize[0]):
                        for y0 in range(y, y + objSize[1]):
                            dkl = [x0, y0, z - 1]
                            returnVal = self.addBrick(cm, dkl, dictKey, objSize)
                            self.zNeg = returnVal

        # set modelIsDirty so model can be updated
        cm.modelIsDirty = True
        # store bricksDict to cache
        cacheBricksDict("UPDATE_MODEL", cm, self.bricksDict)

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_popup(self, event)

class changeBrickType(bpy.types.Operator):
    """Draw brick to one side of active brick"""                                # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "rebrickr.change_brick_type"                                           # unique identifier for buttons and menu items to reference.
    bl_label = "Change Brick Type"                                              # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns False) """
        scn = bpy.context.scene
        objs = bpy.context.selected_objects
        # check that at least 1 object is selected
        if len(objs) == 0:
            return False
        # check that at least 1 selected object is a brick
        for obj in objs:
            if obj.isBrick:
                return True
        return True

    def __init__(self):
        scn = bpy.context.scene
        objs = bpy.context.selected_objects
        # cycle through objects until first object that isBrick
        for obj in objs:
            if obj.isBrick:
                # get cmlist item referred to by object
                for cm in scn.cmlist:
                    if cm.id == obj.cmlist_id:
                        # get bricksDict from cache
                        self.bricksDict,_ = getBricksDict("UPDATE_MODEL", cm=cm)
                        self.cm_idx = cm.idx
                        return

    brickType = bpy.props.EnumProperty(
        name="Brick Type",
        description="Choose what type of brick should be drawn at this location",
        items=[("STANDARD", "Standard", ""),
               ("TILE", "Tile", ""),
               ("STUD", "Stud", ""),
               ("CYLINDER", "Cylinder", ""),
               ("SLOPE", "Slope", ""),
               ("SLOPE_INVERTED", "Slope Inverted", "")],
        default="STANDARD")

    flipBrick = bpy.props.BoolProperty(
        name="Flip Brick Orientation",
        description="Flip the brick about the non-mirrored axis",
        default=False)

    bricksDict = {}
    cm_idx = -1

    def execute(self, context):
        scn = bpy.context.scene
        cm = scn.cmlist[self.cm_idx]
        objs = bpy.context.selected_objects

        # iterate through objects and only operate on bricks in current model
        for obj in objs:
            if obj.isBrick and obj.cmlist_id == cm.id:
                # get dict key details of current obj
                dictKey, dictKeyLoc = getDictKeyDetails(obj)
                x,y,z = dictKeyLoc
                # get size of current brick (e.g. [2, 4, 1])
                objSize = self.bricksDict[dictKey]["size"]

                # skip bricks that are already of type self.brickType
                if self.bricksDict[dictKey]["type"] == self.brickType:
                    continue

                # turn 1x1 & 1x2 plates into slopes
                if (self.brickType == "SLOPE" and
                   objSize[2] == 1 and
                   objSize[0] + objSize[1] in [2, 3]):
                    self.report({"INFO"}, "turn 1x1 & 1x2 plates into slopes")
                    pass
                # turn 1x2 & 1x3 bricks into slopes
                elif (self.brickType in ["SLOPE", "SLOPE_INVERTED"] and
                     objSize[2] == 3 and
                     ((objSize[0] == 1 and objSize[1] in [2, 3]) or
                      (objSize[1] == 1 and objSize[0] in [2, 3]))):
                    self.report({"INFO"}, "turn 1x2 & 1x3 bricks into slopes")
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
                    continue

                self.bricksDict[dictKey]["type"] = "SLOPE"

        # set modelIsDirty so model can be updated
        cm.modelIsDirty = True
        # store bricksDict to cache
        cacheBricksDict("UPDATE_MODEL", cm, self.bricksDict)

        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_popup(self, event)
