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
from mathutils import Matrix, Vector, Euler
props = bpy.props

class legoizerLegoize(bpy.types.Operator):
    """Select objects layer by layer and shift by given values"""               # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "scene.legoizer_legoize"                                        # unique identifier for buttons and menu items to reference.
    bl_label = "Create Build Animation"                                         # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns false) """
        # scn = context.scene
        # cm = scn.cmlist[scn.cmlist_index]
        # objIndex = bpy.data.objects.find(cm.source_name)
        # if objIndex == -1:
        #     return False
        return True

    action = bpy.props.EnumProperty(
        items=(
            ("CREATE", "Create", ""),
            ("UPDATE_MODEL", "Update Model", ""),
            ("UPDATE_ANIM", "Update Animation", ""),
            ("ANIMATE", "Animate", ""),
            ("RUN_MODAL", "Run Modal Operator", "")
        )
    )

    def modal(self, context, event):
        """ ??? """
        scn = context.scene

        if len(self.lastFrame) != len(scn.cmlist):
            self.lastFrame = [scn.frame_current-1]*len(scn.cmlist)

        for i,cm in enumerate(scn.cmlist):
            if cm.animated:
                if context.scene.frame_current != self.lastFrame[i]:
                    fn0 = self.lastFrame[i]
                    fn1 = scn.frame_current
                    if fn1 < cm.lastStartFrame:
                        fn1 = cm.lastStartFrame
                    elif fn1 > cm.lastStopFrame:
                        fn1 = cm.lastStopFrame
                    self.lastFrame[i] = fn1
                    if self.lastFrame[i] == fn0:
                        continue
                    n = cm.source_name

                    try:
                        curBricks = bpy.data.groups["LEGOizer_%(n)s_bricks_frame_%(fn1)s" % locals()]
                        for brick in curBricks.objects:
                            brick.hide = False
                            # scn.objects.link(brick)
                    except Exception as e:
                        print(e)
                    try:
                        lastBricks = bpy.data.groups["LEGOizer_%(n)s_bricks_frame_%(fn0)s" % locals()]
                        for brick in lastBricks.objects:
                            brick.hide = True
                            # scn.objects.unlink(brick)
                            brick.select = False
                    except Exception as e:
                        print(e)
                    scn.update()
                    redraw_areas("VIEW_3D")

        if event.type in {"ESC"} and event.shift:
            scn.modalRunning = False
            bpy.context.window_manager["modal_running"] = False
            self.report({"INFO"}, "Modal Finished")
            return{"FINISHED"}
        return {"PASS_THROUGH"}

    def getObjectToLegoize(self):
        scn = bpy.context.scene
        if self.action in ["CREATE","ANIMATE"]:
            if bpy.data.objects.find(scn.cmlist[scn.cmlist_index].source_name) == -1:
                objToLegoize = bpy.context.active_object
            else:
                objToLegoize = bpy.data.objects[scn.cmlist[scn.cmlist_index].source_name]
        else:
            cm = scn.cmlist[scn.cmlist_index]
            objToLegoize = bpy.data.objects.get(cm.source_name)
        return objToLegoize

    def getDimensionsAndBounds(self, source, skipDimensions=False):
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
        bricksDict = makeBricksDict(source, source_details, dimensions, R)
        if curFrame is not None:
            group_name = 'LEGOizer_%(n)s_bricks_frame_%(curFrame)s' % locals()
        else:
            group_name = None
        makeBricks(parent, refLogo, dimensions, bricksDict, cm.splitModel, R=R, customData=customData, customObj_details=customObj_details, group_name=group_name, frameNum=curFrame)
        if int(round((source_details.x.distance)/(dimensions["width"]+dimensions["gap"]))) == 0:
            self.report({"WARNING"}, "Model is too small on X axis for an accurate calculation. Try scaling up your model or decreasing the brick size for a more accurate calculation.")
        if int(round((source_details.y.distance)/(dimensions["width"]+dimensions["gap"]))) == 0:
            self.report({"WARNING"}, "Model is too small on Y axis for an accurate calculation. Try scaling up your model or decreasing the brick size for a more accurate calculation.")
        if int(round((source_details.z.distance)/(dimensions["height"]+dimensions["gap"]))) == 0:
            self.report({"WARNING"}, "Model is too small on Z axis for an accurate calculation. Try scaling up your model or decreasing the brick size for a more accurate calculation.")
        return group_name

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
        source["ignored_mods"] = None
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
            # if source is soft body and
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

        if self.action == "UPDATE_MODEL":
            # make sure 'LEGOizer_[source name]_bricks' group exists
            if not groupExists(LEGOizer_bricks_gn):
                self.report({"WARNING"}, "LEGOized Model doesn't exist. Create one with the 'LEGOize Object' button.")
                return False

        success = False
        for i in range(20):
            if source.layers[i] == True and scn.layers[i] == True:
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

        sourceOrig = self.getObjectToLegoize()
        if self.action == "UPDATE_ANIM":
            safeLink(sourceOrig)

        # if there are no changes to apply, simply return "FINISHED"
        self.updatedFramesOnly = False
        if not self.action == "ANIMATE" and not cm.modelIsDirty and not cm.buildIsDirty and not cm.bricksAreDirty and (cm.materialType == "Custom" or not cm.materialIsDirty):
            if cm.animIsDirty:
                self.updatedFramesOnly = True
            else:
                return "FINISHED"

        if cm.splitModel:
            cm.splitModel = False

        # delete old bricks if present
        if self.action == "UPDATE_ANIM" and not self.updatedFramesOnly:
            legoizerDelete.cleanUp("ANIMATION", skipDupes=True)

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
                    if mod.type in ["ARMATURE", "SOLIDIFY", "MIRROR", "ARRAY", "BEVEL", "BOOLEAN", "SKIN", "OCEAN"] and mod.show_viewport:
                        try:
                            bpy.ops.object.modifier_apply(apply_as='DATA', modifier=mod.name)
                        except:
                            mod.show_viewport = False
                # apply animated transform data
                source.matrix_world = sourceOrig.matrix_world
                source.animation_data_clear()
                scn.update()
                source["previous_location"] = source.location.to_tuple()
                select(source, active=source)
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                scn.update()
                safeUnlink(source)

            # get source_details and dimensions
            source_details, dimensions = self.getDimensionsAndBounds(source)

            if self.action == "CREATE":
                # set source model height for display in UI
                cm.modelHeight = source_details.z.distance

            # set up parent for this layer
            # TODO: Remove these from memory in the delete function, or don't use them at all
            parent = bpy.data.objects.new(LEGOizer_parent_on + "_frame_" + str(curFrame), source.data)
            parent.location = (source_details.x.mid - parent0.location.x, source_details.y.mid - parent0.location.y, source_details.z.mid - parent0.location.z)
            parent.parent = parent0
            pGroup = bpy.data.groups[LEGOizer_parent_on] # redefine pGroup since it was removed
            pGroup.objects.link(parent)
            scn.objects.link(parent)
            scn.update()
            safeUnlink(parent)

            # create new bricks
            group_name = self.createNewBricks(source, parent, source_details, dimensions, refLogo, curFrame=curFrame)
            for obj in bpy.data.groups[group_name].objects:
                if curFrame != cm.startFrame:
                    obj.hide = True
                # lock location, rotation, and scale of created bricks
                obj.lock_location = [True, True, True]
                obj.lock_rotation = [True, True, True]
                obj.lock_scale    = [True, True, True]

            print("completed frame " + str(curFrame))

        cm.lastStartFrame = cm.startFrame
        cm.lastStopFrame = cm.stopFrame
        scn.frame_set(cm.lastStartFrame)
        cm.animated = True

    def legoizeModel(self):
        # set up variables
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        source = None
        sourceOrig = self.getObjectToLegoize()
        n = cm.source_name
        LEGOizer_bricks_gn = "LEGOizer_%(n)s_bricks" % locals()
        bGroup = bpy.data.groups.get(LEGOizer_bricks_gn)
        LEGOizer_parent_on = "LEGOizer_%(n)s_parent" % locals()

        # get or create parent group
        pGroup = bpy.data.groups.get(LEGOizer_parent_on)
        if pGroup is None:
            pGroup = bpy.data.groups.new(LEGOizer_parent_on)

        # if there are no changes to apply, simply return "FINISHED"
        if not self.action == "CREATE" and not cm.modelIsDirty and not cm.buildIsDirty and not cm.bricksAreDirty and (cm.materialType == "Custom" or not cm.materialIsDirty) and not (self.action == "UPDATE_MODEL" and len(bpy.data.groups[LEGOizer_bricks_gn].objects) == 0):
            return{"FINISHED"}

        # delete old bricks if present and store
        if self.action == "UPDATE_MODEL":
            legoizerDelete.cleanUp("MODEL", skipDupes=True, skipParents=True, skipSource=True)
        else:
            storeTransformData(None)

        if self.action == "CREATE":
            # create dupes group
            LEGOizer_source_dupes_gn = "LEGOizer_%(n)s_dupes" % locals()
            dGroup = bpy.data.groups.new(LEGOizer_source_dupes_gn)
            # duplicate source and add duplicate to group
            select(sourceOrig, active=sourceOrig)
            bpy.ops.object.duplicate()
            source = scn.objects.active
            dGroup.objects.link(source)
            select(source, active=source)
            source.name = sourceOrig.name + "_duplicate"
            # set up source["old_parent"] and remove source parent
            source["frame_parent_cleared"] = None
            if source.parent is not None:
                source["old_parent"] = source.parent.name
                source["frame_parent_cleared"] = scn.frame_current
                select(source, active=source)
                bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
            # list modifiers that need to be applied
            for mod in sourceOrig.modifiers:
                if mod.type in ["ARMATURE", "SOLIDIFY", "MIRROR", "ARRAY", "BEVEL", "BOOLEAN", "SKIN", "OCEAN"] and mod.show_viewport:
                    try:
                        bpy.ops.object.modifier_apply(apply_as='DATA', modifier=mod.name)
                    except:
                        mod.show_viewport = False
            # apply transformation data
            source["previous_location"] = source.location.to_tuple()
            source.location = (0,0,0)
            select(source, active=source)
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
            scn.update()
        else:
            source = bpy.data.objects.get(sourceOrig.name + "_duplicate")
        # if duplicate not created, source is just original source
        if source is None:
            source = sourceOrig

        # update scene so mesh data is available for ray casting
        if source.name not in scn.objects.keys():
            safeLink(source)
        scn.update()

        # get source_details and dimensions
        source_details, dimensions = self.getDimensionsAndBounds(source)

        if self.action == "CREATE":
            # set source model height for display in UI
            cm.modelHeight = source_details.z.distance

        # get parent object
        parent = bpy.data.objects.get(LEGOizer_parent_on)
        if parent is None:
            parentLoc = (source_details.x.mid + source["previous_location"][0], source_details.y.mid + source["previous_location"][1], source_details.z.mid + source["previous_location"][2])
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
            setTransformData(list(bGroup.objects))

        if source != sourceOrig:
            safeUnlink(source)

        cm.modelCreated = True

    def execute(self, context):
        # get start time
        startTime = time.time()

        # set up variables
        scn = context.scene
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        LEGOizer_bricks_gn = "LEGOizer_%(n)s_bricks" % locals()

        if self.action == "RUN_MODAL" and not modalRunning():
            self.lastFrame = []
            bpy.context.window_manager["modal_running"] = True
            context.window_manager.modal_handler_add(self)
            return {"RUNNING_MODAL"}

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

        # # set final variables
        cm.lastLogoResolution = cm.logoResolution
        cm.lastLogoDetail = cm.logoDetail
        cm.lastSplitModel = cm.splitModel
        cm.materialIsDirty = False
        cm.modelIsDirty = False
        cm.buildIsDirty = False
        cm.bricksAreDirty = False

        # unlink source from scene and link to safe scene
        if source.name in scn.objects.keys():
            safeUnlink(source)

        disableRelationshipLines()

        # STOPWATCH CHECK
        stopWatch("Total Time Elapsed", time.time()-startTime)

        if not modalRunning():
            self.lastFrame = []
            bpy.context.window_manager["modal_running"] = True
            context.window_manager.modal_handler_add(self)
            return {"RUNNING_MODAL"}
        else:
            return{"FINISHED"}

    def cancel(self, context):
        scn = context.scene
        bpy.context.window_manager["modal_running"] = False
