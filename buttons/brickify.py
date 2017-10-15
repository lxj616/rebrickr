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
from ..functions import *
# from ..functions.wrappers import timed_call
from .materials import RebrickrApplyMaterial
from .delete import RebrickrDelete
from .bevel import RebrickrBevel


def updateCanRun(type):
    scn = bpy.context.scene
    if scn.name == "Rebrickr_storage (DO NOT RENAME)":
        return True
    elif scn.cmlist_index == -1:
        return False
    else:
        cm = scn.cmlist[scn.cmlist_index]
        if type == "ANIMATION":
            return (cm.logoDetail != "None" and cm.logoDetail != "LEGO Logo") or cm.brickType == "Custom" or cm.modelIsDirty or cm.matrixIsDirty or cm.buildIsDirty or cm.bricksAreDirty or (cm.materialType != "Custom" and (cm.materialIsDirty or cm.brickMaterialsAreDirty))
        elif type == "MODEL":
            # set up variables
            n = cm.source_name
            Rebrickr_bricks_gn = "Rebrickr_%(n)s_bricks" % locals()
            return (cm.logoDetail != "None" and cm.logoDetail != "LEGO Logo") or cm.brickType == "Custom" or cm.modelIsDirty or cm.matrixIsDirty or cm.sourceIsDirty or cm.buildIsDirty or cm.bricksAreDirty or (cm.materialType != "Custom" and not (cm.materialType == "Random" and not (cm.splitModel or cm.lastMaterialType != cm.materialType)) and (cm.materialIsDirty or cm.brickMaterialsAreDirty)) or (groupExists(Rebrickr_bricks_gn) and len(bpy.data.groups[Rebrickr_bricks_gn].objects) == 0)

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

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns false) """
        if context.scene.name == "Rebrickr_storage (DO NOT RENAME)":
            scn = bpy.data.scenes.get(bpy.props.Rebrickr_origScene)
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

    def __init__(self):
        self.createdObjects = []
        self.createdGroups = []
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        self.setAction(scn, cm)
        self.sourceOrig = self.getObjectToBrickify()

    def getObjectToBrickify(self):
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        if self.action in ["UPDATE_MODEL", "COMMIT_UPDATE_MODEL", "UPDATE_ANIM"]:
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

    def getBricksDict(self, source, source_details, dimensions, R, updateCursor, curFrame=None):
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        useCaching = bpy.context.user_preferences.addons[bpy.props.rebrickr_module_name].preferences.useCaching
        # current_source_hash = json.dumps(hash_object(source))
        if useCaching and not cm.matrixIsDirty and cm.BFMCache != "" and not cm.sourceIsDirty and (self.action != "UPDATE_ANIM" or not cm.animIsDirty):#current_source_hash == cm.source_hash:
            if self.action in ["UPDATE_MODEL", "COMMIT_UPDATE_MODEL"]:
                bricksDict = json.loads(cm.BFMCache)
            elif self.action == "UPDATE_ANIM":
                bricksDict = json.loads(cm.BFMCache)[str(curFrame)]
        else:
            bricksDict = makeBricksDict(source, source_details, dimensions, R, cursorStatus=updateCursor)
            if useCaching:
                if self.action in ["CREATE", "UPDATE_MODEL", "COMMIT_UPDATE_MODEL"]:
                    # cm.source_hash = current_source_hash
                    cm.BFMCache = json.dumps(bricksDict)
                elif self.action in ["ANIMATE", "UPDATE_ANIM"]:
                    if cm.BFMCache == "":
                        BFMCache = {}
                    else:
                        BFMCache = json.loads(cm.BFMCache)
                    BFMCache[curFrame] = bricksDict
                    cm.BFMCache = json.dumps(BFMCache)
        # after dict is stored to cache, update materials
        if len(source.material_slots) > 0:
            bricksDict = addMaterialsToBricksDict(bricksDict, source)
        return bricksDict

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
        bricksDict = self.getBricksDict(source, source_details, dimensions, R, updateCursor, curFrame)
        if curFrame is not None:
            group_name = 'Rebrickr_%(n)s_bricks_frame_%(curFrame)s' % locals()
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
        """ sets self.action """
        if cm.modelCreated:
            self.action = "UPDATE_MODEL"
        elif cm.animated:
            self.action = "UPDATE_ANIM"
        elif not cm.useAnimation:
            self.action = "CREATE"
        else:
            self.action = "ANIMATE"

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
            if custom_details.x.distance < 0.00001:
                zeroDistAxes += "X"
            if custom_details.y.distance < 0.00001:
                zeroDistAxes += "Y"
            if custom_details.z.distance < 0.00001:
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

        if self.action in ["UPDATE_MODEL", "COMMIT_UPDATE_MODEL"]:
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
            if len(bricks) > 0:
                obj = bricks[0]
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

    def transformBricks(self, bGroup, cm, parent, parentLoc, updateParentLoc):
            # set transformation of objects in brick group
            if (self.action == "CREATE" and cm.sourceIsDirty):
                setTransformData(list(bGroup.objects))
            # transfer transformation of parent to object
            elif cm.lastSplitModel and not cm.splitModel:
                parent.rotation_mode = "XYZ"
                for obj in bGroup.objects:
                    obj.location = parent.location
                    obj.rotation_mode = parent.rotation_mode
                    obj.rotation_euler = parent.rotation_euler
                    obj.scale = parent.scale
                parent.location = (0,0,0)
                parent.rotation_euler = Euler((0,0,0), "XYZ")
                parent.scale = (1,1,1)
            elif not cm.splitModel:
                setTransformData(list(bGroup.objects), self.sourceOrig)
            # set transformation of brick group parent
            elif not cm.lastSplitModel:
                print("entered here...")
                setTransformData(parent, self.sourceOrig)
            # in this case, the parent was not removed so the transformations should stay the same
            elif cm.sourceIsDirty:
                pass
            # if not split model, select the bricks object
            obj = bGroup.objects[0]
            if not cm.splitModel:
                select(obj, active=obj)
                # if the model contains armature, lock the location, rotation, and scale
                if cm.armature:
                    # lock location, rotation, and scale of created bricks
                    obj.lock_location = [True, True, True]
                    obj.lock_rotation = [True, True, True]
                    obj.lock_scale    = [True, True, True]
            else:
                select(obj, active=obj, only=False)
                obj.select = False
            # match brick layers to source layers
            obj.layers = self.sourceOrig.layers
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

    def getDuplicateObjects(self, dGroup, source_name, startFrame, stopFrame):
        """ returns list of duplicates from sourceOrig with all traits applied """
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]

        duplicates = {}

        lastObj = self.sourceOrig
        for curFrame in range(startFrame, stopFrame + 1):
            source = None
            if self.action == "UPDATE_ANIM":
                # retrieve previously duplicated source
                source = bpy.data.objects.get("Rebrickr_" + source_name + "_frame_" + str(curFrame))
            if source is not None:
                duplicates[curFrame] = {"obj":source, "isReused":True}
                continue
            # duplicate source for current frame
            select(lastObj, active=lastObj)
            bpy.ops.object.duplicate()
            source = scn.objects.active
            source.name = "Rebrickr_" + cm.source_name + "_frame_" + str(curFrame)
            if source.name not in dGroup.objects.keys():
                dGroup.objects.link(source)
            duplicates[curFrame] = {"obj":source, "isReused":False}
            lastObj = source

        for curFrame in range(startFrame, stopFrame + 1):
            if duplicates[curFrame]["isReused"]:
                continue
            source = duplicates[curFrame]["obj"]
            self.createdObjects.append(source.name)
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
            # apply modifiers
            for mod in source.modifiers:
                if mod.type in ["ARMATURE", "SOLIDIFY", "MIRROR", "ARRAY", "BEVEL", "BOOLEAN", "SKIN", "OCEAN", "FLUID_SIMULATION"] and mod.show_viewport:
                    try:
                        bpy.ops.object.modifier_apply(apply_as='DATA', modifier=mod.name)
                    except:
                        mod.show_viewport = False

        # store lastObj transform data to sourceOrig
        if lastObj != self.sourceOrig:
            self.sourceOrig["previous_location"] = lastObj.location.to_tuple()
            lastObj.rotation_mode = "XYZ"
            self.sourceOrig["previous_rotation"] = tuple(lastObj.rotation_euler)
            self.sourceOrig["previous_scale"] = lastObj.scale.to_tuple()

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
            source = duplicates[curFrame]["obj"]
            scn.frame_set(curFrame)
            select(source, active=source)
            # apply baked cloth and soft body modifiers
            for mod in lastObj.modifiers:
                if mod.type in ["CLOTH", "SOFT_BODY"] and mod.show_viewport:
                    try:
                        bpy.ops.object.modifier_apply(apply_as='DATA', modifier=mod.name)
                    except:
                        mod.show_viewport = False
            # apply animated transform data
            source.matrix_world = self.sourceOrig.matrix_world
            source.animation_data_clear()
            scn.update()
            self.sourceOrig["previous_location"] = source.location.to_tuple()
            source.rotation_mode = "XYZ"
            self.sourceOrig["previous_rotation"] = tuple(source.rotation_euler)
            self.sourceOrig["previous_scale"] = source.scale.to_tuple()
            select(source, active=source)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            scn.update()
            safeUnlink(source)
        return duplicates

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
            safeLink(self.sourceOrig)

        # if there are no changes to apply, simply return "FINISHED"
        self.updatedFramesOnly = False
        if self.action == "UPDATE_ANIM" and not updateCanRun("ANIMATION"):
            if cm.animIsDirty:
                self.updatedFramesOnly = True
            else:
                return "FINISHED"

        if (self.action == "ANIMATE" or cm.matrixIsDirty or cm.sourceIsDirty or cm.animIsDirty) and not self.updatedFramesOnly:
            cm.BFMCache = ""

        if cm.splitModel:
            cm.splitModel = False

        # delete old bricks if present
        if self.action == "UPDATE_ANIM":
            preservedFrames = None
            if self.updatedFramesOnly:
                # preserve duplicates, parents, and bricks for frames that haven't changed
                preservedFrames = [cm.startFrame, cm.stopFrame]
            RebrickrDelete.cleanUp("ANIMATION", skipDupes=not self.updatedFramesOnly, skipParents=not self.updatedFramesOnly, preservedFrames=preservedFrames)
            self.sourceOrig.name = self.sourceOrig.name + " (DO NOT RENAME)"

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
            parent0 = self.getParent(Rebrickr_parent_on, self.sourceOrig.location.to_tuple())
            pGroup.objects.link(parent0)
            cm.parent_name = parent0.name
        self.createdObjects.append(parent0.name)

        # update refLogo
        if cm.brickType != "Custom":
            if cm.logoDetail == "LEGO Logo":
                refLogo = self.getLegoLogo()
            else:
                refLogo = bpy.data.objects.get(cm.logoObjectName)
        else:
            refLogo = None

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
            source_details, dimensions = getDimensionsAndBounds(source)

            if self.action == "ANIMATE":
                # set source model height for display in UI
                cm.modelHeight = source_details.z.distance

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
                self.createdObjects.append(parent)

            # create new bricks
            try:
                group_name = self.createNewBricks(source, parent, source_details, dimensions, refLogo, curFrame=curFrame)
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
                obj.layers = self.sourceOrig.layers

        for obj in objsToSelect:
            obj.hide = False
            obj.hide_render = False
            select(obj, active=obj)

        wm.progress_end()
        cm.lastStartFrame = cm.startFrame
        cm.lastStopFrame = cm.stopFrame
        scn.frame_set(sceneCurFrame)

        cm.animated = True

    def brickifyModel(self):
        """ create brick model """
        # set up variables
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        origFrame = None
        source = None
        n = cm.source_name
        Rebrickr_bricks_gn = "Rebrickr_%(n)s_bricks" % locals()
        Rebrickr_last_origin_on = "Rebrickr_%(n)s_last_origin" % locals()
        Rebrickr_parent_on = "Rebrickr_%(n)s_parent" % locals()
        updateParentLoc = False

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

        if self.action == "CREATE":
            # get origin location for source
            previous_origin = self.sourceOrig.matrix_world.to_translation().to_tuple()

            # create empty object at source's old origin location and set as child of source
            m = bpy.data.meshes.new("Rebrickr_%(n)s_last_origin_mesh" % locals())
            obj = bpy.data.objects.new("Rebrickr_%(n)s_last_origin" % locals(), m)
            self.createdObjects.append(Rebrickr_last_origin_on)
            obj.location = previous_origin
            scn.objects.link(obj)
            select([obj, self.sourceOrig], active=self.sourceOrig)
            bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
            safeUnlink(obj)

        # if there are no changes to apply, simply return "FINISHED"
        if self.action in ["UPDATE_MODEL", "COMMIT_UPDATE_MODEL"] and not updateCanRun("MODEL"):
            return{"FINISHED"}

        sto_scn = bpy.data.scenes.get("Rebrickr_storage (DO NOT RENAME)")
        if sto_scn is not None:
            sto_scn.update()

        # delete old bricks if present
        if self.action in ["UPDATE_MODEL", "COMMIT_UPDATE_MODEL"]:
            if cm.sourceIsDirty:
                # alert that parent loc needs updating at the end
                updateParentLoc = True
                # delete source/dupes as well if source is dirty, but only delete parent if not cm.splitModel
                RebrickrDelete.cleanUp("MODEL", skipParents=True)#cm.splitModel)
            else:
                # else, skip source
                RebrickrDelete.cleanUp("MODEL", skipDupes=True, skipParents=True, skipSource=True)
        else:
            storeTransformData(None)

        if self.action == "CREATE" or cm.sourceIsDirty:
            # create dupes group
            Rebrickr_source_dupes_gn = "Rebrickr_%(n)s_dupes" % locals()
            dGroup = bpy.data.groups.new(Rebrickr_source_dupes_gn)
            self.createdGroups.append(dGroup.name)
            # set sourceOrig origin to previous origin location
            lastSourceOrigLoc = self.sourceOrig.matrix_world.to_translation().to_tuple()
            last_origin_obj = bpy.data.objects.get(Rebrickr_last_origin_on)
            setOriginToObjOrigin(toObj=self.sourceOrig, fromObj=last_origin_obj)
            # duplicate source and add duplicate to group
            select(self.sourceOrig, active=self.sourceOrig)
            bpy.ops.object.duplicate()
            source = scn.objects.active
            dGroup.objects.link(source)
            select(source, active=source)
            source.name = self.sourceOrig.name + "_duplicate"
            self.createdObjects.append(source.name)
            # reset sourceOrig origin to adjusted location
            setOriginToObjOrigin(toObj=self.sourceOrig, fromLoc=lastSourceOrigLoc)
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
                self.sourceOrig["previous_location"] = self.sourceOrig.location.to_tuple()
            self.sourceOrig.rotation_mode = "XYZ"
            self.sourceOrig["previous_rotation"] = tuple(self.sourceOrig.rotation_euler)
            self.sourceOrig["previous_scale"] = self.sourceOrig.scale.to_tuple()
            select(source, active=source)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            scn.update()
        else:
            # get previously greated source duplicate
            source = bpy.data.objects.get(n + "_duplicate")
        # if duplicate not created, source is just original source
        if source is None:
            source = self.sourceOrig

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
        parent = bpy.data.objects.get(Rebrickr_parent_on)
        # if parent doesn't exist, get parent with new location
        parentLoc = (source_details.x.mid, source_details.y.mid, source_details.z.mid)
        if parent is None:
            parent = self.getParent(Rebrickr_parent_on, parentLoc)
            cm.parent_name = parent.name
            pGroup.objects.link(parent)
        self.createdObjects.append(parent.name)

        # update refLogo
        if cm.brickType != "Custom":
            if cm.logoDetail == "LEGO Logo":
                refLogo = self.getLegoLogo()
            else:
                refLogo = bpy.data.objects.get(cm.logoObjectName)
        else:
            refLogo = None

        # create new bricks
        self.createNewBricks(source, parent, source_details, dimensions, refLogo)

        bGroup = bpy.data.groups.get(Rebrickr_bricks_gn) # redefine bGroup since it was removed
        if bGroup is not None:
            self.transformBricks(bGroup, cm, parent, parentLoc, updateParentLoc)

        # unlink source duplicate if created
        if source != self.sourceOrig and source.name in scn.objects.keys():
            safeUnlink(source)

        # add bevel if it was previously added
        if self.action == "UPDATE_MODEL" and cm.bevelAdded:
            bricks = getBricks()
            RebrickrBevel.runBevelAction(bricks, cm)

        cm.modelCreated = True

        cm.lastSourceMid = str(tuple(parentLoc))[1:-1]

        if origFrame is not None:
            scn.frame_set(origFrame)

    @timed_call('Total Time Elapsed')
    def runBrickify(self, context):
        # set up variables
        scn = context.scene
        scn.Rebrickr_runningOperation = True
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        previously_animated = cm.animated
        previously_model_created = cm.modelCreated
        Rebrickr_bricks_gn = "Rebrickr_%(n)s_bricks" % locals()

        # get source and initialize values
        source = self.getObjectToBrickify()
        source["old_parent"] = ""

        if not self.isValid(source, Rebrickr_bricks_gn):
            return {"CANCELLED"}

        if self.action not in ["ANIMATE", "UPDATE_ANIM"]:
            self.brickifyModel()
        else:
            self.brickifyAnimation()
            cm.animIsDirty = False

        if self.action in ["CREATE", "ANIMATE"] or cm.sourceIsDirty:
            source.name = cm.source_name + " (DO NOT RENAME)"

        # # set final variables
        cm.lastLogoResolution = cm.logoResolution
        cm.lastLogoDetail = cm.logoDetail
        cm.lastSplitModel = cm.splitModel
        cm.lastBrickType = cm.brickType
        cm.lastMaterialType = cm.materialType
        cm.materialIsDirty = False
        cm.brickMaterialsAreDirty = False
        cm.modelIsDirty = False
        cm.buildIsDirty = False
        cm.sourceIsDirty = False
        cm.bricksAreDirty = False
        cm.matrixIsDirty = False
        scn.Rebrickr_runningOperation = False

        # apply random materials
        if cm.materialType == "Random":
            bricks = getBricks()
            RebrickrApplyMaterial.applyRandomMaterial(context, bricks)

        # unlink source from scene and link to safe scene
        if source.name in scn.objects.keys():
            safeUnlink(source, hide=False)

        disableRelationshipLines()

    def execute(self, context):
        try:
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
                if self.sourceOrig is not None:
                    self.sourceOrig.protected = False
                    select(self.sourceOrig, active=self.sourceOrig)
                cm.animated = previously_animated
                cm.modelCreated = previously_model_created
            print()
            self.report({"WARNING"}, "Process forcably interrupted with 'KeyboardInterrupt'")
        except:
            self.handle_exception()

        return{"FINISHED"}

    def handle_exception(self):
        errormsg = print_exception('Rebrickr_log')
        # if max number of exceptions occur within threshold of time, abort!
        print('\n'*5)
        print('-'*100)
        print("Something went wrong. Please start an error report with us so we can fix it! (press the 'Report a Bug' button under the 'Brick Models' dropdown menu of the Rebrickr)")
        print('-'*100)
        print('\n'*5)
        showErrorMessage("Something went wrong. Please start an error report with us so we can fix it! (press the 'Report a Bug' button under the 'Brick Models' dropdown menu of the Rebrickr)", wrap=240)
