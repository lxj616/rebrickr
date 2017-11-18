bl_info = {
    "name"        : "Rebrickr",
    "author"      : "Christopher Gearhart <chris@bblanimation.com>",
    "version"     : (1, 0, 1),
    "blender"     : (2, 78, 0),
    "description" : "Turn any mesh into a 3D brick sculpture or simulation with the click of a button",
    "location"    : "View3D > Tools > Rebrickr",
    "warning"     : "",  # used for warning icon and text in addons panel
    "wiki_url"    : "https://www.blendermarket.com/creator/products/rebrickr/",
    "tracker_url" : "https://github.com/bblanimation/rebrickr/issues",
    "category"    : "Object"}

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
from bpy.types import Operator
from bpy.props import *

# Rebrickr imports
from ..lib.bricksDict import *
from ..functions.common import *
from ..functions.general import *
from ..buttons.brickMods import getDictKey, getAdjKeysAndBrickVals, runCreateNewBricks2
from ..buttons.delete import RebrickrDelete
from ..lib.Brick import Bricks

def deleteUnprotected(context, use_global=False):
    scn = context.scene
    protected = []
    objs = context.selected_objects
    bricksDicts = {}
    for obj in objs:
        if obj.isBrick:
            # get cmlist item referred to by object
            cm = getItemByID(scn.cmlist, obj.cmlist_id)
            # get bricksDict for current cm
            if cm.idx not in bricksDicts.keys():
                # get bricksDict from cache
                bricksDict,_ = getBricksDict("UPDATE_MODEL", cm=cm)
                bricksDicts[cm.idx] = {"dict":bricksDict, "keys_to_update":[]}
                keysToUpdate = bricksDicts[cm.idx]["keys_to_update"]
            else:
                # get bricksDict from bricksDicts
                bricksDict = bricksDicts[cm.idx]["dict"]

            # get dict key details of current obj
            dictKey, dictLoc = getDictKey(obj)
            x0,y0,z0 = dictLoc
            # get size of current brick (e.g. [2, 4, 1])
            objSize = bricksDict[dictKey]["size"]

            zStep = getZStep(cm)
            # for all locations in bricksDict covered by current obj
            for x in range(x0, x0 + objSize[0]):
                for y in range(y0, y0 + objSize[1]):
                    for z in range(z0, z0 + (objSize[2]//zStep)):
                        curKey = listToStr([x,y,z])
                        # set 'draw' to false
                        bricksDict[curKey]["draw"] = False
                        bricksDict[curKey]["val"] = 0
                        # make adjustments to adjacent bricks
                        adjKeys, adjBrickVals = getAdjKeysAndBrickVals(bricksDict, key=curKey)
                        if min(adjBrickVals) == 0 and cm.autoUpdateExposed and cm.lastSplitModel:
                            # set adjacent bricks to shell if deleted brick was on shell
                            for k0 in adjKeys:
                                if bricksDict[k0]["val"] != 0: # if adjacent brick not outside
                                    bricksDict[k0]["val"] = 1
                                    if not bricksDict[k0]["draw"]:
                                        bricksDict[k0]["draw"] = True
                                        bricksDict[k0]["size"] = [1,1,zStep]
                                        bricksDict[k0]["parent_brick"] = "self"
                                        if k0 not in keysToUpdate:
                                            # add key to simple bricksDict for drawing
                                            keysToUpdate.append(k0)
                            # if top of deleted brick was exposed, top of bricks below are now exposed
                            if bricksDict[dictKey]["top_exposed"]:
                                k0 = listToStr([x, y, z - 1])
                                if bricksDict[k0]["draw"]:
                                    if bricksDict[k0]["parent_brick"] == "self":
                                        k1 = k0
                                    else:
                                        k1 = bricksDict[k0]["parent_brick"]
                                    if not bricksDict[k1]["top_exposed"]:
                                        bricksDict[k1]["top_exposed"] = True
                                        if k1 not in keysToUpdate:
                                            # add key to simple bricksDict for drawing
                                            keysToUpdate.append(k1)
                            # if bottom of deleted brick was exposed, bottom of bricks above are now exposed
                            if bricksDict[dictKey]["bot_exposed"]:
                                k0 = listToStr([x, y, z + 1])
                                if bricksDict[k0]["draw"]:
                                    if bricksDict[k0]["parent_brick"] == "self":
                                        k1 = k0
                                    else:
                                        k1 = bricksDict[k0]["parent_brick"]
                                    if not bricksDict[k1]["bot_exposed"]:
                                        bricksDict[k1]["bot_exposed"] = True
                                        if k1 not in keysToUpdate:
                                            # add key to simple bricksDict for drawing
                                            keysToUpdate.append(k1)

        if obj.isBrickifiedObject or obj.isBrick:
            cm = None
            for cmCur in scn.cmlist:
                n = cmCur.source_name
                if obj.isBrickifiedObject:
                    cm = cmCur
                    break
                elif obj.isBrick:
                    bGroup = bpy.data.groups.get("Rebrickr_%(n)s_bricks" % locals())
                    if bGroup is not None and len(bGroup.objects) < 2:
                        cm = cmCur
                        break
            if cm is not None:
                RebrickrDelete.runFullDelete(cm=cm)
                scn.objects.active.select = False
                return protected
            else:
                obj_users_scene = len(obj.users_scene)
                scn.objects.unlink(obj)
                if use_global or obj_users_scene == 1:
                    bpy.data.objects.remove(obj, True)
        elif not obj.protected:
            obj_users_scene = len(obj.users_scene)
            scn.objects.unlink(obj)
            if use_global or obj_users_scene == 1:
                bpy.data.objects.remove(obj, True)
        else:
            print(obj.name +' is protected')
            protected.append(obj.name)

    for cm_idx in bricksDicts.keys():
        # store bricksDicts to cache
        cm = scn.cmlist[cm_idx]
        bricksDict = bricksDicts[cm_idx]["dict"]
        keysToUpdate = bricksDicts[cm_idx]["keys_to_update"]
        cacheBricksDict("UPDATE_MODEL", cm, bricksDict)
        Bricks.splitAll(bricksDict, keys=keysToUpdate, cm=cm)
        cm.buildIsDirty = True
        # draw modified bricks
        if len(keysToUpdate) > 0:
            # delete bricks that didn't get deleted already
            for k in keysToUpdate:
                brick = bpy.data.objects.get(bricksDict[k]["name"])
                delete(brick)
            # create new bricks at all keysToUpdate locations
            runCreateNewBricks2(cm, bricksDict, keysToUpdate)

    return protected

class delete_override(Operator):
    """OK?"""
    bl_idname = "object.delete"
    bl_label = "Delete"
    bl_options = {'REGISTER', 'INTERNAL'}

    use_global = BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        # return context.active_object is not None
        return True

    def runDelete(self, context):
        protected = deleteUnprotected(context, self.use_global)
        if len(protected) > 0:
            self.report({"WARNING"}, "Rebrickr is using the following object(s): " + str(protected)[1:-1])
        # push delete action to undo stack
        bpy.ops.ed.undo_push(message="Delete")

    def execute(self, context):
        try:
            self.runDelete(context)
        except:
            handle_exception()
        return {'FINISHED'}

    def invoke(self, context, event):
        # Run confirmation popup for delete action
        confirmation_returned = context.window_manager.invoke_confirm(self, event)
        if confirmation_returned != {'FINISHED'}:
            return confirmation_returned
        else:
            try:
                self.runDelete(context)
            except:
                handle_exception()
            return {'FINISHED'}
