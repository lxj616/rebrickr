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

# Rebrickr imports
from .customize.undo_stack import *
from .materials import RebrickrApplyMaterial
from .delete import RebrickrDelete
from .bevel import RebrickrBevel
from .cache import *
from ..lib.bricksDict import *
from ..ui.cmlist import dirtyMatrix
from ..functions import *


def updateCanRun(type):
    scn = bpy.context.scene
    if scn.name == "Rebrickr_storage (DO NOT RENAME)":
        return True
    elif scn.cmlist_index == -1:
        return False
    else:
        cm = scn.cmlist[scn.cmlist_index]
        if type == "ANIMATION":
            return (cm.logoDetail != "None" and cm.logoDetail != "LEGO Logo") or cm.brickType == "Custom" or cm.modelIsDirty or cm.matrixIsDirty or cm.internalIsDirty or cm.buildIsDirty or cm.bricksAreDirty or (cm.materialType != "Custom" and (cm.materialIsDirty or cm.brickMaterialsAreDirty))
        elif type == "MODEL":
            # set up variables
            n = cm.source_name
            Rebrickr_bricks_gn = "Rebrickr_%(n)s_bricks" % locals()
            return (cm.logoDetail != "None" and cm.logoDetail != "LEGO Logo") or cm.brickType == "Custom" or cm.modelIsDirty or cm.matrixIsDirty or cm.internalIsDirty or cm.buildIsDirty or cm.bricksAreDirty or (cm.materialType != "Custom" and not (cm.materialType == "Random" and not (cm.splitModel or cm.lastMaterialType != cm.materialType)) and (cm.materialIsDirty or cm.brickMaterialsAreDirty)) or (groupExists(Rebrickr_bricks_gn) and len(bpy.data.groups[Rebrickr_bricks_gn].objects) == 0)

def importLogo():
    """ import logo object from Rebrickr addon folder """
    addonsPath = bpy.utils.user_resource('SCRIPTS', "addons")
    Rebrickr = bpy.props.rebrickr_module_name
    logoObjPath = "%(addonsPath)s/%(Rebrickr)s/lego_logo.obj" % locals()
    bpy.ops.import_scene.obj(filepath=logoObjPath)
    logoObj = bpy.context.selected_objects[0]
    return logoObj

class RebrickrBrickify(bpy.types.Operator):
    """ Create brick sculpture from source object mesh """                       # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "rebrickr.brickify"                                        # unique identifier for buttons and menu items to reference.
    bl_label = "Create/Update Brick Model from Source Object"                 # display name in the interface.
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
            scn = bpy.context.scene
            cm = scn.cmlist[scn.cmlist_index]
            previously_animated = cm.animated
            previously_model_created = cm.modelCreated
            self.runBrickify(context)
        except KeyboardInterrupt:
            if self.action in ["CREATE", "ANIMATE"]:
                for n in self.createdObjects:
                    obj = bpy.data.objects.get(n)
                    if obj is not None:
                        bpy.data.objects.remove(obj)
                for n in self.createdGroups:
                    group = bpy.data.groups.get(n)
                    if group is not None:
                        bpy.data.groups.remove(group)
                if self.source is not None:
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
        self.undo_stack = UndoStack.get_instance()
        self.undo_stack.undo_push('brickify')
        self.createdObjects = []
        self.createdGroups = []
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        self.action = getAction(cm)
        self.source = self.getObjectToBrickify()

    #############################################
    # class methods

    @timed_call('Total Time Elapsed')
    def runBrickify(self, context):
        # set up variables
        scn = context.scene
        scn.Rebrickr_runningOperation = True
        cm = scn.cmlist[scn.cmlist_index]
        cm.version = bpy.props.rebrickr_version
        self.undo_stack.iterateStates(cm)
        n = cm.source_name
        Rebrickr_bricks_gn = "Rebrickr_%(n)s_bricks" % locals()

        # get source and initialize values
        source = self.getObjectToBrickify()
        source["old_parent"] = ""
        source.cmlist_id = cm.id

        # check if matrix is dirty
        if cm.matrixIsDirty:
            if not matrixReallyIsDirty(cm) and getBricksDict("UPDATE_MODEL", cm=cm, restrictContext=True)[1]:
                cm.matrixIsDirty = False

        if not self.isValid(source, Rebrickr_bricks_gn):
            return {"CANCELLED"}

        if self.action not in ["ANIMATE", "UPDATE_ANIM"]:
            self.brickifyModel()
        else:
            self.brickifyAnimation()
            cm.animIsDirty = False

        if self.action in ["CREATE", "ANIMATE"]:
            source.name = cm.source_name + " (DO NOT RENAME)"

        # set cmlist_id for all created objects
        for obj_name in self.createdObjects:
            obj = bpy.data.objects.get(obj_name)
            if obj is not None: obj.cmlist_id = cm.id

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
        scn.Rebrickr_runningOperation = False

        # apply random materials
        if cm.materialType == "Random":
            bricks = getBricks()
            RebrickrApplyMaterial.applyRandomMaterial(context, bricks)

        # unlink source from scene and link to safe scene
        if source.name in scn.objects.keys():
            safeUnlink(source, hide=False)

        disableRelationshipLines()

    def brickifyModel(self):
        """ create brick model """
        # set up variables
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        origFrame = None
        source = None
        n = cm.source_name
        Rebrickr_bricks_gn = "Rebrickr_%(n)s_bricks" % locals()
        Rebrickr_parent_on = "Rebrickr_%(n)s_parent" % locals()

        # get or create parent group
        pGroup = bpy.data.groups.get(Rebrickr_parent_on)
        if pGroup is None:
            pGroup = bpy.data.groups.new(Rebrickr_parent_on)
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

        sto_scn = bpy.data.scenes.get("Rebrickr_storage (DO NOT RENAME)")
        if sto_scn is not None:
            sto_scn.update()

        # delete old bricks if present
        if self.action in ["UPDATE_MODEL"]:
            # skip source, dupes, and parents
            RebrickrDelete.cleanUp("MODEL", skipDupes=True, skipParents=True, skipSource=True)
        else:
            storeTransformData(None)

        if self.action == "CREATE":
            # create dupes group
            Rebrickr_source_dupes_gn = "Rebrickr_%(n)s_dupes" % locals()
            dGroup = bpy.data.groups.new(Rebrickr_source_dupes_gn)
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
                sourceDup.rotation_euler = Euler((0,0,0), "XYZ")
            self.createdObjects.append(sourceDup.name)
            # set up sourceDup["old_parent"] and remove sourceDup parent
            sourceDup["frame_parent_cleared"] = -1
            select(sourceDup, active=sourceDup)
            if sourceDup.parent is not None:
                sourceDup["old_parent"] = sourceDup.parent.name
                sourceDup["frame_parent_cleared"] = scn.frame_current
                bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
            # apply shape keys if existing
            shapeKeys = sourceDup.data.shape_keys
            if shapeKeys is not None and len(shapeKeys.key_blocks) > 0:
                select(sourceDup, active=sourceDup)
                bpy.ops.object.shape_key_add(from_mix=True)
                for i in range(len(shapeKeys.key_blocks)):
                    sourceDup.shape_key_remove(sourceDup.data.shape_keys.key_blocks[0])
                # bpy.ops.object.shape_key_remove(all=True)
            # apply modifiers for source duplicate
            applyModifiers(sourceDup)
            # set cm.armature
            foundOne = False
            for mod in sourceDup.modifiers:
                if mod.type == "ARMATURE" and mod.show_viewport:
                    cm.armature = True
                    foundOne = True
                    break
            if not foundOne: cm.armature = False
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
        if sourceDup is None:
            sourceDup = self.source

        # link sourceDup if it isn't in scene
        if sourceDup.name not in scn.objects.keys():
            safeLink(sourceDup)
            scn.update()

        # get sourceDup_details and dimensions
        sourceDup_details, dimensions = getDetailsAndBounds(sourceDup)

        if self.action == "CREATE":
            # set sourceDup model height for display in UI
            cm.modelHeight = sourceDup_details.z.dist

        # get parent object
        parent = bpy.data.objects.get(Rebrickr_parent_on)
        # if parent doesn't exist, get parent with new location
        parentLoc = (sourceDup_details.x.mid, sourceDup_details.y.mid, sourceDup_details.z.mid)
        if parent is None:
            parent = self.getParent(Rebrickr_parent_on, parentLoc)
            cm.parent_name = parent.name
            pGroup.objects.link(parent)
        self.createdObjects.append(parent.name)

        # update refLogo
        refLogo = self.getLogo(cm)

        # create new bricks
        self.runCreateNewBricks(sourceDup, parent, sourceDup_details, dimensions, refLogo, self.action)

        bGroup = bpy.data.groups.get(Rebrickr_bricks_gn) # redefine bGroup since it was removed
        if bGroup is not None:
            self.transformBricks(bGroup, cm, parent, self.source, self.action)

        # unlink source duplicate if created
        if sourceDup != self.source and sourceDup.name in scn.objects.keys():
            safeUnlink(sourceDup)

        # add bevel if it was previously added
        if self.action == "UPDATE_MODEL" and cm.bevelAdded:
            bricks = getBricks()
            RebrickrBevel.runBevelAction(bricks, cm)

        cm.modelCreated = True

        cm.lastSourceMid = listToStr(parentLoc)

        if origFrame is not None:
            scn.frame_set(origFrame)

    def brickifyAnimation(self):
        """ create brick animation """
        # set up variables
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        Rebrickr_bricks_gn = "Rebrickr_%(n)s_bricks" % locals()
        Rebrickr_parent_on = "Rebrickr_%(n)s_parent" % locals()
        Rebrickr_source_dupes_gn = "Rebrickr_%(n)s_dupes" % locals()
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
            Caches.clearCaches()

        if cm.splitModel:
            cm.splitModel = False

        # delete old bricks if present
        if self.action == "UPDATE_ANIM":
            preservedFrames = None
            if self.updatedFramesOnly:
                # preserve duplicates, parents, and bricks for frames that haven't changed
                preservedFrames = [cm.startFrame, cm.stopFrame]
            RebrickrDelete.cleanUp("ANIMATION", skipDupes=not self.updatedFramesOnly, skipParents=not self.updatedFramesOnly, preservedFrames=preservedFrames)
            self.source.name = self.source.name + " (DO NOT RENAME)"

        # get or create duplicate and parent groups
        dGroup = bpy.data.groups.get(Rebrickr_source_dupes_gn)
        if dGroup is None:
            dGroup = bpy.data.groups.new(Rebrickr_source_dupes_gn)
            self.createdGroups.append(dGroup.name)
        pGroup = bpy.data.groups.get(Rebrickr_parent_on)
        if pGroup is None:
            pGroup = bpy.data.groups.new(Rebrickr_parent_on)
            self.createdGroups.append(pGroup.name)

        # get parent object
        parent0 = bpy.data.objects.get(Rebrickr_parent_on)
        if parent0 is None:
            parent0 = self.getParent(Rebrickr_parent_on, self.source.location.to_tuple())
            pGroup.objects.link(parent0)
            cm.parent_name = parent0.name
        self.createdObjects.append(parent0.name)

        # update refLogo
        refLogo = self.getLogo(cm)

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

            if self.action == "ANIMATE":
                # set source model height for display in UI
                cm.modelHeight = source_details.z.dist

            # set up parent for this layer
            # TODO: Remove these from memory in the delete function, or don't use them at all
            pGroup = bpy.data.groups[Rebrickr_parent_on] # redefine pGroup since it was removed
            parent = bpy.data.objects.get(Rebrickr_parent_on + "_frame_" + str(curFrame))
            if parent is None:
                m = bpy.data.meshes.new(Rebrickr_parent_on + "_frame_" + str(curFrame) + "_mesh")
                parent = bpy.data.objects.new(Rebrickr_parent_on + "_frame_" + str(curFrame), m)
                parent.location = (source_details.x.mid - parent0.location.x, source_details.y.mid - parent0.location.y, source_details.z.mid - parent0.location.z)
                parent.parent = parent0
                pGroup.objects.link(parent)
                scn.objects.link(parent)
                scn.update()
                safeUnlink(parent)
                self.createdObjects.append(parent.name)

            # create new bricks
            try:
                group_name = self.runCreateNewBricks(source, parent, source_details, dimensions, refLogo, self.action, curFrame=curFrame, sceneCurFrame=sceneCurFrame)
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

            wm.progress_update(curFrame-cm.startFrame)
            print("completed frame " + str(curFrame))

        # prepare bricks to be displayed
        for curFrame in range(cm.startFrame, cm.stopFrame + 1):
            group_name = "Rebrickr_%(n)s_bricks_frame_%(curFrame)s" % locals()
            for obj in bpy.data.groups[group_name].objects:
                if (curFrame == cm.startFrame and sceneCurFrame < cm.startFrame) or curFrame == sceneCurFrame or (curFrame == cm.stopFrame and sceneCurFrame > cm.stopFrame):
                    objsToSelect = bpy.data.groups[group_name].objects
                else:
                    obj.hide = True
                    obj.hide_render = True
                # lock location, rotation, and scale of created bricks
                obj.lock_location = [True, True, True]
                obj.lock_rotation = [True, True, True]
                obj.lock_scale    = [True, True, True]
                # match brick layers to source layers
                obj.layers = self.source.layers

        for obj in objsToSelect:
            obj.hide = False
            obj.hide_render = False
            select(obj, active=obj)

        wm.progress_end()
        cm.lastStartFrame = cm.startFrame
        cm.lastStopFrame = cm.stopFrame
        scn.frame_set(sceneCurFrame)

        cm.animated = True

    def runCreateNewBricks(self, source, parent, source_details, dimensions, refLogo, action, curFrame=None, sceneCurFrame=None):
        group_name = self.createNewBricks(source, parent, source_details, dimensions, refLogo, action, curFrame=curFrame, sceneCurFrame=sceneCurFrame)
        if int(round((source_details.x.dist)/(dimensions["width"]+dimensions["gap"]))) == 0:
            self.report({"WARNING"}, "Model is too small on X axis for an accurate calculation. Try scaling up your model or decreasing the brick size for a more accurate calculation.")
        if int(round((source_details.y.dist)/(dimensions["width"]+dimensions["gap"]))) == 0:
            self.report({"WARNING"}, "Model is too small on Y axis for an accurate calculation. Try scaling up your model or decreasing the brick size for a more accurate calculation.")
        if int(round((source_details.z.dist)/(dimensions["height"]+dimensions["gap"]))) == 0:
            self.report({"WARNING"}, "Model is too small on Z axis for an accurate calculation. Try scaling up your model or decreasing the brick size for a more accurate calculation.")
        return group_name

    @classmethod
    def createNewBricks(self, source, parent, source_details, dimensions, refLogo, action, cm=None, curFrame=None, sceneCurFrame=None, bricksDict=None, keys="ALL", replaceExistingGroup=True, selectCreated=False, printStatus=True):
        """ gets/creates bricksDict, runs makeBricks, and caches the final bricksDict """
        scn = bpy.context.scene
        if cm is None: cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        _,_,_,R, customData, customObj_details = getArgumentsForBricksDict(cm, source=source, source_details=source_details, dimensions=dimensions)
        updateCursor = action in ["CREATE", "UPDATE_MODEL"] # evaluates to boolean value
        if bricksDict is None:
            R2 = (R[0] * cm.distOffsetX, R[1] * cm.distOffsetY, R[2] * cm.distOffsetZ)
            bricksDict, loadedFromCache = getBricksDict(action, source=source, source_details=source_details, dimensions=dimensions, R=R2, updateCursor=updateCursor, curFrame=curFrame)
            if curFrame == sceneCurFrame:
                cm.activeKeyX = 1
                cm.activeKeyY = 1
                cm.activeKeyZ = 1
        else:
            loadedFromCache = True
        # reset all values for certain keys in bricksDict dictionaries
        if cm.buildIsDirty and loadedFromCache:
            threshold = getThreshold(cm)
            for kk in bricksDict.keys():
                bD = bricksDict[kk]
                if keys == "ALL" or kk in keys:
                    bD["size"] = None
                    bD["parent_brick"] = None
                    bD["top_exposed"] = None
                    bD["bot_exposed"] = None
                    if cm.lastShellThickness != cm.shellThickness:
                        bD["draw"] = bD["val"] >= threshold
                else:
                    # don't merge bricks not in 'keys'
                    bD["attempted_merge"] = True
        if not loadedFromCache or cm.internalIsDirty:
            updateInternal(bricksDict, cm, keys, clearExisting=loadedFromCache)
            cm.buildIsDirty = True
        group_name = 'Rebrickr_%(n)s_bricks_frame_%(curFrame)s' % locals() if curFrame is not None else None
        bricksCreated, bricksDict = makeBricks(parent, refLogo, dimensions, bricksDict, cm=cm, split=cm.splitModel, R=R, customData=customData, customObj_details=customObj_details, group_name=group_name, replaceExistingGroup=replaceExistingGroup, frameNum=curFrame, cursorStatus=updateCursor, keys=keys, printStatus=printStatus)
        if selectCreated:
            select(None)
            for brick in bricksCreated:
                select(brick, active=brick, only=False)
        cacheBricksDict(action, cm, bricksDict, curFrame=curFrame) # store current bricksDict to cache
        return group_name

    def isValid(self, source, Rebrickr_bricks_gn):
        """ returns True if brickify action can run, else report WARNING/ERROR and return False """
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        if cm.brickType == "Custom":
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
            if custom_details.x.dist < 0.00001:
                zeroDistAxes += "X"
            if custom_details.y.dist < 0.00001:
                zeroDistAxes += "Y"
            if custom_details.z.dist < 0.00001:
                zeroDistAxes += "Z"
            if zeroDistAxes != "":
                if len(zeroDistAxes) == 1:
                    warningMsg = "Custom brick type object is to small along the '%(zeroDistAxes)s' axis (<0.00001). Please select another object or extrude it along the '%(zeroDistAxes)s' axis." % locals()
                else:
                    warningMsg = "Custom brick type object is to small on the following axes (<0.00001): '%(zeroDistAxes)s'. Please select another object or extrude it along the '%(zeroDistAxes)s' axes." % locals()
                self.report({"WARNING"}, warningMsg)
                return False
        if cm.materialType == "Custom" and cm.materialName != "" and bpy.data.materials.find(cm.materialName) == -1:
            n = cm.materialName
            self.report({"WARNING"}, "Custom material '%(n)s' could not be found" % locals())
            return False

        self.clothMod = False
        source["ignored_mods"] = ""
        if self.action in ["CREATE", "ANIMATE"]:
            # verify function can run
            if groupExists(Rebrickr_bricks_gn):
                self.report({"WARNING"}, "Brickified Model already created.")
                return False
            # verify source exists and is of type mesh
            if cm.source_name == "":
                self.report({"WARNING"}, "Please select a mesh to Brickify")
                return False
            if cm.source_name[:9] == "Rebrickr_" and (cm.source_name[-7:] == "_bricks" or cm.source_name[-9:] == "_combined"):
                self.report({"WARNING"}, "Cannot Brickify models created with the Rebrickr")
                return False
            if source == None:
                n = cm.source_name
                self.report({"WARNING"}, "'%(n)s' could not be found" % locals())
                return False
            if source.type != "MESH":
                self.report({"WARNING"}, "Only 'MESH' objects can be Brickified. Please select another object (or press 'ALT-C to convert object to mesh).")
                return False
            # verify source is not a rigid body
            if source.rigid_body is not None:
                self.report({"WARNING"}, "Rebrickr: Rigid body physics not supported")
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
                    self.report({"WARNING"}, "'" + str(mod.type) + "' modifier not supported by the Rebrickr.")
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
            # make sure 'Rebrickr_[source name]_bricks' group exists
            if not groupExists(Rebrickr_bricks_gn):
                self.report({"WARNING"}, "Brickified Model doesn't exist. Create one with the 'Brickify Object' button.")
                return False

        # check that custom logo object exists in current scene and is of type "MESH"
        if cm.logoDetail == "Custom Logo" and cm.brickType != "Custom":
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
            if obj is not None and obj.layers[i] == True and scn.layers[i] == True:
                success = True
        if not success:
            self.report({"WARNING"}, "Object is not on active layer(s)")
            return False

        return True

    def transformBricks(self, bGroup, cm, parent, source, action):
        # if using local orientation and creating model for first time
        if cm.useLocalOrient and action == "CREATE":
            obj = parent if cm.splitModel else bGroup.objects[0]
            obj.rotation_mode = "XYZ"
            obj.rotation_euler = source.rotation_euler
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
            parent.location = (0,0,0)
            parent.rotation_euler = Euler((0,0,0), "XYZ")
            cm.transformScale = 1
            parent.scale = (1,1,1)
        # if model is not split
        elif not cm.splitModel:
            # apply stored transformation to bricks
            applyTransformData(list(bGroup.objects))
        # if model wasn't split but is now
        elif not cm.lastSplitModel:
            # apply stored transformation to parent of bricks
            applyTransformData(parent)
        obj = bGroup.objects[0]
        # if not split model
        if not cm.splitModel:
            # select the bricks object
            select(obj, active=obj)
            # if the model contains armature, lock the location, rotation, and scale
            if cm.armature:
                # lock location, rotation, and scale of created bricks
                obj.lock_location = [True, True, True]
                obj.lock_rotation = [True, True, True]
                obj.lock_scale    = [True, True, True]
        else:
            # set active object to obj (keeps original selection)
            select(None, active=obj)
        # match brick layers to source layers
        obj.layers = self.source.layers

    @classmethod
    def getLogo(self, cm):
        if cm.brickType != "Custom":
            if cm.logoDetail == "LEGO Logo":
                refLogo = self.getLegoLogo(self)
            else:
                refLogo = bpy.data.objects.get(cm.logoObjectName)
        else:
            refLogo = None
        return refLogo

    def getLegoLogo(self):
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        # update refLogo
        if cm.logoDetail == "None":
            refLogo = None
        else:
            decimate = False
            r = cm.logoResolution
            refLogoImport = bpy.data.objects.get("Rebrickr_refLogo")
            if refLogoImport is not None:
                refLogo = bpy.data.objects.get("Rebrickr_refLogo_%(r)s" % locals())
                if refLogo is None:
                    refLogo = bpy.data.objects.new("Rebrickr_refLogo_%(r)s" % locals(), refLogoImport.data.copy())
                    decimate = True
            else:
                # import refLogo and add to group
                refLogoImport = importLogo()
                refLogoImport.name = "Rebrickr_refLogo"
                safeUnlink(refLogoImport)
                refLogo = bpy.data.objects.new("Rebrickr_refLogo_%(r)s" % locals(), refLogoImport.data.copy())
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
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        activeFrame = scn.frame_current

        duplicates = {}

        lastObj = self.source
        for curFrame in range(startFrame, stopFrame + 1):
            sourceDup = None
            if self.action == "UPDATE_ANIM":
                # retrieve previously duplicated source
                sourceDup = bpy.data.objects.get("Rebrickr_" + source_name + "_frame_" + str(curFrame))
            if sourceDup is not None:
                duplicates[curFrame] = {"obj":sourceDup, "isReused":True}
                continue
            # duplicate source for current frame
            select(lastObj, active=lastObj)
            bpy.ops.object.duplicate()
            sourceDup = scn.objects.active
            sourceDup.name = "Rebrickr_" + cm.source_name + "_frame_" + str(curFrame)
            if sourceDup.name not in dGroup.objects.keys():
                dGroup.objects.link(sourceDup)
            duplicates[curFrame] = {"obj":sourceDup, "isReused":False}
            lastObj = sourceDup

        denom = stopFrame - startFrame
        if denom != 0: update_progress("Applying Modifiers", 0)

        for curFrame in range(startFrame, stopFrame + 1):
            if duplicates[curFrame]["isReused"]:
                continue
            sourceDup = duplicates[curFrame]["obj"]
            self.createdObjects.append(sourceDup.name)
            if sourceDup.parent is not None:
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
            # print status
            if denom != 0:
                percent = (curFrame - startFrame) / (denom + 1)
                if percent < 1:
                    update_progress("Applying Modifiers", percent)
            applyModifiers(sourceDup, exclude=["CLOTH", "SOFT_BODY"])
        if denom != 0: update_progress("Applying Modifiers", 1)

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
            if duplicates[curFrame]["isReused"]:
                continue
            sourceDup = duplicates[curFrame]["obj"]
            scn.frame_set(curFrame)
            # apply sourceDup modifiers
            applyModifiers(sourceDup, only=["CLOTH", "SOFT_BODY"])
            # apply animated transform data
            sourceDup.matrix_world = self.source.matrix_world
            sourceDup.animation_data_clear()
            scn.update()
            self.source["previous_location"] = sourceDup.location.to_tuple()
            sourceDup.rotation_mode = "XYZ"
            self.source["previous_rotation"] = tuple(sourceDup.rotation_euler)
            self.source["previous_scale"] = sourceDup.scale.to_tuple()
            select(sourceDup, active=sourceDup)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            scn.update()
            safeUnlink(sourceDup)
        return duplicates

    def getObjectToBrickify(self):
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        if self.action in ["UPDATE_MODEL", "UPDATE_ANIM"]:
            objToBrickify = bpy.data.objects.get(cm.source_name + " (DO NOT RENAME)")
        elif self.action in ["CREATE", "ANIMATE"]:
            objToBrickify = bpy.data.objects.get(cm.source_name)
            if objToBrickify is None:
                objToBrickify = bpy.context.active_object
        else:
            objToBrickify = bpy.data.objects.get(cm.source_name)
        return objToBrickify

    def getParent(self, Rebrickr_parent_on, loc):
        m = bpy.data.meshes.new(Rebrickr_parent_on + "_mesh")
        parent = bpy.data.objects.new(Rebrickr_parent_on, m)
        parent.location = loc
        safeScn = getSafeScn()
        safeScn.objects.link(parent)
        return parent

    #############################################
