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
import math
import json

# Blender imports
import bpy
from mathutils import Matrix, Vector, Euler
props = bpy.props

# Bricker imports
from .customize.undo_stack import *
from .materials import BrickerApplyMaterial
from .delete import BrickerDelete
from .bevel import BrickerBevel
from .cache import *
from ..lib.bricksDict import *
from ..ui.cmlist_utils import dirtyMatrix
from ..functions import *


def updateCanRun(type):
    scn, cm, n = getActiveContextInfo()
    if scn.name == "Bricker_storage (DO NOT RENAME)":
        return True
    elif scn.cmlist_index == -1:
        return False
    else:
        if type == "ANIMATION":
            return (cm.logoDetail != "NONE" and cm.logoDetail != "LEGO") or cm.brickType == "CUSTOM" or cm.modelIsDirty or cm.matrixIsDirty or cm.internalIsDirty or cm.buildIsDirty or cm.bricksAreDirty or (cm.materialType != "CUSTOM" and (cm.materialIsDirty or cm.brickMaterialsAreDirty))
        elif type == "MODEL":
            # set up variables
            Bricker_bricks_gn = "Bricker_%(n)s_bricks" % locals()
            return (cm.logoDetail != "NONE" and cm.logoDetail != "LEGO") or cm.brickType == "CUSTOM" or cm.modelIsDirty or cm.matrixIsDirty or cm.internalIsDirty or cm.buildIsDirty or cm.bricksAreDirty or (cm.materialType != "CUSTOM" and not (cm.materialType == "RANDOM" and not (cm.splitModel or cm.lastMaterialType != cm.materialType)) and (cm.materialIsDirty or cm.brickMaterialsAreDirty)) or (groupExists(Bricker_bricks_gn) and len(bpy.data.groups[Bricker_bricks_gn].objects) == 0)


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
        try:
            scn, cm, _ = getActiveContextInfo()
            previously_animated = cm.animated
            previously_model_created = cm.modelCreated
            self.runBrickify(context)
        except KeyboardInterrupt:
            if self.action in ["CREATE", "ANIMATE"]:
                for n in self.createdObjects:
                    obj = bpy.data.objects.get(n)
                    if obj:
                        bpy.data.objects.remove(obj)
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
        self.source = self.getObjectToBrickify()

    #############################################
    # class methods

    @timed_call('Total Time Elapsed')
    def runBrickify(self, context):
        # set up variables
        scn, cm, n = getActiveContextInfo()
        scn.Bricker_runningOperation = True
        self.undo_stack.iterateStates(cm)
        Bricker_bricks_gn = "Bricker_%(n)s_bricks" % locals()

        # get source and initialize values
        source = self.getObjectToBrickify()
        source["old_parent"] = ""
        source.cmlist_id = cm.id

        # make sure matrix really is dirty
        if cm.matrixIsDirty:
            _, loadedFromCache = getBricksDict(dType="MODEL", cm=cm, restrictContext=True)
            if not matrixReallyIsDirty(cm) and loadedFromCache:
                cm.matrixIsDirty = False

        if not self.isValid(source, Bricker_bricks_gn):
            return {"CANCELLED"}

        if "ANIM" not in self.action:
            self.brickifyModel()
        else:
            self.brickifyAnimation()
            cm.animIsDirty = False

        if self.action in ["CREATE", "ANIMATE"]:
            source.name = cm.source_name + " (DO NOT RENAME)"

        # set cmlist_id for all created objects
        for obj_name in self.createdObjects:
            obj = bpy.data.objects.get(obj_name)
            if obj:
                obj.cmlist_id = cm.id

        # # set final variables
        cm.lastLogoResolution = cm.logoResolution
        cm.lastLogoDetail = cm.logoDetail
        cm.lastSplitModel = cm.splitModel
        cm.lastBrickType = cm.brickType
        cm.lastMaterialType = cm.materialType
        cm.lastShellThickness = cm.shellThickness
        cm.lastMatrixSettings = getMatrixSettings()
        cm.materialIsDirty = False
        cm.brickMaterialsAreDirty = False
        cm.modelIsDirty = False
        cm.buildIsDirty = False
        cm.bricksAreDirty = False
        cm.matrixIsDirty = False
        cm.internalIsDirty = False
        cm.modelCreated = "ANIM" not in self.action
        cm.animated = "ANIM" in self.action
        scn.Bricker_runningOperation = False
        cm.version = bpy.props.bricker_version

        # unlink source from scene and link to safe scene
        if source.name in scn.objects.keys():
            safeUnlink(source, hide=False)

        disableRelationshipLines()

    def brickifyModel(self):
        """ create brick model """
        # set up variables
        scn, cm, n = getActiveContextInfo()
        origFrame = None
        source = None
        Bricker_parent_on = "Bricker_%(n)s_parent" % locals()

        # get or create parent group
        pGroup = bpy.data.groups.get(Bricker_parent_on)
        if pGroup is None:
            pGroup = bpy.data.groups.new(Bricker_parent_on)
            self.createdGroups.append(pGroup.name)

        if self.action == "CREATE":
            # set modelCreatedOnFrame
            cm.modelCreatedOnFrame = scn.frame_current
        else:
            origFrame = scn.frame_current
            scn.frame_set(cm.modelCreatedOnFrame)

        # if there are no changes to apply, simply return "FINISHED"
        if self.action in ["UPDATE_MODEL"] and not updateCanRun("MODEL"):
            return{"FINISHED"}

        sto_scn = bpy.data.scenes.get("Bricker_storage (DO NOT RENAME)")
        if sto_scn:
            sto_scn.update()

        if matrixReallyIsDirty(cm) and cm.customized:
            cm.customized = False

        # delete old bricks if present
        if self.action in ["UPDATE_MODEL"]:
            # skip source, dupes, and parents
            BrickerDelete.cleanUp("MODEL", skipDupes=True, skipParents=True, skipSource=True)
        else:
            storeTransformData(None)

        if self.action == "CREATE":
            # create dupes group
            Bricker_source_dupes_gn = "Bricker_%(n)s_dupes" % locals()
            dGroup = bpy.data.groups.new(Bricker_source_dupes_gn)
            self.createdGroups.append(dGroup.name)
            # duplicate source and add duplicate to group
            select(self.source, active=self.source)
            bpy.ops.object.duplicate()
            sourceDup = scn.objects.active
            dGroup.objects.link(sourceDup)
            select(sourceDup, active=sourceDup)
            sourceDup.name = self.source.name + "_duplicate"
            if cm.useLocalOrient:
                sourceDup.rotation_mode = "XYZ"
                sourceDup.rotation_euler = Euler((0, 0, 0), "XYZ")
            self.createdObjects.append(sourceDup.name)
            # set up sourceDup["old_parent"] and remove sourceDup parent
            sourceDup["frame_parent_cleared"] = -1
            select(sourceDup, active=sourceDup)
            if sourceDup.parent:
                sourceDup["old_parent"] = sourceDup.parent.name
                sourceDup["frame_parent_cleared"] = scn.frame_current
                bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
            # apply shape keys if existing
            shapeKeys = sourceDup.data.shape_keys
            if shapeKeys and len(shapeKeys.key_blocks) > 0:
                select(sourceDup, active=sourceDup)
                bpy.ops.object.shape_key_add(from_mix=True)
                for i in range(len(shapeKeys.key_blocks)):
                    sourceDup.shape_key_remove(sourceDup.data.shape_keys.key_blocks[0])
                # bpy.ops.object.shape_key_remove(all=True)
            # apply modifiers for source duplicate
            cm.armature = applyModifiers(sourceDup)
            # apply transformation data
            if self.action == "CREATE":
                self.source["previous_location"] = self.source.location.to_tuple()
            self.source.rotation_mode = "XYZ"
            self.source["previous_rotation"] = tuple(self.source.rotation_euler)
            self.source["previous_scale"] = self.source.scale.to_tuple()
            select(sourceDup, active=sourceDup)
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
            parent = self.getParent(Bricker_parent_on, parentLoc)
            cm.parent_name = parent.name
            pGroup.objects.link(parent)
        parent["loc_diff"] = self.source.location - parentLoc
        self.createdObjects.append(parent.name)

        # update refLogo
        logo_details, refLogo = self.getLogo(cm, dimensions)

        # create new bricks
        group_name = self.createNewBricks(sourceDup, parent, sourceDup_details, dimensions, refLogo, logo_details, self.action, curFrame=None, sceneCurFrame=None)

        bGroup = bpy.data.groups.get(group_name)
        if bGroup:
            self.createdGroups.append(group_name)
            # transform bricks to appropriate location
            self.transformBricks(bGroup, cm, parent, self.source, sourceDup_details, self.action)
            # match brick layers to source layers
            for obj in bGroup.objects:
                obj.layers = self.source.layers

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

        cm.lastSourceMid = listToStr(parentLoc)

    def brickifyAnimation(self):
        """ create brick animation """
        # set up variables
        scn, cm, n = getActiveContextInfo()
        Bricker_parent_on = "Bricker_%(n)s_parent" % locals()
        Bricker_source_dupes_gn = "Bricker_%(n)s_dupes" % locals()
        sceneCurFrame = scn.frame_current
        objsToSelect = []

        if self.action == "UPDATE_ANIM":
            safeLink(self.source)

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
        if self.action == "UPDATE_ANIM":
            preservedFrames = None
            if self.updatedFramesOnly:
                # preserve duplicates, parents, and bricks for frames that haven't changed
                preservedFrames = [cm.startFrame, cm.stopFrame]
            BrickerDelete.cleanUp("ANIMATION", skipDupes=not self.updatedFramesOnly, skipParents=not self.updatedFramesOnly, preservedFrames=preservedFrames)
            self.source.name = self.source.name + " (DO NOT RENAME)"

        # get or create duplicate and parent groups
        dGroup = bpy.data.groups.get(Bricker_source_dupes_gn)
        if dGroup is None:
            dGroup = bpy.data.groups.new(Bricker_source_dupes_gn)
            self.createdGroups.append(dGroup.name)
        pGroup = bpy.data.groups.get(Bricker_parent_on)
        if pGroup is None:
            pGroup = bpy.data.groups.new(Bricker_parent_on)
            self.createdGroups.append(pGroup.name)

        # get parent object
        parent0 = bpy.data.objects.get(Bricker_parent_on)
        if parent0 is None:
            parent0 = self.getParent(Bricker_parent_on, self.source.location.to_tuple())
            pGroup.objects.link(parent0)
            cm.parent_name = parent0.name
        self.createdObjects.append(parent0.name)

        # begin drawing status to cursor
        wm = bpy.context.window_manager
        wm.progress_begin(0, cm.stopFrame + 1 - cm.startFrame)

        # prepare duplicate objects for animation
        duplicates = self.getDuplicateObjects(dGroup, cm.source_name, cm.startFrame, cm.stopFrame)

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
            logo_details, refLogo = self.getLogo(cm, dimensions)

            if self.action == "ANIMATE":
                # set source model height for display in UI
                cm.modelHeight = source_details.dist.z

            # set up parent for this layer
            # TODO: Remove these from memory in the delete function, or don't use them at all
            pGroup = bpy.data.groups[Bricker_parent_on]  # redefine pGroup since it was removed
            parent = bpy.data.objects.get(Bricker_parent_on + "_frame_" + str(curFrame))
            if parent is None:
                m = bpy.data.meshes.new(Bricker_parent_on + "_frame_" + str(curFrame) + "_mesh")
                parent = bpy.data.objects.new(Bricker_parent_on + "_frame_" + str(curFrame), m)
                parent.location = source_details.mid - parent0.location
                parent.parent = parent0
                pGroup.objects.link(parent)
                scn.objects.link(parent)
                scn.update()
                safeUnlink(parent)
                self.createdObjects.append(parent.name)

            # create new bricks
            try:
                group_name = self.createNewBricks(source, parent, source_details, dimensions, refLogo, logo_details, self.action, curFrame=curFrame, sceneCurFrame=sceneCurFrame)
                self.createdGroups.append(group_name)
            except KeyboardInterrupt:
                self.report({"WARNING"}, "Process forcably interrupted with 'KeyboardInterrupt'")
                if curFrame != cm.startFrame:
                    wm.progress_end()
                    cm.lastStartFrame = cm.startFrame
                    cm.lastStopFrame = curFrame
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
    def createNewBricks(self, source, parent, source_details, dimensions, refLogo, logo_details, action, cm=None, curFrame=None, sceneCurFrame=None, bricksDict=None, keys="ALL", replaceExistingGroup=True, selectCreated=False, printStatus=True, redraw=False):
        """ gets/creates bricksDict, runs makeBricks, and caches the final bricksDict """
        scn = bpy.context.scene
        cm = cm or scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        _, _, _, brickScale, customData, customObj_details = getArgumentsForBricksDict(cm, source=source, source_details=source_details, dimensions=dimensions)
        updateCursor = action in ["CREATE", "UPDATE_MODEL"]  # evaluates to boolean value
        if bricksDict is None:
            # multiply brickScale by offset distance
            brickScale2 = brickScale if cm.brickType != "CUSTOM" else vec_mult(brickScale, Vector((cm.distOffsetX, cm.distOffsetY, cm.distOffsetZ)))
            # get bricks dictionary
            bricksDict, loadedFromCache = getBricksDict(dType=action, source=source, source_details=source_details, dimensions=dimensions, brickScale=brickScale2, updateCursor=updateCursor, curFrame=curFrame)
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
        bricksDict = updateMaterials(bricksDict, source)
        # make bricks
        group_name = 'Bricker_%(n)s_bricks_frame_%(curFrame)s' % locals() if curFrame is not None else "Bricker_%(n)s_bricks" % locals()
        bricksCreated, bricksDict = makeBricks(source, parent, refLogo, logo_details, dimensions, bricksDict, cm=cm, split=cm.splitModel, brickScale=brickScale, customData=customData, customObj_details=customObj_details, group_name=group_name, replaceExistingGroup=replaceExistingGroup, frameNum=curFrame, cursorStatus=updateCursor, keys=keys, printStatus=printStatus)
        if selectCreated:
            deselectAll()
            for brick in bricksCreated:
                select(brick, active=brick, only=False)
        # store current bricksDict to cache
        cacheBricksDict(action, cm, bricksDict, curFrame=curFrame)
        return group_name

    def isValid(self, source, Bricker_bricks_gn):
        """ returns True if brickify action can run, else report WARNING/ERROR and return False """
        scn, cm, _ = getActiveContextInfo()
        if cm.brickType == "CUSTOM":
            if cm.customObjectName == "":
                self.report({"WARNING"}, "Custom brick type object not specified.")
                return False
            customObj = bpy.data.objects.get(cm.customObjectName)
            if customObj is None:
                n = cm.customObjectName
                self.report({"WARNING"}, "Custom brick type object '%(n)s' could not be found" % locals())
                return False
            if cm.customObjectName == cm.source_name and (not (cm.animated or cm.modelCreated) or customObj.protected):
                self.report({"WARNING"}, "Source object cannot be its own brick type.")
                return False
            if customObj.type != "MESH":
                self.report({"WARNING"}, "Custom brick type object is not of type 'MESH'. Please select another object (or press 'ALT-C to convert object to mesh).")
                return False
            custom_details = bounds(customObj)
            zeroDistAxes = ""
            if custom_details.dist.x < 0.00001:
                zeroDistAxes += "X"
            if custom_details.dist.y < 0.00001:
                zeroDistAxes += "Y"
            if custom_details.dist.z < 0.00001:
                zeroDistAxes += "Z"
            if zeroDistAxes != "":
                axisStr = "axis" if len(zeroDistAxes) == 1 else "axes"
                warningMsg = "Custom brick type object is to small along the '%(zeroDistAxes)s' %(axisStr)s (<0.00001). Please select another object or extrude it along the '%(zeroDistAxes)s' %(axisStr)s." % locals()
                self.report({"WARNING"}, warningMsg)
                return False
        if cm.materialType == "CUSTOM" and cm.materialName != "" and bpy.data.materials.find(cm.materialName) == -1:
            n = cm.materialName
            self.report({"WARNING"}, "Custom material '%(n)s' could not be found" % locals())
            return False

        self.clothMod = False
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
                self.report({"WARNING"}, "Bricker: Rigid body physics not supported")
                return False
            # verify all appropriate modifiers have been applied
            ignoredMods = []
            for mod in source.modifiers:
                # abort render if these modifiers are enabled but not applied
                # if mod.type in ["ARRAY", "BEVEL", "BOOLEAN", "SKIN", "OCEAN"] and mod.show_viewport:
                #     self.report({"WARNING"}, "Please apply '" + str(mod.type) + "' modifier(s) or disable from view before Brickifying the object.")
                #     return False
                # ignore these modifiers (disable from view until Brickified model deleted)
                if mod.type in ["BUILD"] and mod.show_viewport:
                    mod.show_viewport = False
                    ignoredMods.append(mod.name)
                # these modifiers are unsupported - abort render if enabled
                if mod.type in ["SMOKE"] and mod.show_viewport:
                    self.report({"WARNING"}, "'" + str(mod.type) + "' modifier not supported by the Bricker.")
                    return False
                # handle cloth modifier
                if mod.type == "CLOTH" and mod.show_viewport:
                    self.clothMod = mod
            if len(ignoredMods) > 0:
                # store disabled mods to source so they can be enabled in delete operation
                source["ignored_mods"] = ignoredMods
                # warn user that modifiers were ignored
                warningMsg = "The following modifiers were ignored (apply to respect changes): "
                for i in ignoredMods:
                    warningMsg += "'%(i)s', " % locals()
                self.report({"WARNING"}, warningMsg[:-2])

        if self.action == "CREATE":
            # if source is soft body or cloth and is enabled, prompt user to apply the modifiers
            for mod in source.modifiers:
                if mod.type in ["SOFT_BODY", "CLOTH"] and mod.show_viewport:
                    self.report({"WARNING"}, "Please apply '" + str(mod.type) + "' modifier or disable from view before Brickifying the object.")
                    return False

        if self.action in ["ANIMATE", "UPDATE_ANIM"]:
            # if source is soft body or cloth and is enabled and file not saved, prompt user to save the file
            for mod in source.modifiers:
                if mod.type in ["SOFT_BODY", "CLOTH"] and mod.show_viewport and not bpy.data.is_saved:
                    self.report({"WARNING"}, "Blend file must be saved before brickifying '" + str(mod.type) + "' modifiers.")
                    return False
            # verify start frame is less than stop frame
            if cm.startFrame > cm.stopFrame:
                self.report({"ERROR"}, "Start frame must be less than or equal to stop frame (see animation tab below).")
                return False
            # TODO: Alert user to bake fluid/cloth simulation before attempting to Brickify

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
            obj.rotation_mode = "XYZ"
            obj.rotation_euler = source.rotation_euler
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
            parent.rotation_euler = Euler((0, 0, 0), "XYZ")
            cm.transformScale = 1
            parent.scale = (1, 1, 1)
        # if model is not split
        elif not cm.splitModel:
            # apply stored transformation to bricks
            applyTransformData(list(bGroup.objects))
        # if model wasn't split but is now
        elif not cm.lastSplitModel:
            # apply stored transformation to parent of bricks
            applyTransformData(parent)
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
    def getLogo(self, cm, dimensions):
        if cm.brickType == "CUSTOM":
            refLogo = None
            logo_details = None
        else:
            if cm.logoDetail == "LEGO":
                refLogo = self.getLegoLogo(self, dimensions)
                logo_details = bounds(refLogo)
            else:
                refLogo = bpy.data.objects.get(cm.logoObjectName)
                # apply transformation to duplicate of logo object and normalize size/position
                logo_details, refLogo = prepareLogoAndGetDetails(refLogo, dimensions)
        return logo_details, refLogo

    def getLegoLogo(self, dimensions):
        scn, cm, _ = getActiveContextInfo()
        # update refLogo
        if cm.logoDetail == "NONE":
            refLogo = None
        else:
            decimate = False
            r = cm.logoResolution
            refLogoImport = bpy.data.objects.get("Bricker_refLogo")
            if refLogoImport is not None:
                refLogo = bpy.data.objects.get("Bricker_refLogo_%(r)s" % locals())
                if refLogo is None:
                    refLogo = bpy.data.objects.new("Bricker_refLogo_%(r)s" % locals(), refLogoImport.data.copy())
                    # queue for decimation
                    decimate = True
            else:
                # import refLogo and add to group
                refLogoImport = importLogo()
                refLogoImport.name = "Bricker_refLogo"
                safeUnlink(refLogoImport)
                refLogo = bpy.data.objects.new("Bricker_refLogo_%(r)s" % locals(), refLogoImport.data.copy())
                m = refLogo.data
                # smooth faces
                smoothMeshFaces(list(m.polygons))
                # get transformation matrix
                r_mat = Matrix.Rotation(math.radians(90.0), 4, 'X')
                # transform logo into place
                m.transform(r_mat)
                # queue for decimation
                decimate = True
            # decimate refLogo
            # TODO: Speed this up, if possible
            if refLogo is not None and decimate and cm.logoResolution < 1:
                dMod = refLogo.modifiers.new('Decimate', type='DECIMATE')
                dMod.ratio = cm.logoResolution * 1.6
                scn.objects.link(refLogo)
                select(refLogo, active=refLogo)
                bpy.ops.object.modifier_apply(apply_as='DATA', modifier='Decimate')
                safeUnlink(refLogo)

        return refLogo

    def getDuplicateObjects(self, dGroup, source_name, startFrame, stopFrame):
        """ returns list of duplicates from self.source with all traits applied """
        scn, cm, _ = getActiveContextInfo()
        activeFrame = scn.frame_current

        duplicates = {}

        lastObj = self.source
        for curFrame in range(startFrame, stopFrame + 1):
            sourceDup = None
            if self.action == "UPDATE_ANIM":
                # retrieve previously duplicated source
                sourceDup = bpy.data.objects.get("Bricker_" + source_name + "_frame_" + str(curFrame))
            if sourceDup:
                duplicates[curFrame] = {"obj":sourceDup, "isReused":True}
                continue
            # duplicate source for current frame
            select(lastObj, active=lastObj)
            bpy.ops.object.duplicate()
            sourceDup = scn.objects.active
            sourceDup.name = "Bricker_" + cm.source_name + "_frame_" + str(curFrame)
            if sourceDup.name not in dGroup.objects.keys():
                dGroup.objects.link(sourceDup)
            duplicates[curFrame] = {"obj":sourceDup, "isReused":False}
            lastObj = sourceDup

        denom = stopFrame - startFrame
        if denom != 0:
            update_progress("Applying Modifiers", 0)

        for curFrame in range(startFrame, stopFrame + 1):
            if duplicates[curFrame]["isReused"]:
                continue
            sourceDup = duplicates[curFrame]["obj"]
            self.createdObjects.append(sourceDup.name)
            if sourceDup.parent:
                # apply parent transformation
                select(sourceDup, active=sourceDup)
                bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
            # apply shape keys if existing
            shapeKeys = sourceDup.data.shape_keys
            if shapeKeys is not None and len(shapeKeys.key_blocks) > 0:
                select(sourceDup, active=sourceDup)
                bpy.ops.object.shape_key_add(from_mix=True)
                for i in range(len(shapeKeys.key_blocks)):
                    sourceDup.shape_key_remove(sourceDup.data.shape_keys.key_blocks[0])
                # bpy.ops.object.shape_key_remove(all=True)

        # store lastObj transform data to source
        if lastObj != self.source:
            self.source["previous_location"] = lastObj.location.to_tuple()
            lastObj.rotation_mode = "XYZ"
            self.source["previous_rotation"] = tuple(lastObj.rotation_euler)
            self.source["previous_scale"] = lastObj.scale.to_tuple()

            # bake & apply cloth and soft body modifiers
            for mod in lastObj.modifiers:
                if mod.type in ["CLOTH", "SOFT_BODY"] and mod.show_viewport:
                    if not mod.point_cache.use_disk_cache:
                        mod.point_cache.use_disk_cache = True
                        mod.point_cache.use_library_path = True
                    if mod.point_cache.frame_end >= stopFrame:
                        mod.point_cache.frame_end = stopFrame
                        override = {'scene': scn, 'active_object': lastObj, 'point_cache': mod.point_cache}
                        bpy.ops.ptcache.bake(override, bake=True)

        for curFrame in range(startFrame, stopFrame + 1):
            # print status
            if denom != 0:
                percent = (curFrame - startFrame) / (denom + 1)
                if percent < 1:
                    update_progress("Applying Modifiers", percent)
            if duplicates[curFrame]["isReused"]:
                continue
            sourceDup = duplicates[curFrame]["obj"]
            # set active frame for applying modifiers
            scn.frame_set(curFrame)
            # apply animated transform data
            sourceDup.matrix_world = self.source.matrix_world
            sourceDup.animation_data_clear()
            # apply sourceDup modifiers
            cm.armature = applyModifiers(sourceDup)
            scn.update()
            # set source previous transforms
            self.source["previous_location"] = sourceDup.location.to_tuple()
            sourceDup.rotation_mode = "XYZ"
            self.source["previous_rotation"] = tuple(sourceDup.rotation_euler)
            self.source["previous_scale"] = sourceDup.scale.to_tuple()
            # apply transform data
            select(sourceDup, active=sourceDup)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            scn.update()
            # unlink source duplicate
            safeUnlink(sourceDup)
        if denom != 0:
            update_progress("Applying Modifiers", 1)
        return duplicates

    def getObjectToBrickify(self):
        scn, cm, _ = getActiveContextInfo()
        if self.action in ["UPDATE_MODEL", "UPDATE_ANIM"]:
            objToBrickify = bpy.data.objects.get(cm.source_name + " (DO NOT RENAME)")
        elif self.action in ["CREATE", "ANIMATE"]:
            objToBrickify = bpy.data.objects.get(cm.source_name) or bpy.context.active_object
        else:
            objToBrickify = bpy.data.objects.get(cm.source_name)
        return objToBrickify

    def getParent(self, Bricker_parent_on, loc):
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
