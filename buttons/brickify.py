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
import random
import time
import bmesh
import os
import sys
import math
import json

# Blender imports
import bpy
from mathutils import Matrix, Vector, Euler
props = bpy.props

# Addon imports
from .customize.undo_stack import *
from .materials import BrickerApplyMaterial
from .delete import BrickerDelete
from .bevel import BrickerBevel
from .cache import *
from ..lib.bricksDict import *
# from ..lib.rigid_body_props import *
from ..functions import *


def updateCanRun(type):
    scn, cm, n = getActiveContextInfo()
    if createdWithUnsupportedVersion(cm):
        return True
    elif scn.cmlist_index == -1:
        return False
    else:
        commonNeedsUpdate = (cm.logoDetail != "NONE" and cm.logoDetail != "LEGO") or cm.brickType == "CUSTOM" or cm.modelIsDirty or cm.matrixIsDirty or cm.internalIsDirty or cm.buildIsDirty or cm.bricksAreDirty
        if type == "ANIMATION":
            return commonNeedsUpdate or (cm.materialType != "CUSTOM" and cm.materialIsDirty)
        elif type == "MODEL":
            Bricker_bricks_gn = "Bricker_%(n)s_bricks" % locals()
            return commonNeedsUpdate or (groupExists(Bricker_bricks_gn) and len(bpy.data.groups[Bricker_bricks_gn].objects) == 0) or (cm.materialType != "CUSTOM" and (cm.materialType != "RANDOM" or cm.splitModel or cm.lastMaterialType != cm.materialType or cm.materialIsDirty) and cm.materialIsDirty)


def importLogo():
    """ import logo object from Bricker addon folder """
    addonsPath = bpy.utils.user_resource('SCRIPTS', "addons")
    Bricker = bpy.props.bricker_module_name
    logoObjPath = "%(addonsPath)s/%(Bricker)s/lego_logo.obj" % locals()
    bpy.ops.import_scene.obj(filepath=logoObjPath)
    logoObj = bpy.context.selected_objects[0]
    return logoObj


class BrickerBrickify(bpy.types.Operator):
    """ Create brick sculpture from source object mesh """
    bl_idname = "bricker.brickify"
    bl_label = "Create/Update Brick Model from Source Object"
    bl_options = {"REGISTER", "UNDO"}

    ################################################
    # Blender Operator methods

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns false) """
        scn = bpy.context.scene
        if scn.cmlist_index == -1:
            return False
        cm = scn.cmlist[scn.cmlist_index]
        if ((cm.animated and (not updateCanRun("ANIMATION") and not cm.animIsDirty))
           or (cm.modelCreated and not updateCanRun("MODEL"))):
            return False
        return True

    def execute(self, context):
        scn, cm, _ = getActiveContextInfo()
        scn.Bricker_runningBlockingOperation = True
        try:
            previously_animated = cm.animated
            previously_model_created = cm.modelCreated
            self.runBrickify(context)
        except KeyboardInterrupt:
            if self.action in ["CREATE", "ANIMATE"]:
                for n in self.createdObjects:
                    obj = bpy.data.objects.get(n)
                    if obj:
                        bpy.data.objects.remove(obj, True)
                for n in self.createdGroups:
                    group = bpy.data.groups.get(n)
                    if group:
                        bpy.data.groups.remove(group)
                if self.source:
                    self.source.protected = False
                    select(self.source, active=self.source)
                cm.animated = previously_animated
                cm.modelCreated = previously_model_created
            print()
            self.report({"WARNING"}, "Process forcably interrupted with 'KeyboardInterrupt'")
        except:
            handle_exception()
        scn.Bricker_runningBlockingOperation = False
        return{"FINISHED"}

    ################################################
    # initialization method

    def __init__(self):
        scn, cm, _ = getActiveContextInfo()
        # push to undo stack
        self.undo_stack = UndoStack.get_instance()
        self.undo_stack.undo_push('brickify', affected_ids=[cm.id])
        # initialize vars
        self.createdObjects = []
        self.createdGroups = []
        self.setAction(cm)
        self.source = self.getObjectToBrickify(cm)

    #############################################
    # class methods

    @timed_call('Total Time Elapsed')
    def runBrickify(self, context):
        # set up variables
        scn, cm, n = getActiveContextInfo()
        self.undo_stack.iterateStates(cm)
        Bricker_bricks_gn = "Bricker_%(n)s_bricks" % locals()
        # ensureObjNamesUnique(getSafeScn())

        # get source and initialize values
        source = self.getObjectToBrickify(cm)
        source["old_parent"] = ""
        source.cmlist_id = cm.id
        skipTransAndAnimData = cm.animated or (cm.splitModel or cm.lastSplitModel) and (matrixReallyIsDirty(cm) or cm.buildIsDirty)

        # # check if source object is smoke simulation domain
        cm.isSmoke = is_smoke(source)
        if cm.isSmoke != cm.lastIsSmoke:
            cm.matrixIsDirty = True

        # clear cache if updating from previous version
        if createdWithUnsupportedVersion(cm) and "UPDATE" in self.action:
            Caches.clearCache(cm)
            cm.matrixIsDirty = True

        # make sure matrix really is dirty
        if cm.matrixIsDirty:
            _, loadedFromCache = getBricksDict(dType="MODEL", cm=cm)
            if not matrixReallyIsDirty(cm) and loadedFromCache:
                cm.matrixIsDirty = False

        if not self.isValid(scn, cm, source, Bricker_bricks_gn):
            return {"CANCELLED"}

        if "ANIM" not in self.action:
            self.brickifyModel(skipTransAndAnimData)
        else:
            self.brickifyAnimation()
            cm.animIsDirty = False

        # set cmlist_id for all created objects
        for obj_name in self.createdObjects:
            obj = bpy.data.objects.get(obj_name)
            if obj:
                obj.cmlist_id = cm.id

        # # set final variables
        cm.lastLogoDetail = cm.logoDetail
        cm.lastSplitModel = cm.splitModel
        cm.lastBrickType = cm.brickType
        cm.lastMaterialType = cm.materialType
        cm.lastShellThickness = cm.shellThickness
        cm.lastMatShellDepth = cm.matShellDepth
        cm.lastMatrixSettings = getMatrixSettings()
        cm.lastIsSmoke = cm.isSmoke
        cm.materialIsDirty = False
        cm.modelIsDirty = False
        cm.buildIsDirty = False
        cm.bricksAreDirty = False
        cm.matrixIsDirty = False
        cm.matrixLost = False
        cm.internalIsDirty = False
        cm.modelCreated = "ANIM" not in self.action
        cm.animated = "ANIM" in self.action
        cm.version = bpy.props.bricker_version
        cm.exposeParent = False

        # unlink source from scene and link to safe scene
        if source.name in scn.objects.keys():
            safeUnlink(source, hide=False)

        disableRelationshipLines()

    def brickifyModel(self, skipTransAndAnimData=False):
        """ create brick model """
        # set up variables
        scn, cm, n = getActiveContextInfo()
        origFrame = None
        source = None
        Bricker_parent_on = "Bricker_%(n)s_parent" % locals()

        if self.action == "CREATE":
            # set modelCreatedOnFrame
            cm.modelCreatedOnFrame = scn.frame_current
        else:
            origFrame = scn.frame_current
            scn.frame_set(cm.modelCreatedOnFrame)

        # if there are no changes to apply, simply return "FINISHED"
        if self.action in ["UPDATE_MODEL"] and not updateCanRun("MODEL"):
            return{"FINISHED"}

        getSafeScn().update()

        if (matrixReallyIsDirty(cm) or self.action != "UPDATE_MODEL") and cm.customized:
            cm.customized = False

        # delete old bricks if present
        if self.action.startswith("UPDATE") and (matrixReallyIsDirty(cm) or cm.buildIsDirty or cm.lastSplitModel != cm.splitModel):
            # skip source, dupes, and parents
            trans_and_anim_data = BrickerDelete.cleanUp("MODEL", skipDupes=True, skipParents=True, skipSource=True, skipTransAndAnimData=skipTransAndAnimData)[4]
        else:
            storeTransformData(cm, None)
            trans_and_anim_data = []

        if self.action == "CREATE":
            # duplicate source
            sourceDup = duplicateObj(self.source, link=True)
            sourceDup.name = self.source.name + "_duplicate"
            if cm.useLocalOrient:
                sourceDup.rotation_mode = "XYZ"
                sourceDup.rotation_euler = Euler((0, 0, 0))
            self.createdObjects.append(sourceDup.name)
            self.source.select = False
            # remove modifiers and constraints
            for mod in sourceDup.modifiers:
                sourceDup.modifiers.remove(mod)
            for constraint in sourceDup.constraints:
                sourceDup.constraints.remove(constraint)
            # set up sourceDup["old_parent"] and remove sourceDup parent
            sourceDup["frame_parent_cleared"] = -1
            if sourceDup.parent:
                sourceDup["old_parent"] = sourceDup.parent.name
                sourceDup["frame_parent_cleared"] = scn.frame_current
                select(sourceDup, active=True)
                bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
            # send to new mesh
            sourceDup.data = self.source.to_mesh(scn, True, 'PREVIEW')
            # apply transformation data
            select(sourceDup, active=True)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            scn.update()
        else:
            # get previously created source duplicate
            sourceDup = bpy.data.objects.get(n + "_duplicate")
        # if duplicate not created, sourceDup is just original source
        sourceDup = sourceDup or self.source

        # link sourceDup if it isn't in scene
        if sourceDup.name not in scn.objects.keys():
            safeLink(sourceDup)
            scn.update()

        # get sourceDup_details and dimensions
        sourceDup_details, dimensions = getDetailsAndBounds(sourceDup)

        if self.action == "CREATE":
            # set sourceDup model height for display in UI
            cm.modelHeight = sourceDup_details.dist.z

        # get parent object
        parent = bpy.data.objects.get(Bricker_parent_on)
        # if parent doesn't exist, get parent with new location
        parentLoc = sourceDup_details.mid
        if parent is None:
            parent = self.getNewParent(Bricker_parent_on, parentLoc)
            cm.parent_name = parent.name
        parent["loc_diff"] = self.source.location - parentLoc
        self.createdObjects.append(parent.name)

        # update refLogo
        logo_details, refLogo = self.getLogo(scn, cm, dimensions)

        # create new bricks
        group_name = self.createNewBricks(sourceDup, parent, sourceDup_details, dimensions, refLogo, logo_details, self.action, curFrame=None, sceneCurFrame=None, origSource=self.source)

        bGroup = bpy.data.groups.get(group_name)
        if bGroup:
            self.createdGroups.append(group_name)
            # transform bricks to appropriate location
            self.transformBricks(bGroup, cm, parent, self.source, sourceDup_details, self.action)
            # match brick layers to source layers
            for obj in bGroup.objects:
                obj.layers = self.source.layers
            # apply old animation data to objects
            for d0 in trans_and_anim_data:
                obj = bpy.data.objects.get(d0["name"])
                if obj is not None:
                    obj.location = d0["loc"]
                    obj.rotation_euler = d0["rot"]
                    obj.scale = d0["scale"]
                    if d0["action"] is not None:
                        obj.animation_data_create()
                        obj.animation_data.action = d0["action"]

        # unlink source duplicate if created
        if sourceDup != self.source and sourceDup.name in scn.objects.keys():
            safeUnlink(sourceDup)

        # add bevel if it was previously added
        if cm.bevelAdded:
            bricks = getBricks(cm, typ="MODEL")
            BrickerBevel.runBevelAction(bricks, cm)

        # set active frame to original active frame
        if origFrame:
            scn.frame_set(origFrame)

        cm.lastSourceMid = vecToStr(parentLoc)

    def brickifyAnimation(self):
        """ create brick animation """
        # set up variables
        scn, cm, n = getActiveContextInfo()
        Bricker_parent_on = "Bricker_%(n)s_parent" % locals()
        sceneCurFrame = scn.frame_current
        objsToSelect = []

        if self.action == "UPDATE_ANIM":
            safeLink(self.source)
            self.source.name = cm.source_name  # fixes issue with smoke simulation cache

        # if there are no changes to apply, simply return "FINISHED"
        self.updatedFramesOnly = False
        if self.action == "UPDATE_ANIM" and not updateCanRun("ANIMATION"):
            if cm.animIsDirty:
                self.updatedFramesOnly = True
            else:
                return "FINISHED"

        if (self.action == "ANIMATE" or cm.matrixIsDirty or cm.animIsDirty) and not self.updatedFramesOnly:
            Caches.clearCache(cm, brick_mesh=False)

        if cm.splitModel:
            cm.splitModel = False

        # delete old bricks if present
        if self.action.startswith("UPDATE") and (matrixReallyIsDirty(cm) or cm.buildIsDirty or cm.lastSplitModel != cm.splitModel or self.updatedFramesOnly):
            preservedFrames = None
            if self.updatedFramesOnly:
                # preserve duplicates, parents, and bricks for frames that haven't changed
                preservedFrames = [cm.startFrame, cm.stopFrame]
            BrickerDelete.cleanUp("ANIMATION", skipDupes=not self.updatedFramesOnly, skipParents=not self.updatedFramesOnly, preservedFrames=preservedFrames, source_name=self.source.name)

        # get parent object
        parent0 = bpy.data.objects.get(Bricker_parent_on)
        if parent0 is None:
            parent0 = self.getNewParent(Bricker_parent_on, self.source.location)
            cm.parent_name = parent0.name
        self.createdObjects.append(parent0.name)

        # begin drawing status to cursor
        wm = bpy.context.window_manager
        wm.progress_begin(0, cm.stopFrame + 1 - cm.startFrame)

        # prepare duplicate objects for animation
        duplicates = self.getDuplicateObjects(scn, cm, cm.source_name, cm.startFrame, cm.stopFrame)

        # iterate through frames of animation and generate Brick Model
        for curFrame in range(cm.startFrame, cm.stopFrame + 1):

            if self.updatedFramesOnly and cm.lastStartFrame <= curFrame and curFrame <= cm.lastStopFrame:
                print("skipped frame %(curFrame)s" % locals())
                continue
            scn.frame_set(curFrame)
            # get duplicated source
            source = duplicates[curFrame]["obj"]

            # get source_details and dimensions
            source_details, dimensions = getDetailsAndBounds(source)

            # update refLogo
            logo_details, refLogo = self.getLogo(scn, cm, dimensions)

            if self.action == "ANIMATE":
                # set source model height for display in UI
                cm.modelHeight = source_details.dist.z

            # set up parent for this layer
            # TODO: Remove these from memory in the delete function, or don't use them at all
            p_name = "%(Bricker_parent_on)s_f_%(curFrame)s" % locals()
            parent = bpy.data.objects.get(p_name)
            if parent is None:
                m = bpy.data.meshes.new("%(p_name)s_mesh" % locals())
                parent = bpy.data.objects.new(p_name, m)
                parent.location = source_details.mid - parent0.location
                parent.parent = parent0
                scn.objects.link(parent)
                scn.update()
                safeUnlink(parent)
                self.createdObjects.append(parent.name)

            # create new bricks
            try:
                group_name = self.createNewBricks(source, parent, source_details, dimensions, refLogo, logo_details, self.action, curFrame=curFrame, sceneCurFrame=sceneCurFrame, origSource=self.source, selectCreated=False)
                self.createdGroups.append(group_name)
            except KeyboardInterrupt:
                self.report({"WARNING"}, "Process forcably interrupted with 'KeyboardInterrupt'")
                if curFrame != cm.startFrame:
                    wm.progress_end()
                    cm.lastStartFrame = cm.startFrame
                    cm.lastStopFrame = curFrame - 1
                    scn.frame_set(sceneCurFrame)
                    cm.animated = True
                return

            # get object with created bricks
            obj = bpy.data.groups[group_name].objects[0]
            # hide obj unless on scene current frame
            showCurObj = (curFrame == cm.startFrame and sceneCurFrame < cm.startFrame) or curFrame == sceneCurFrame or (curFrame == cm.stopFrame and sceneCurFrame > cm.stopFrame)
            if not showCurObj:
                obj.hide = True
                obj.hide_render = True
            # lock location, rotation, and scale of created bricks
            obj.lock_location = [True, True, True]
            obj.lock_rotation = [True, True, True]
            obj.lock_scale    = [True, True, True]
            # match brick layers to source layers
            obj.layers = self.source.layers

            wm.progress_update(curFrame-cm.startFrame)
            print('-'*100)
            print("completed frame " + str(curFrame))
            print('-'*100)

        wm.progress_end()
        cm.lastStartFrame = cm.startFrame
        cm.lastStopFrame = cm.stopFrame
        scn.frame_set(sceneCurFrame)

        # add bevel if it was previously added
        if cm.bevelAdded:
            bricks = getBricks(cm, typ="ANIM")
            BrickerBevel.runBevelAction(bricks, cm)

    @classmethod
    def createNewBricks(self, source, parent, source_details, dimensions, refLogo, logo_details, action, cm=None, curFrame=None, sceneCurFrame=None, bricksDict=None, keys="ALL", clearExistingGroup=True, selectCreated=False, printStatus=True, redraw=False, origSource=None):
        """ gets/creates bricksDict, runs makeBricks, and caches the final bricksDict """
        scn = bpy.context.scene
        cm = cm or scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        _, _, _, brickScale, customData = getArgumentsForBricksDict(cm, source=source, source_details=source_details, dimensions=dimensions)
        updateCursor = action in ["CREATE", "UPDATE_MODEL"]  # evaluates to boolean value
        if bricksDict is None:
            # multiply brickScale by offset distance
            brickScale2 = brickScale if cm.brickType != "CUSTOM" else vec_mult(brickScale, Vector(cm.distOffset))
            # get bricks dictionary
            bricksDict, loadedFromCache = getBricksDict(dType=action, source=source, source_details=source_details, dimensions=dimensions, brickScale=brickScale2, updateCursor=updateCursor, curFrame=curFrame, origSource=origSource, restrictContext=False)
        else:
            loadedFromCache = True
        # reset all values for certain keys in bricksDict dictionaries
        if cm.buildIsDirty and loadedFromCache:
            threshold = getThreshold(cm)
            for kk in bricksDict:
                bD = bricksDict[kk]
                if keys == "ALL" or kk in keys:
                    bD["size"] = None
                    bD["parent"] = None
                    bD["top_exposed"] = None
                    bD["bot_exposed"] = None
                    if cm.lastShellThickness != cm.shellThickness:
                        bD["draw"] = bD["val"] >= threshold
                else:
                    # don't merge bricks not in 'keys'
                    bD["attempted_merge"] = True
        elif redraw:
            for kk in keys:
                bricksDict[kk]["attempted_merge"] = False
        if not loadedFromCache or cm.internalIsDirty:
            updateInternal(bricksDict, cm, keys, clearExisting=loadedFromCache)
            cm.buildIsDirty = True
        # update materials in bricksDict
        if cm.materialType != "NONE" and (cm.materialIsDirty or cm.matrixIsDirty or cm.animIsDirty): bricksDict = updateMaterials(bricksDict, source, origSource, curFrame)
        # make bricks
        group_name = 'Bricker_%(n)s_bricks_f_%(curFrame)s' % locals() if curFrame is not None else "Bricker_%(n)s_bricks" % locals()
        bricksCreated, bricksDict = makeBricks(source, parent, refLogo, logo_details, dimensions, bricksDict, cm=cm, split=cm.splitModel, brickScale=brickScale, customData=customData, group_name=group_name, clearExistingGroup=clearExistingGroup, frameNum=curFrame, cursorStatus=updateCursor, keys=keys, printStatus=printStatus, redraw=redraw)
        if selectCreated and len(bricksCreated) > 0:
            select(bricksCreated, active=bricksCreated[0], only=True)
        # store current bricksDict to cache
        cacheBricksDict(action, cm, bricksDict, curFrame=curFrame)
        return group_name

    def isValid(self, scn, cm, source, Bricker_bricks_gn):
        """ returns True if brickify action can run, else report WARNING/ERROR and return False """
        if (cm.brickType == "CUSTOM" or cm.hasCustomObj1 or cm.hasCustomObj2 or cm.hasCustomObj3):
            warningMsg = customValidObject(cm)
            if warningMsg is not None:
                self.report({"WARNING"}, warningMsg)
                return False
        if len(cm.source_name) > 30:
            self.report({"WARNING"}, "Source object name too long (must be <= 30 characters)")
        if cm.materialType == "CUSTOM" and cm.materialName != "" and bpy.data.materials.find(cm.materialName) == -1:
            n = cm.materialName
            self.report({"WARNING"}, "Custom material '%(n)s' could not be found" % locals())
            return False
        if cm.materialType == "SOURCE" and cm.colorSnap == "ABS":
            if not hasattr(scn, "isBrickMaterialsInstalled") or not scn.isBrickMaterialsInstalled:
                self.report({"WARNING"}, "ABS Plastic Materials must be installed from Blender Market")
                return False
            matObj = getMatObject(cm, typ="ABS")
            if len(matObj.data.materials) == 0:
                self.report({"WARNING"}, "No ABS Plastic Materials found in Materials to be used")
                return False

        source["ignored_mods"] = ""
        if self.action in ["CREATE", "ANIMATE"]:
            # verify function can run
            if groupExists(Bricker_bricks_gn):
                self.report({"WARNING"}, "Brickified Model already created.")
                return False
            # verify source exists and is of type mesh
            if cm.source_name == "":
                self.report({"WARNING"}, "Please select a mesh to Brickify")
                return False
            if cm.source_name[:9] == "Bricker_" and (cm.source_name[-7:] == "_bricks" or cm.source_name[-9:] == "_combined"):
                self.report({"WARNING"}, "Cannot Brickify models created with the Bricker")
                return False
            if source is None:
                n = cm.source_name
                self.report({"WARNING"}, "'%(n)s' could not be found" % locals())
                return False
            if source.type != "MESH":
                self.report({"WARNING"}, "Only 'MESH' objects can be Brickified. Please select another object (or press 'ALT-C to convert object to mesh).")
                return False
            # verify source is not a rigid body
            if source.rigid_body is not None:
                self.report({"WARNING"}, "First bake rigid body transformations to keyframes (SPACEBAR > Bake To Keyframes).")
                return False

        # Verify smoke simulation is set up correctly
        for mod in source.modifiers:
            if mod.type == "SMOKE" and mod.domain_settings and mod.show_viewport:
                if not bpy.data.is_saved:
                    self.report({"WARNING"}, "Blend file must be saved before brickifying '" + str(mod.type) + "' modifiers.")
                    return False

        if self.action in ["ANIMATE", "UPDATE_ANIM"]:
            # verify start frame is less than stop frame
            if cm.startFrame > cm.stopFrame:
                self.report({"ERROR"}, "Start frame must be less than or equal to stop frame (see animation tab below).")
                return False

        if self.action in ["UPDATE_MODEL"]:
            # make sure 'Bricker_[source name]_bricks' group exists
            if not groupExists(Bricker_bricks_gn):
                self.report({"WARNING"}, "Brickified Model doesn't exist. Create one with the 'Brickify Object' button.")
                return False

        # check that custom logo object exists in current scene and is of type "MESH"
        if cm.logoDetail == "CUSTOM" and cm.brickType != "CUSTOM":
            if cm.logoObjectName == "":
                self.report({"WARNING"}, "Custom logo object not specified.")
                return False
            logoObject = bpy.data.objects.get(cm.logoObjectName)
            if logoObject is None:
                n = cm.logoObjectName
                self.report({"WARNING"}, "Custom logo object '%(n)s' could not be found" % locals())
                return False
            if cm.logoObjectName == cm.source_name and (not (cm.animated or cm.modelCreated) or logoObject.protected):
                self.report({"WARNING"}, "Source object cannot be its own logo.")
                return False
            if logoObject.type != "MESH":
                self.report({"WARNING"}, "Custom logo object is not of type 'MESH'. Please select another object (or press 'ALT-C to convert object to mesh).")
                return False

        success = False
        if cm.modelCreated or cm.animated:
            bricks = getBricks()
            obj = bricks[0] if len(bricks) > 0 else None
        else:
            obj = source
        for i in range(20):
            if obj and obj.layers[i] and scn.layers[i]:
                success = True
        if not success:
            self.report({"WARNING"}, "Object is not on active layer(s)")
            return False

        return True

    def transformBricks(self, bGroup, cm, parent, source, sourceDup_details, action):
        # if using local orientation and creating model for first time
        if cm.useLocalOrient and action == "CREATE":
            obj = parent if cm.splitModel else bGroup.objects[0]
            source_details = bounds(source)
            lastMode = source.rotation_mode
            obj.rotation_mode = "XYZ"
            source.rotation_mode = obj.rotation_mode
            obj.rotation_euler = source.rotation_euler
            obj.rotation_mode = lastMode
            source["local_orient_offset"] = source_details.mid - sourceDup_details.mid
            obj.location += Vector(source["local_orient_offset"])
        # if model was split but isn't now
        if cm.lastSplitModel and not cm.splitModel:
            # transfer transformation of parent to object
            parent.rotation_mode = "XYZ"
            for obj in bGroup.objects:
                obj.location = parent.location
                obj.rotation_mode = parent.rotation_mode
                obj.rotation_euler.rotate(parent.rotation_euler)
                obj.scale = parent.scale
            # reset parent transformation
            parent.location = (0, 0, 0)
            parent.rotation_euler = Euler((0, 0, 0))
            cm.transformScale = 1
            parent.scale = (1, 1, 1)
        # if model is not split
        elif not cm.splitModel:
            # apply stored transformation to bricks
            applyTransformData(cm, list(bGroup.objects))
        # if model wasn't split but is now
        elif not cm.lastSplitModel:
            # apply stored transformation to parent of bricks
            applyTransformData(cm, parent)
        obj = bGroup.objects[0] if len(bGroup.objects) > 0 else None
        if obj is None:
            return
        # select the bricks object unless it's massive
        if not cm.splitModel and len(obj.data.vertices) < 500000:
            select(obj, active=obj)
        # if model contains armature, lock the location, rotation, and scale of created bricks object
        if not cm.splitModel and cm.armature:
            obj.lock_location = [True, True, True]
            obj.lock_rotation = [True, True, True]
            obj.lock_scale    = [True, True, True]

    @classmethod
    def getLogo(self, scn, cm, dimensions):
        if cm.brickType == "CUSTOM":
            refLogo = None
            logo_details = None
        else:
            if cm.logoDetail == "LEGO":
                refLogo = getLegoLogo(self, scn, cm, dimensions)
            else:
                refLogo = bpy.data.objects.get(cm.logoObjectName)
            # apply transformation to duplicate of logo object and normalize size/position
            logo_details, refLogo = prepareLogoAndGetDetails(scn, cm, refLogo, dimensions)
        return logo_details, refLogo

    def getDuplicateObjects(self, scn, cm, source_name, startFrame, stopFrame):
        """ returns list of duplicates from self.source with all traits applied """
        activeFrame = scn.frame_current
        soft_body = False
        smoke = False

        # set cm.armature and cm.physics
        for mod in self.source.modifiers:
            if mod.type == "ARMATURE":
                cm.armature = True
            elif mod.type in ["CLOTH", "SOFT_BODY"]:
                soft_body = True
            elif mod.type == "SMOKE":
                smoke = True
        # if self.source.rigid_body is not None:
        #     cm.rigid_body = True
        #     storeRigidBodySettings(self.source)

        if soft_body or smoke:
            # TODO: Figure out how to cut down on the amount of frames covered here. e.g. start at last baked frame or something
            for curFrame in range(0, startFrame):
                # set active frame for applying modifiers
                scn.frame_set(curFrame)

        denom = stopFrame - startFrame
        update_progress("Applying Modifiers", 0)

        duplicates = {}
        for curFrame in range(startFrame, stopFrame + 1):
            # retrieve previously duplicated source if possible
            if self.action == "UPDATE_ANIM":
                sourceDup = bpy.data.objects.get("Bricker_" + source_name + "_f_" + str(curFrame))
                if sourceDup is not None:
                    duplicates[curFrame] = {"obj":sourceDup, "isReused":True}
                    continue
            # set active frame for applying modifiers
            scn.frame_set(curFrame)
            # duplicate source for current frame
            sourceDup = duplicateObj(self.source, link=True)
            sourceDup.name = "Bricker_" + cm.source_name + "_f_" + str(curFrame)
            select(sourceDup, active=True, only=True)
            # # apply rigid body transform data
            # if cm.rigid_body:
            #     bpy.ops.object.visual_transform_apply()
            #     bpy.ops.rigidbody.object_remove()
            #     scn.update()
            # remove modifiers and constraints
            for mod in sourceDup.modifiers:
                sourceDup.modifiers.remove(mod)
            for constraint in sourceDup.constraints:
                sourceDup.constraints.remove(constraint)
            # apply parent transformation
            if sourceDup.parent:
                bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
            # apply animated transform data
            sourceDup.matrix_world = self.source.matrix_world
            sourceDup.animation_data_clear()
            # send to new mesh
            # NOTE: should I use 'PREVIEW' or 'RENDER' here? https://docs.blender.org/api/blender_python_api_2_78_release/bpy.types.Object.html#bpy.types.Object.to_mesh
            sourceDup.data = self.source.to_mesh(scn, True, 'PREVIEW')
            # apply transform data
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            scn.update()
            duplicates[curFrame] = {"obj":sourceDup, "isReused":False}
            # unlink source duplicate
            safeUnlink(sourceDup)
            # update progress bar
            percent = (curFrame - startFrame) / (denom + 1)
            if percent < 1:
                update_progress("Applying Modifiers", percent)
        # update progress bar
        update_progress("Applying Modifiers", 1)
        return duplicates

    def getObjectToBrickify(self, cm):
        objToBrickify = bpy.data.objects.get(cm.source_name) or bpy.context.active_object
        return objToBrickify

    def getNewParent(self, Bricker_parent_on, loc):
        m = bpy.data.meshes.new(Bricker_parent_on + "_mesh")
        parent = bpy.data.objects.new(Bricker_parent_on, m)
        parent.location = loc
        safeScn = getSafeScn()
        safeScn.objects.link(parent)
        return parent

    def setAction(self, cm):
        """ sets self.action """
        if cm.modelCreated:
            self.action = "UPDATE_MODEL"
        elif cm.animated:
            self.action = "UPDATE_ANIM"
        elif not cm.useAnimation:
            self.action = "CREATE"
        else:
            self.action = "ANIMATE"

    #############################################
