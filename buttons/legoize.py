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
import random
import time
import bmesh
import os
import math
from ..functions import *
from .delete import legoizerDelete
from .bevel import legoizerBevel
from mathutils import Matrix, Vector, Euler
props = bpy.props

def updateCanRun(type):
    scn = bpy.context.scene
    if scn.name == "LEGOizer_storage (DO NOT RENAME)":
        return True
    elif scn.cmlist_index == -1:
        return False
    else:
        cm = scn.cmlist[scn.cmlist_index]
        if type == "ANIMATION":
            return cm.modelIsDirty or cm.buildIsDirty or cm.bricksAreDirty or (cm.materialType == "Custom" and cm.materialIsDirty)
        elif type == "MODEL":
            # set up variables
            n = cm.source_name
            LEGOizer_bricks_gn = "LEGOizer_%(n)s_bricks" % locals()
            return cm.modelIsDirty or cm.sourceIsDirty or cm.buildIsDirty or cm.bricksAreDirty or (cm.materialType != "Custom" and cm.materialIsDirty) or (groupExists(LEGOizer_bricks_gn) and len(bpy.data.groups[LEGOizer_bricks_gn].objects) == 0)

def getDimensionsAndBounds(source, skipDimensions=False):
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    # get dimensions and bounds
    source_details = bounds(source)
    if not skipDimensions:
        if cm.brickType == "Plates" or cm.brickType == "Bricks and Plates":
            zScale = 0.333
        elif cm.brickType in ["Bricks", "Custom"]:
            zScale = 1
        dimensions = Bricks.get_dimensions(cm.brickHeight, zScale, cm.gap)
        return source_details, dimensions
    else:
        return source_details

class legoizerLegoize(bpy.types.Operator):
    """ Create LEGO sculpture from source object mesh """                       # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "scene.legoizer_legoize"                                        # unique identifier for buttons and menu items to reference.
    bl_label = "Create/Update LEGO model from Source Object"                 # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns false) """
        if context.scene.name == "LEGOizer_storage (DO NOT RENAME)":
            scn = bpy.data.scenes.get(bpy.props.origScene)
            if scn is None:
                return False
        else:
            scn = context.scene
        if scn.cmlist_index == -1:
            return False
        cm = scn.cmlist[scn.cmlist_index]
        if ((cm.animated and (not updateCanRun("ANIMATION") and not cm.animIsDirty))
           or (cm.modelCreated and not updateCanRun("MODEL"))):
            return False
        return True

    def getObjectToLegoize(self):
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        if self.action in ["UPDATE_MODEL", "COMMIT_UPDATE_MODEL", "UPDATE_ANIM"]:
            objToLegoize = bpy.data.objects.get(cm.source_name + " (DO NOT RENAME)")
        elif self.action in ["CREATE", "ANIMATE"]:
            objToLegoize = bpy.data.objects.get(cm.source_name)
            if objToLegoize is None:
                objToLegoize = bpy.context.active_object
        else:
            objToLegoize = bpy.data.objects.get(cm.source_name)
        return objToLegoize

    def getParent(self, LEGOizer_parent_on, loc):
        m = bpy.data.meshes.new(LEGOizer_parent_on + "_mesh")
        parent = bpy.data.objects.new(LEGOizer_parent_on, m)
        parent.location = loc
        safeScn = getSafeScn()
        safeScn.objects.link(parent)
        return parent


    def getRefLogo(self):
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        # update refLogo
        if cm.logoDetail == "None":
            refLogo = None
        else:
            decimate = False
            r = cm.logoResolution
            refLogoImport = bpy.data.objects.get("LEGOizer_refLogo")
            if refLogoImport is not None:
                refLogo = bpy.data.objects.get("LEGOizer_refLogo_%(r)s" % locals())
                if refLogo is None:
                    refLogo = bpy.data.objects.new("LEGOizer_refLogo_%(r)s" % locals(), refLogoImport.data.copy())
                    decimate = True
            else:
                # import refLogo and add to group
                refLogoImport = importLogo()
                refLogoImport.name = "LEGOizer_refLogo"
                safeUnlink(refLogoImport)
                refLogo = bpy.data.objects.new("LEGOizer_refLogo_%(r)s" % locals(), refLogoImport.data.copy())
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

    def createNewBricks(self, source, parent, source_details, dimensions, refLogo, curFrame=None):
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        if cm.brickType == "Custom":
            customObj0 = bpy.data.objects[cm.customObjectName]
            oldLayers = list(scn.layers) # store scene layers for later reset
            scn.layers = customObj0.layers # set scene layers to sourceOrig layers
            select(customObj0, active=customObj0)
            bpy.ops.object.duplicate()
            customObj = scn.objects.active
            select(customObj, active=customObj)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            customObj_details = bounds(customObj)
            customData = customObj.data
            bpy.data.objects.remove(customObj, True)
            scale = cm.brickHeight/customObj_details.z.distance
            R = (scale * customObj_details.x.distance + dimensions["gap"], scale * customObj_details.y.distance + dimensions["gap"], scale * customObj_details.z.distance + dimensions["gap"])
            scn.layers = oldLayers
        else:
            customData = None
            customObj_details = None
            R = (dimensions["width"]+dimensions["gap"], dimensions["width"]+dimensions["gap"], dimensions["height"]+dimensions["gap"])
        updateCursor = self.action in ["CREATE", "UPDATE_MODEL", "COMMIT_UPDATE_MODEL"] # evaluates to boolean value
        bricksDict = makeBricksDict(source, source_details, dimensions, R, cursorStatus=updateCursor)
        if curFrame is not None:
            group_name = 'LEGOizer_%(n)s_bricks_frame_%(curFrame)s' % locals()
        else:
            group_name = None
        makeBricks(parent, refLogo, dimensions, bricksDict, cm.splitModel, R=R, customData=customData, customObj_details=customObj_details, group_name=group_name, frameNum=curFrame, cursorStatus=updateCursor)
        if int(round((source_details.x.distance)/(dimensions["width"]+dimensions["gap"]))) == 0:
            self.report({"WARNING"}, "Model is too small on X axis for an accurate calculation. Try scaling up your model or decreasing the brick size for a more accurate calculation.")
        if int(round((source_details.y.distance)/(dimensions["width"]+dimensions["gap"]))) == 0:
            self.report({"WARNING"}, "Model is too small on Y axis for an accurate calculation. Try scaling up your model or decreasing the brick size for a more accurate calculation.")
        if int(round((source_details.z.distance)/(dimensions["height"]+dimensions["gap"]))) == 0:
            self.report({"WARNING"}, "Model is too small on Z axis for an accurate calculation. Try scaling up your model or decreasing the brick size for a more accurate calculation.")
        return group_name

    def setAction(self, scn, cm):

        if cm.modelCreated:
            self.action = "UPDATE_MODEL"
        elif cm.animated:
            self.action = "UPDATE_ANIM"
        elif not cm.useAnimation:
            self.action = "CREATE"
        else:
            self.action = "ANIMATE"

    def isValid(self, source, LEGOizer_bricks_gn,):
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        if cm.brickType == "Custom":
            if cm.customObjectName == "":
                self.report({"WARNING"}, "Custom brick type object not specified.")
                return False
            if bpy.data.objects.find(cm.customObjectName) == -1:
                n = cm.customObjectName
                self.report({"WARNING"}, "Custom brick type object '%(n)s' could not be found" % locals())
                return False
            if bpy.data.objects[cm.customObjectName].type != "MESH":
                self.report({"WARNING"}, "Custom brick type object is not of type 'MESH'. Please select another object (or press 'ALT-C to convert object to mesh).")
                return False

        self.clothMod = False
        source["ignored_mods"] = ""
        if self.action in ["CREATE", "ANIMATE"]:
            # verify function can run
            if groupExists(LEGOizer_bricks_gn):
                self.report({"WARNING"}, "LEGOized Model already created.")
                return False
            # verify source exists and is of type mesh
            if cm.source_name == "":
                self.report({"WARNING"}, "Please select a mesh to LEGOize")
                return False
            if cm.source_name[:9] == "LEGOizer_" and (cm.source_name[-7:] == "_bricks" or cm.source_name[-9:] == "_combined"):
                self.report({"WARNING"}, "Cannot LEGOize models created with the LEGOizer")
                return False
            if source == None:
                n = cm.source_name
                self.report({"WARNING"}, "'%(n)s' could not be found" % locals())
                return False
            if source.type != "MESH":
                self.report({"WARNING"}, "Only 'MESH' objects can be LEGOized. Please select another object (or press 'ALT-C to convert object to mesh).")
                return False
            # verify source is not a rigid body
            if source.rigid_body is not None:
                self.report({"WARNING"}, "LEGOizer: Rigid body physics not supported")
                return False
            # verify all appropriate modifiers have been applied
            ignoredMods = []
            for mod in source.modifiers:
                # abort render if these modifiers are enabled but not applied
                # if mod.type in ["ARRAY", "BEVEL", "BOOLEAN", "SKIN", "OCEAN"] and mod.show_viewport:
                #     self.report({"WARNING"}, "Please apply '" + str(mod.type) + "' modifier(s) or disable from view before LEGOizing the object.")
                #     return False
                # ignore these modifiers (disable from view until LEGOized model deleted)
                if mod.type in ["BUILD"] and mod.show_viewport:
                    mod.show_viewport = False
                    ignoredMods.append(mod.name)
                # these modifiers are unsupported - abort render if enabled
                if mod.type in ["SMOKE"] and mod.show_viewport:
                    self.report({"WARNING"}, "'" + str(mod.type) + "' modifier not supported by the LEGOizer.")
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
                    self.report({"WARNING"}, "Please apply '" + str(mod.type) + "' modifier or disable from view before LEGOizing the object.")
                    return False

        if self.action in ["ANIMATE", "UPDATE_ANIM"]:
            # verify start frame is less than stop frame
            if cm.startFrame > cm.stopFrame:
                self.report({"ERROR"}, "Start frame must be less than or equal to stop frame (see animation tab below).")
                return False
            # TODO: Alert user to bake fluid/cloth simulation before attempting to LEGOize

        if self.action in ["UPDATE_MODEL", "COMMIT_UPDATE_MODEL"]:
            # make sure 'LEGOizer_[source name]_bricks' group exists
            if not groupExists(LEGOizer_bricks_gn):
                self.report({"WARNING"}, "LEGOized Model doesn't exist. Create one with the 'LEGOize Object' button.")
                return False

        success = False
        if cm.modelCreated:
            g = bpy.data.groups.get(LEGOizer_bricks_gn)
        elif cm.animated:
            g = bpy.data.groups.get(LEGOizer_bricks_gn + "_frame_" + str(cm.lastStartFrame))
        if cm.modelCreated or cm.animated:
            if g is not None and len(g.objects) > 0:
                obj = g.objects[0]
            else:
                obj = None
        else:
            obj = source
        for i in range(20):
            if obj is not None and obj.layers[i] == True and scn.layers[i] == True:
                success = True
        if not success:
            self.report({"WARNING"}, "Object is not on active layer(s)")
            return False

        return True

    def legoizeAnimation(self):
        # set up variables
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        LEGOizer_bricks_gn = "LEGOizer_%(n)s_bricks" % locals()
        LEGOizer_parent_on = "LEGOizer_%(n)s_parent" % locals()
        LEGOizer_source_dupes_gn = "LEGOizer_%(n)s_dupes" % locals()
        sceneCurFrame = scn.frame_current

        sourceOrig = self.getObjectToLegoize()
        if self.action == "UPDATE_ANIM":
            safeLink(sourceOrig)

        # if there are no changes to apply, simply return "FINISHED"
        self.updatedFramesOnly = False
        if self.action == "UPDATE_ANIM" and not updateCanRun("ANIMATION"):
            if cm.animIsDirty:
                self.updatedFramesOnly = True
            else:
                return "FINISHED"

        if cm.splitModel:
            cm.splitModel = False

        # delete old bricks if present
        if self.action == "UPDATE_ANIM" and not self.updatedFramesOnly:
            legoizerDelete.cleanUp("ANIMATION", skipDupes=True, skipParents=True)
            sourceOrig.name = sourceOrig.name + " (DO NOT RENAME)"

        # get or create duplicate and parent groups
        dGroup = bpy.data.groups.get(LEGOizer_source_dupes_gn)
        if dGroup is None:
            dGroup = bpy.data.groups.new(LEGOizer_source_dupes_gn)
        pGroup = bpy.data.groups.get(LEGOizer_parent_on)
        if pGroup is None:
            pGroup = bpy.data.groups.new(LEGOizer_parent_on)

        # get parent object
        parent0 = bpy.data.objects.get(LEGOizer_parent_on)
        if parent0 is None:
            parent0 = self.getParent(LEGOizer_parent_on, sourceOrig.location.to_tuple())
            pGroup.objects.link(parent0)

        if cm.brickType != "Custom":
            refLogo = self.getRefLogo()
        else:
            refLogo = None

        # begin drawing status to cursor
        wm = bpy.context.window_manager
        wm.progress_begin(0, cm.stopFrame + 1 - cm.startFrame)

        # iterate through frames of animation and generate lego model
        for curFrame in range(cm.startFrame, cm.stopFrame + 1):

            if self.updatedFramesOnly and cm.lastStartFrame <= curFrame and curFrame <= cm.lastStopFrame:
                print("skipped frame %(curFrame)s" % locals())
                continue
            scn.frame_set(curFrame)
            # get duplicated source
            if self.action == "UPDATE_ANIM":
                # retrieve previously duplicated source
                source = bpy.data.objects.get("LEGOizer_" + sourceOrig.name + "_frame_" + str(curFrame))
            else:
                source = None
            if source is None:
                # duplicate source for current frame
                select(sourceOrig, active=sourceOrig)
                bpy.ops.object.duplicate()
                source = scn.objects.active
                dGroup.objects.link(source)
                source.name = "LEGOizer_" + sourceOrig.name + "_frame_" + str(curFrame)
                if source.parent is not None:
                    # apply parent transformation
                    select(source, active=source)
                    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
                # apply shape keys if existing
                shapeKeys = source.data.shape_keys
                if shapeKeys is not None and len(shapeKeys.key_blocks) > 0:
                    select(source, active=source)
                    bpy.ops.object.shape_key_add(from_mix=True)
                    for i in range(len(shapeKeys.key_blocks)):
                        source.shape_key_remove(source.data.shape_keys.key_blocks[0])
                    # bpy.ops.object.shape_key_remove(all=True)
                # bake and apply modifiers
                for mod in source.modifiers:
                    # apply cloth and soft body modifiers
                    if mod.type in ["CLOTH", "SOFT_BODY"] and mod.show_viewport:
                        if not mod.point_cache.use_disk_cache:
                            mod.point_cache.use_disk_cache = True
                        if mod.point_cache.frame_end >= scn.frame_current:
                            mod.point_cache.frame_end = scn.frame_current
                            override = {'scene': scn, 'active_object': source, 'point_cache': mod.point_cache}
                            bpy.ops.ptcache.bake(override, bake=True)
                            try:
                                bpy.ops.object.modifier_apply(apply_as='DATA', modifier=mod.name)
                            except:
                                mod.show_viewport = False
                    if mod.type in ["ARMATURE", "SOLIDIFY", "MIRROR", "ARRAY", "BEVEL", "BOOLEAN", "SKIN", "OCEAN", "FLUID_SIMULATION"] and mod.show_viewport:
                        try:
                            bpy.ops.object.modifier_apply(apply_as='DATA', modifier=mod.name)
                        except:
                            mod.show_viewport = False
                # apply animated transform data
                source.matrix_world = sourceOrig.matrix_world
                source.animation_data_clear()
                scn.update()
                sourceOrig["previous_location"] = source.location.to_tuple()
                source.rotation_mode = "XYZ"
                sourceOrig["previous_rotation"] = tuple(source.rotation_euler)
                sourceOrig["previous_scale"] = source.scale.to_tuple()
                select(source, active=source)
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                scn.update()
                safeUnlink(source)

            # get source_details and dimensions
            source_details, dimensions = getDimensionsAndBounds(source)

            if self.action == "CREATE":
                # set source model height for display in UI
                cm.modelHeight = source_details.z.distance

            # set up parent for this layer
            # TODO: Remove these from memory in the delete function, or don't use them at all
            pGroup = bpy.data.groups[LEGOizer_parent_on] # redefine pGroup since it was removed
            parent = bpy.data.objects.get(LEGOizer_parent_on + "_frame_" + str(curFrame))
            if parent is None:
                parent = bpy.data.objects.new(LEGOizer_parent_on + "_frame_" + str(curFrame), source.data)
                parent.location = (source_details.x.mid - parent0.location.x, source_details.y.mid - parent0.location.y, source_details.z.mid - parent0.location.z)
                parent.parent = parent0
                pGroup.objects.link(parent)
                scn.objects.link(parent)
                scn.update()
                safeUnlink(parent)

            # create new bricks
            group_name = self.createNewBricks(source, parent, source_details, dimensions, refLogo, curFrame=curFrame)
            for obj in bpy.data.groups[group_name].objects:
                if (curFrame == cm.startFrame and sceneCurFrame < cm.startFrame) or curFrame == sceneCurFrame or (curFrame == cm.stopFrame and sceneCurFrame > cm.stopFrame):
                    selectFromGroup = bpy.data.groups[group_name]
                else:
                    obj.hide = True
                # lock location, rotation, and scale of created bricks
                obj.lock_location = [True, True, True]
                obj.lock_rotation = [True, True, True]
                obj.lock_scale    = [True, True, True]

            wm.progress_update(curFrame-cm.startFrame)
            print("completed frame " + str(curFrame))

        for obj in selectFromGroup.objects:
            select(obj, active=obj)

        wm.progress_end()
        cm.lastStartFrame = cm.startFrame
        cm.lastStopFrame = cm.stopFrame
        scn.frame_set(sceneCurFrame)
        cm.animated = True

    def legoizeModel(self):
        # set up variables
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        origFrame = None
        source = None
        sourceOrig = self.getObjectToLegoize()
        n = cm.source_name
        LEGOizer_bricks_gn = "LEGOizer_%(n)s_bricks" % locals()
        bGroup = bpy.data.groups.get(LEGOizer_bricks_gn)
        LEGOizer_last_origin_on = "LEGOizer_%(n)s_last_origin" % locals()
        LEGOizer_parent_on = "LEGOizer_%(n)s_parent" % locals()
        updateParentLoc = False

        # get or create parent group
        pGroup = bpy.data.groups.get(LEGOizer_parent_on)
        if pGroup is None:
            pGroup = bpy.data.groups.new(LEGOizer_parent_on)

        if self.action == "CREATE":
            # set modelCreatedOnFrame
            cm.modelCreatedOnFrame = scn.frame_current
        else:
            origFrame = scn.frame_current
            scn.frame_set(cm.modelCreatedOnFrame)

        if self.action == "CREATE":
            # get origin location for source
            previous_origin = sourceOrig.matrix_world.to_translation().to_tuple()

            # create empty object at source's old origin location and set as child of source
            m = bpy.data.meshes.new("LEGOizer_%(n)s_last_origin_mesh" % locals())
            obj = bpy.data.objects.new("LEGOizer_%(n)s_last_origin" % locals(), m)
            obj.location = previous_origin
            scn.objects.link(obj)
            select([obj, sourceOrig], active=sourceOrig)
            bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
            safeUnlink(obj)

        # if there are no changes to apply, simply return "FINISHED"
        if self.action in ["UPDATE_MODEL", "COMMIT_UPDATE_MODEL"] and not updateCanRun("MODEL"):
            return{"FINISHED"}

        sto_scn = bpy.data.scenes.get("LEGOizer_storage (DO NOT RENAME)")
        if sto_scn is not None:
            sto_scn.update()

        # delete old bricks if present
        if self.action in ["UPDATE_MODEL", "COMMIT_UPDATE_MODEL"]:
            if cm.sourceIsDirty:
                # alert that parent loc needs updating at the end
                updateParentLoc = True
                # delete source/dupes as well if source is dirty, but only delete parent if not cm.splitModel
                legoizerDelete.cleanUp("MODEL", skipParents=True)#cm.splitModel)
            else:
                # else, skip source
                legoizerDelete.cleanUp("MODEL", skipDupes=True, skipParents=True, skipSource=True)
        else:
            storeTransformData(None)

        if self.action == "CREATE" or cm.sourceIsDirty:
            # create dupes group
            LEGOizer_source_dupes_gn = "LEGOizer_%(n)s_dupes" % locals()
            dGroup = bpy.data.groups.new(LEGOizer_source_dupes_gn)
            # set sourceOrig origin to previous origin location
            lastSourceOrigLoc = sourceOrig.location.to_tuple()
            last_origin_obj = bpy.data.objects.get(LEGOizer_last_origin_on)
            setOriginToObjOrigin(toObj=sourceOrig, fromObj=last_origin_obj)
            # duplicate source and add duplicate to group
            select(sourceOrig, active=sourceOrig)
            bpy.ops.object.duplicate()
            source = scn.objects.active
            dGroup.objects.link(source)
            select(source, active=source)
            source.name = sourceOrig.name + "_duplicate"
            # reset sourceOrig origin to adjusted location
            setOriginToObjOrigin(toObj=sourceOrig, fromLoc=lastSourceOrigLoc)
            # set up source["old_parent"] and remove source parent
            source["frame_parent_cleared"] = -1
            select(source, active=source)
            if source.parent is not None:
                source["old_parent"] = source.parent.name
                source["frame_parent_cleared"] = scn.frame_current
                bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
            # apply shape keys if existing
            shapeKeys = source.data.shape_keys
            if shapeKeys is not None and len(shapeKeys.key_blocks) > 0:
                select(source, active=source)
                bpy.ops.object.shape_key_add(from_mix=True)
                for i in range(len(shapeKeys.key_blocks)):
                    source.shape_key_remove(source.data.shape_keys.key_blocks[0])
                # bpy.ops.object.shape_key_remove(all=True)
            # list modifiers that need to be applied
            for mod in source.modifiers:
                if mod.type in ["ARMATURE", "SOLIDIFY", "MIRROR", "ARRAY", "BEVEL", "BOOLEAN", "SKIN", "OCEAN", "FLUID_SIMULATION"] and mod.show_viewport:
                    try:
                        bpy.ops.object.modifier_apply(apply_as='DATA', modifier=mod.name)
                    except:
                        mod.show_viewport = False
                if mod.type == "ARMATURE":
                    cm.armature = True
                else:
                    cm.armature = False

            # apply transformation data
            if self.action == "CREATE":
                sourceOrig["previous_location"] = source.location.to_tuple()
            source.rotation_mode = "XYZ"
            sourceOrig["previous_rotation"] = tuple(source.rotation_euler)
            sourceOrig["previous_scale"] = source.scale.to_tuple()
            select(source, active=source)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            scn.update()
        else:
            # get previously greated source duplicate
            source = bpy.data.objects.get(n + "_duplicate")
        # if duplicate not created, source is just original source
        if source is None:
            source = sourceOrig

        # link source if it isn't in scene
        if source.name not in scn.objects.keys():
            safeLink(source)
            scn.update()

        # get source_details and dimensions
        source_details, dimensions = getDimensionsAndBounds(source)

        if self.action == "CREATE":
            # set source model height for display in UI
            cm.modelHeight = source_details.z.distance

        # get parent object
        parent = bpy.data.objects.get(LEGOizer_parent_on)
        # if parent doesn't exist, get parent with new location
        parentLoc = (source_details.x.mid, source_details.y.mid, source_details.z.mid)
        if parent is None:
            parent = self.getParent(LEGOizer_parent_on, parentLoc)
            pGroup.objects.link(parent)

        # update refLogo
        if cm.brickType != "Custom":
            refLogo = self.getRefLogo()
        else:
            refLogo = None

        # create new bricks
        self.createNewBricks(source, parent, source_details, dimensions, refLogo)

        bGroup = bpy.data.groups.get(LEGOizer_bricks_gn) # redefine bGroup since it was removed
        if bGroup is not None:
            # set transformation of objects in brick group
            if (self.action == "CREATE" and cm.sourceIsDirty):
                setTransformData(list(bGroup.objects))
            elif cm.lastSplitModel and not cm.splitModel:
                pass
            elif not cm.splitModel:
                setTransformData(list(bGroup.objects), sourceOrig)
            # set transformation of brick group parent
            elif not cm.lastSplitModel:
                setTransformData(parent, sourceOrig)
            # in this case, the parent was not removed so the transformations should stay the same
            elif cm.sourceIsDirty:
                pass
            # if not split model, select the bricks object
            if not cm.splitModel:
                obj = bGroup.objects[0]
                select(obj, active=obj)
                # if the model contains armature, lock the location, rotation, and scale
                if cm.armature:
                    # lock location, rotation, and scale of created bricks
                    obj.lock_location = [True, True, True]
                    obj.lock_rotation = [True, True, True]
                    obj.lock_scale    = [True, True, True]
            else:
                obj = bGroup.objects[0]
                select(obj, active=obj, only=False)
                obj.select = False
            # update location of bricks in case source mesh has been edited
            if updateParentLoc:
                l = cm.lastSourceMid.split(",")
                for i in range(len(l)):
                    l[i] = float(l[i])
                lastSourceMid = tuple(l)
                v = Vector(parentLoc) - Vector(lastSourceMid)
                center_v = Vector((0, 0, 0))
                v_new = v - center_v
                if not cm.splitModel:
                    parent.rotation_mode = "XYZ"
                    eu1 = parent.rotation_euler
                    v_new.rotate(eu1)
                if not cm.lastSplitModel:
                    bGroup.objects[0].rotation_mode = "XYZ"
                    eu2 = bGroup.objects[0].rotation_euler
                    v_new.rotate(eu2)
                v_new += center_v
                for brick in bGroup.objects:
                    if not cm.lastSplitModel:
                        brick.location += Vector((v_new.x * parent.scale[0] * bGroup.objects[0].scale[0], v_new.y * parent.scale[1] * bGroup.objects[0].scale[1], v_new.z * parent.scale[2] * bGroup.objects[0].scale[2]))
                    else:
                        brick.location += Vector((v_new.x * parent.scale[0], v_new.y * parent.scale[1], v_new.z * parent.scale[2]))

        # unlink source duplicate if created
        if source != sourceOrig and source.name in scn.objects.keys():
            safeUnlink(source)

        # add bevel if it was previously added
        if self.action == "UPDATE_MODEL" and cm.bevelAdded:
            bGroup = bpy.data.groups.get("LEGOizer_%(n)s_bricks" % locals())
            legoizerBevel.runBevelAction(bGroup, cm)

        cm.modelCreated = True

        cm.lastSourceMid = str(tuple(parentLoc))[1:-1]

        if origFrame is not None:
            scn.frame_set(origFrame)

    def execute(self, context):
        try:
            # get start time
            startTime = time.time()

            # set up variables
            scn = context.scene
            scn.runningOperation = True
            cm = scn.cmlist[scn.cmlist_index]
            n = cm.source_name
            LEGOizer_bricks_gn = "LEGOizer_%(n)s_bricks" % locals()

            # set self.action
            self.setAction(scn, cm)

            # get source and initialize values
            source = self.getObjectToLegoize()
            source["old_parent"] = ""

            if not self.isValid(source, LEGOizer_bricks_gn):
                return {"CANCELLED"}

            if self.action not in ["ANIMATE", "UPDATE_ANIM"]:
                self.legoizeModel()
            else:
                self.legoizeAnimation()
                cm.animIsDirty = False

            if self.action in ["CREATE", "ANIMATE"] or cm.sourceIsDirty:
                source.name = cm.source_name + " (DO NOT RENAME)"

            # # set final variables
            cm.lastLogoResolution = cm.logoResolution
            cm.lastLogoDetail = cm.logoDetail
            cm.lastSplitModel = cm.splitModel
            cm.materialIsDirty = False
            cm.modelIsDirty = False
            cm.buildIsDirty = False
            cm.sourceIsDirty = False
            cm.bricksAreDirty = False
            scn.runningOperation = False

            # unlink source from scene and link to safe scene
            if source.name in scn.objects.keys():
                safeUnlink(source, hide=False)

            disableRelationshipLines()

            # STOPWATCH CHECK
            stopWatch("Total Time Elapsed", time.time()-startTime)
        except:
            self.handle_exception()

        return{"FINISHED"}

    def handle_exception(self):
        errormsg = print_exception('LEGOizer_log')
        # if max number of exceptions occur within threshold of time, abort!
        curtime = time.time()
        print('\n'*5)
        print('-'*100)
        print("Something went wrong. Please start an error report with us so we can fix it! (press the 'Report a Bug' button under the 'LEGO Models' dropdown menu of the LEGOizer)")
        print('-'*100)
        print('\n'*5)
        showErrorMessage("Something went wrong. Please start an error report with us so we can fix it! (press the 'Report a Bug' button under the 'LEGO Models' dropdown menu of the LEGOizer)", wrap=240)
