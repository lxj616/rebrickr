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
import time
import sys

# Blender imports
import bpy
from mathutils import Vector, Euler
props = bpy.props

# Addon imports
from ..functions import *
from .cache import *


def getModelType(cm=None):
    """ return 'MODEL' if modelCreated, 'ANIMATION' if animated """
    scn = bpy.context.scene
    cm = cm or scn.cmlist[scn.cmlist_index]
    if cm.animated:
        modelType = "ANIMATION"
    elif cm.modelCreated:
        modelType = "MODEL"
    return modelType


class BrickerDelete(bpy.types.Operator):
    """ Delete Brickified model """
    bl_idname = "bricker.delete"
    bl_label = "Delete Brickified model from Blender"
    bl_options = {"REGISTER", "UNDO"}

    ################################################
    # Blender Operator methods

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns false) """
        scn = bpy.context.scene
        if scn.cmlist_index == -1:
            return False
        return True

    def execute(self, context):
        scn, cm, _ = getActiveContextInfo()
        scn.Bricker_runningBlockingOperation = True
        try:
            self.undo_stack.iterateStates(cm)
            self.runFullDelete()
        except:
            handle_exception()
        scn.Bricker_runningBlockingOperation = False

        return{"FINISHED"}

    ################################################
    # initialization method

    def __init__(self):
        cm = getActiveContextInfo()[1]
        # push to undo stack
        self.undo_stack = UndoStack.get_instance()
        self.undo_stack.undo_push('delete', affected_ids=[cm.id])

    #############################################
    # class methods

    @classmethod
    def cleanUp(cls, modelType, cm=None, skipSource=False, skipDupes=False, skipParents=False, skipTransAndAnimData=True, preservedFrames=None, source_name=None):
        """ externally callable cleanup function for bricks, source, dupes, and parents """
        # set up variables
        scn = bpy.context.scene
        cm = cm or scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        Bricker_source_dupes_gn = "Bricker_%(n)s_dupes" % locals()
        source = bpy.data.objects.get(source_name or n)

        # set all layers active temporarily
        curLayers = list(scn.layers)
        setLayers([True]*20)
        # match source layers to brick layers
        gn = "Bricker_%(n)s_bricks" % locals()
        if groupExists(gn) and len(bpy.data.groups[gn].objects) > 0:
            brick = bpy.data.groups[gn].objects[0]
            source.layers = brick.layers

        # clean up 'Bricker_[source name]' group
        if not skipSource:
            cls.cleanSource(cm, source, modelType)

        # clean up 'Bricker_[source name]_dupes' group
        if groupExists(Bricker_source_dupes_gn) and not skipDupes:
            cls.cleanDupes(cm, preservedFrames, modelType)

        if not skipParents:
            brickLoc, brickRot, brickScl = cls.cleanParents(cm, preservedFrames, modelType)
        else:
            brickLoc, brickRot, brickScl = None, None, None

        # initialize variables for cursor status updates
        wm = bpy.context.window_manager
        wm.progress_begin(0, 100)
        print()

        trans_and_anim_data = cls.cleanBricks(scn, cm, n, preservedFrames, modelType, skipTransAndAnimData)

        # set scene layers back to original layers
        setLayers(curLayers)

        return source, brickLoc, brickRot, brickScl, trans_and_anim_data

    @classmethod
    def runFullDelete(cls, cm=None):
        """ externally callable cleanup function for full delete action (clears everything from memory) """
        scn = bpy.context.scene
        cm = cm or scn.cmlist[scn.cmlist_index]
        modelType = getModelType(cm)
        n = cm.source_name
        source = bpy.data.objects.get(n)
        origFrame = scn.frame_current
        scn.frame_set(cm.modelCreatedOnFrame)
        # store pivot point for model
        if cm.lastSplitModel or cm.animated:
            Bricker_parent_on = "Bricker_%(n)s_parent" % locals()
            p = bpy.data.objects.get(Bricker_parent_on)
            pivot_point = p.matrix_world.to_translation()
        else:
            bricks = getBricks()
            pivot_point = bricks[0].matrix_world.to_translation()
        # store last active layers
        lastLayers = list(scn.layers)

        source, brickLoc, brickRot, brickScl, _ = cls.cleanUp(modelType, cm=cm, skipSource=source is None)

        # select source
        if source is None:
            print("[Bricker] Source object for model could not be found")
        else:
            select(source, active=source)

            # apply transformation to source
            if not cm.armature and ((modelType == "MODEL" and (cm.applyToSourceObject or not cm.lastSplitModel)) or (modelType == "ANIMATION" and cm.applyToSourceObject)):
                l, r, s = getTransformData(cm)
                if modelType == "MODEL":
                    loc = strToTuple(cm.lastSourceMid, float)
                    if brickLoc is not None:
                        source.location = source.location + brickLoc - Vector(loc)
                    else:
                        source.location = Vector(l)# - Vector(loc)
                else:
                    source.location = Vector(l)
                source.scale = (source.scale[0] * s[0], source.scale[1] * s[1], source.scale[2] * s[2])
                lastMode = source.rotation_mode
                source.rotation_mode = "XYZ"
                # create vert to track original source origin
                last_co = source.data.vertices[0].co.to_tuple()
                source.data.vertices[0].co = (0, 0, 0)
                # set source origin to rotation point for transformed brick object
                setObjOrigin(source, pivot_point)
                # rotate source
                if cm.useLocalOrient and not cm.useAnimation:
                    source.rotation_euler = brickRot or Euler(tuple(r))
                else:
                    rotateBy = Euler(tuple(r))
                    # if source.parent is not None:
                    #     # TODO: convert rotateBy to local with respect to source's parent
                    source.rotation_euler.rotate(rotateBy)
                # set source origin back to original point (tracked by last vert)
                scn.update()
                setObjOrigin(source, source.matrix_world * source.data.vertices[0].co)
                source.data.vertices[0].co = last_co
                source.rotation_mode = lastMode
            # adjust source loc to account for local_orient_offset applied in BrickerBrickify.transformBricks
            if cm.useLocalOrient and not cm.useAnimation:
                try:
                    source.location -= Vector(source["local_orient_offset"])
                except KeyError:
                    pass

            # return open layers to original
            setLayers(lastLayers)

            # delete custom properties from source
            customPropNames = ["ignored_mods", "frame_parent_cleared", "old_parent"]
            for cPN in customPropNames:
                try:
                    del source[cPN]
                except KeyError:
                    pass

        Caches.clearCache(cm, brick_mesh=False)

        # reset default values for select items in cmlist
        cls.resetCmlistAttrs()

        clearTransformData(cm)

        # reset frame (for proper update), update scene and redraw 3D view
        scn.frame_set(origFrame)
        scn.update()
        tag_redraw_areas("VIEW_3D")

    @classmethod
    def cleanSource(cls, cm, source, modelType):
        scn = bpy.context.scene
        n = cm.source_name
        Bricker_bricks_gn = "Bricker_%(n)s_bricks" % locals()
        # link source to scene
        if source not in list(scn.objects):
            # ensureObjNamesUnique(scn)
            safeLink(source)
        # set source layers to brick layers
        if modelType == "MODEL":
            bGroup = bpy.data.groups.get(Bricker_bricks_gn)
        elif modelType == "ANIMATION":
            bGroup = bpy.data.groups.get(Bricker_bricks_gn + "_f_" + str(cm.lastStartFrame))
        if bGroup and len(bGroup.objects) > 0:
            source.layers = list(bGroup.objects[0].layers)
        # reset source parent to original parent object
        old_parent = bpy.data.objects.get(source["old_parent"])
        if old_parent:
            select([source, old_parent], active=old_parent, only=True)
            if source["frame_parent_cleared"] != -1:
                origFrame = scn.frame_current
                scn.frame_set(source["frame_parent_cleared"])
                bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
                scn.frame_set(origFrame)
        # if modifiers were ignored/disabled from view, enable in view
        if source["ignored_mods"] != "":
            for mn in source["ignored_mods"]:
                source.modifiers[mn].show_viewport = True
        # reset cm properties
        cm.modelHeight = -1
        # reset source properties
        source.name = n
        source.cmlist_id = -1

    @classmethod
    def cleanDupes(cls, cm, preservedFrames, modelType):
        scn = bpy.context.scene
        n = cm.source_name
        Bricker_source_dupes_gn = "Bricker_%(n)s_dupes" % locals()
        dGroup = bpy.data.groups[Bricker_source_dupes_gn]
        dObjects = list(dGroup.objects)
        # if preserve frames, remove those objects from dObjects
        objsToRemove = []
        if modelType == "ANIMATION" and preservedFrames is not None:
            for obj in dObjects:
                frameNumIdx = obj.name.rfind("_") + 1
                curFrameNum = int(obj.name[frameNumIdx:])
                if curFrameNum >= preservedFrames[0] and curFrameNum <= preservedFrames[1]:
                    objsToRemove.append(obj)
            for obj in objsToRemove:
                dObjects.remove(obj)
        if len(dObjects) > 0:
            delete(dObjects)
        if preservedFrames is None:
            bpy.data.groups.remove(dGroup, do_unlink=True)

    @classmethod
    def cleanParents(cls, cm, preservedFrames, modelType):
        scn = bpy.context.scene
        n = cm.source_name
        Bricker_bricks_gn = "Bricker_%(n)s_bricks" % locals()
        Bricker_parent_on = "Bricker_%(n)s_parent" % locals()
        brickLoc, brickRot, brickScl = None, None, None
        if preservedFrames is None:
            p = bpy.data.objects.get(Bricker_parent_on)
            if modelType == "ANIMATION" or cm.lastSplitModel:
                # store transform data of transformation parent object
                try:
                    loc_diff = p["loc_diff"]
                except KeyError:
                    loc_diff = None
                storeTransformData(cm, p, offsetBy=loc_diff)
            if not cm.lastSplitModel and groupExists(Bricker_bricks_gn):
                bricks = getBricks()
                if len(bricks) > 0:
                    b = bricks[0]
                    scn.update()
                    brickLoc = b.matrix_world.to_translation().copy()
                    brickRot = b.matrix_world.to_euler().copy()
                    brickScl = b.matrix_world.to_scale().copy()  # currently unused
        # clean up Bricker_parent objects
        pGroup = bpy.data.groups.get(Bricker_parent_on)
        if pGroup:
            for parent in pGroup.objects:
                # if preserve frames, skip those parents
                if modelType == "ANIMATION" and preservedFrames is not None:
                    frameNumIdx = parent.name.rfind("_") + 1
                    try:
                        curFrameNum = int(parent.name[frameNumIdx:])
                        if curFrameNum >= preservedFrames[0] and curFrameNum <= preservedFrames[1]:
                            continue
                    except ValueError:
                        continue
                m = parent.data
                bpy.data.objects.remove(parent, True)
                bpy.data.meshes.remove(m, True)
            if preservedFrames is None:
                bpy.data.groups.remove(pGroup, do_unlink=True)
        return brickLoc, brickRot, brickScl

    def updateAnimationData(objs, trans_and_anim_data):
        """ add anim data for objs to 'trans_and_anim_data' """
        for obj in objs:
            obj.rotation_mode = "XYZ"
            trans_and_anim_data.append({"name":obj.name, "loc":obj.location.to_tuple(), "rot":obj.rotation_euler.copy(), "scale":obj.scale.to_tuple(), "action":obj.animation_data.action.copy() if obj.animation_data and obj.animation_data.action else None})

    @classmethod
    def cleanBricks(cls, scn, cm, n, preservedFrames, modelType, skipTransAndAnimData):
        trans_and_anim_data = []
        wm = bpy.context.window_manager
        Bricker_bricks_gn = "Bricker_%(n)s_bricks" % locals()
        if modelType == "MODEL":
            # clean up Bricker_bricks group
            sys.stdout.write("\rDeleting...")
            sys.stdout.flush()
            if groupExists(Bricker_bricks_gn):
                brickGroup = bpy.data.groups[Bricker_bricks_gn]
                bricks = getBricks()
                if not cm.lastSplitModel:
                    if len(bricks) > 0:
                        storeTransformData(cm, bricks[0])
                if not skipTransAndAnimData:
                    cls.updateAnimationData(bricks, trans_and_anim_data)
                last_percent = 0
                # remove objects
                select(bricks, only=True)
                bpy.ops.object.delete(update_model=False, undo=False)
                bpy.data.groups.remove(brickGroup, do_unlink=True)
            cm.modelCreated = False
        elif modelType == "ANIMATION":
            # clean up Bricker_bricks group
            for i in range(cm.lastStartFrame, cm.lastStopFrame + 1):
                if preservedFrames is not None and i >= preservedFrames[0] and i <= preservedFrames[1]:
                    continue
                percent = (i - cm.lastStartFrame + 1)/(cm.lastStopFrame - cm.lastStartFrame + 1)
                if percent < 1:
                    update_progress("Deleting", percent)
                    wm.progress_update(percent*100)
                Bricker_bricks_curF_gn = Bricker_bricks_gn + "_f_" + str(i)
                brickGroup = bpy.data.groups.get(Bricker_bricks_curF_gn)
                if brickGroup:
                    bricks = list(brickGroup.objects)
                    if not skipTransAndAnimData:
                        cls.updateAnimationData(bricks, trans_and_anim_data)
                    if len(bricks) > 0:
                        delete(bricks)
                    bpy.data.groups.remove(brickGroup, do_unlink=True)
            cm.animated = False
        # finish status update
        update_progress("Deleting", 1)
        wm.progress_end()
        return trans_and_anim_data

    def resetCmlistAttrs():
        scn, cm, n = getActiveContextInfo()
        cm.modelLoc = "-1,-1,-1"
        cm.modelRot = "-1,-1,-1"
        cm.modelScale = "-1,-1,-1"
        cm.transformScale = 1
        cm.modelCreatedOnFrame = -1
        cm.lastSourceMid = "-1,-1,-1"
        cm.lastLogoDetail = "NONE"
        cm.lastSplitModel = False
        cm.lastBrickType = "NONE"
        cm.lastMatrixSettings = "NONE"
        cm.lastMaterialType = "NONE"
        cm.lastIsSmoke = False
        cm.animIsDirty = True
        cm.materialIsDirty = True
        cm.modelIsDirty = True
        cm.buildIsDirty = True
        cm.matrixIsDirty = True
        cm.bricksAreDirty = True
        cm.armature = False
        cm.exposeParent = False
        cm.version = bpy.props.bricker_version
        cm.activeKeyX = -1
        cm.activeKeyY = -1
        cm.activeKeyZ = -1
        cm.firstKey = ""
        cm.isSmoke = False
        cm.hasCustomBrick = False
