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

# Blender imports
import bpy
from mathutils import Vector, Euler
props = bpy.props

# Bricker imports
from ..functions import *
from .cache import *


def getModelType(self, cm=None):
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
        try:
            scn, cm, _ = getActiveContextInfo()
            self.undo_stack.iterateStates(cm)
            self.runFullDelete()
        except:
            handle_exception()

        return{"FINISHED"}

    ################################################
    # initialization method

    def __init__(self):
        self.undo_stack = UndoStack.get_instance()
        self.undo_stack.undo_push('brickify')

    #############################################
    # class methods

    @classmethod
    def cleanUp(cls, modelType, cm=None, skipSource=False, skipDupes=False, skipParents=False, preservedFrames=None):
        """ externally callable cleanup function for bricks, source, dupes, and parents """
        # set up variables
        scn = bpy.context.scene
        cm = cm or scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        Bricker_source_dupes_gn = "Bricker_%(n)s_dupes" % locals()
        source = bpy.data.objects.get("%(n)s (DO NOT RENAME)" % locals())

        # set layers to source layers temporarily
        curLayers = list(scn.layers)
        setLayers([True]*20)

        # clean up 'Bricker_[source name]' group
        if not skipSource:
            cls.cleanSource(source, modelType)

        # clean up 'Bricker_[source name]_dupes' group
        if groupExists(Bricker_source_dupes_gn) and not skipDupes:
            cls.cleanDupes(preservedFrames, modelType)

        if not skipParents:
            brickLoc, brickRot, brickScl = cls.cleanParents(preservedFrames, modelType)
        else:
            brickLoc, brickRot, brickScl = None, None, None

        # initialize variables for cursor status updates
        wm = bpy.context.window_manager
        wm.progress_begin(0, 100)
        print()

        cls.cleanBricks(preservedFrames, modelType)

        # finish status update
        update_progress("Deleting", 1)
        wm.progress_end()

        # set scene layers back to original layers
        setLayers(curLayers)

        return source, brickLoc, brickRot, brickScl

    @classmethod
    def runFullDelete(cls, cm=None):
        """ externally callable cleanup function for full delete action (clears everything from memory) """
        scn = bpy.context.scene
        scn.Bricker_runningOperation = True
        cm = cm or scn.cmlist[scn.cmlist_index]
        modelType = getModelType(cm)
        n = cm.source_name
        source = bpy.data.objects.get("%(n)s (DO NOT RENAME)" % locals())
        parentOb = None
        origFrame = scn.frame_current
        scn.frame_set(cm.modelCreatedOnFrame)

        # set scene layers for source adjustments
        if source is not None:
            # store last active layers
            lastLayers = list(scn.layers)
            # match source layers to brick layers
            brick = None
            gn = "Bricker_%(n)s_bricks" % locals()
            if groupExists(gn) and len(bpy.data.groups[gn].objects) > 0:
                brick = bpy.data.groups[gn].objects[0]
                source.layers = brick.layers
            # set active layers to source layers
            setLayers(source.layers)

        source, brickLoc, brickRot, brickScl = cls.cleanUp(modelType, cm=cm, skipSource=source is None)

        # select source
        if source is None:
            print("Source object for model could not be found")
        else:
            select(source, active=source)

            # apply transformation to source
            if not cm.armature and ((modelType == "MODEL" and (cm.applyToSourceObject and cm.lastSplitModel) or not cm.lastSplitModel) or (modelType == "ANIMATION" and cm.applyToSourceObject)):
                l, r, s = getTransformData()
                if modelType == "MODEL":
                    loc = strToTuple(cm.lastSourceMid, float)
                    if brickLoc is not None:
                        source.location = source.location + brickLoc - Vector(loc)
                    else:
                        source.location = Vector(l)# - Vector(loc)
                else:
                    source.location = Vector(l)
                source.scale = (source.scale[0] * s[0], source.scale[1] * s[1], source.scale[2] * s[2])
                source.rotation_mode = "XYZ"
                if cm.useLocalOrient:
                    source.rotation_euler = brickRot or Euler(tuple(r), "XYZ")
                else:
                    source.rotation_euler.rotate(Euler(tuple(r), "XYZ"))

            # return open layers to original
            scn.Bricker_runningOperation = False
            setLayers(lastLayers)

            # delete custom properties from source
            customPropNames = ["ignored_mods", "frame_parent_cleared", "old_parent", "previous_location", "previous_rotation", "previous_scale", "before_edit_location", "before_origin_set_location"]
            for cPN in customPropNames:
                try:
                    del source[cPN]
                except KeyError:
                    pass

        Caches.clearCache(cm, brick_mesh=False)

        # reset default values for select items in cmlist
        cls.resetCmlistAttrs()

        clearTransformData()

        # reset frame (for proper update), update scene and redraw 3D view
        scn.frame_set(origFrame)
        scn.update()
        tag_redraw_areas("VIEW_3D")

    def cleanSource(source, modelType):
        scn, cm, n = getActiveContextInfo()
        Bricker_bricks_gn = "Bricker_%(n)s_bricks" % locals()
        # link source to scene
        if source not in list(scn.objects):
            safeLink(source)
        # set source layers to brick layers
        if modelType == "MODEL":
            bGroup = bpy.data.groups.get(Bricker_bricks_gn)
        elif modelType == "ANIMATION":
            bGroup = bpy.data.groups.get(Bricker_bricks_gn + "_frame_" + str(cm.lastStartFrame))
        if bGroup and len(bGroup.objects) > 0:
            source.layers = list(bGroup.objects[0].layers)
        # select source and reset cm.modelHeight
        select(source, active=source)
        cm.modelHeight = -1
        # reset source parent to original parent object
        old_parent = bpy.data.objects.get(source["old_parent"])
        if old_parent:
            select([source, old_parent], active=old_parent)
            if source["frame_parent_cleared"] != -1:
                origFrame = scn.frame_current
                scn.frame_set(source["frame_parent_cleared"])
                bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
                scn.frame_set(origFrame)
        # if modifiers were ignored/disabled from view, enable in view
        if source["ignored_mods"] != "":
            for mn in source["ignored_mods"]:
                source.modifiers[mn].show_viewport = True
        source.name = n
        source.cmlist_id = -1

    def cleanDupes(preservedFrames, modelType):
        scn, cm, n = getActiveContextInfo()
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

    def cleanParents(preservedFrames, modelType):
        scn, cm, n = getActiveContextInfo()
        Bricker_bricks_gn = "Bricker_%(n)s_bricks" % locals()
        Bricker_parent_on = "Bricker_%(n)s_parent" % locals()
        brickLoc, brickRot, brickScl = None, None, None
        if preservedFrames is None:
            p = bpy.data.objects.get(Bricker_parent_on)
            if modelType == "ANIMATION" or cm.lastSplitModel:
                # store transform data of transformation parent object
                try:
                    loc_diff = p["loc_diff"]
                except:
                    loc_diff = None
                storeTransformData(p, offsetBy=p["loc_diff"])
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

    def cleanBricks(preservedFrames, modelType):
        scn, cm, n = getActiveContextInfo()
        wm = bpy.context.window_manager
        Bricker_bricks_gn = "Bricker_%(n)s_bricks" % locals()
        if modelType == "MODEL":
            # clean up Bricker_bricks group
            if groupExists(Bricker_bricks_gn):
                brickGroup = bpy.data.groups[Bricker_bricks_gn]
                bricks = getBricks()
                if not cm.lastSplitModel:
                    if len(bricks) > 0:
                        storeTransformData(bricks[0])
                last_percent = 0
                # remove objects
                for i, obj in enumerate(bricks):
                    percent = i/len(bricks)
                    if percent - last_percent > 0.001 and percent < 1:
                        update_progress("Deleting", percent)
                        wm.progress_update(percent*100)
                        last_percent
                    m = obj.data
                    bpy.data.objects.remove(obj, True)
                    bpy.data.meshes.remove(m, True)
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
                Bricker_bricks_cur_frame_gn = Bricker_bricks_gn + "_frame_" + str(i)
                brickGroup = bpy.data.groups.get(Bricker_bricks_cur_frame_gn)
                if brickGroup:
                    bricks = list(brickGroup.objects)
                    if len(bricks) > 0:
                        delete(bricks)
                    bpy.data.groups.remove(brickGroup, do_unlink=True)
            cm.animated = False

    def resetCmlistAttrs():
        scn, cm, n = getActiveContextInfo()
        cm.modelLoc = "-1,-1,-1"
        cm.modelRot = "-1,-1,-1"
        cm.modelScale = "-1,-1,-1"
        cm.transformScale = 1
        cm.modelCreatedOnFrame = -1
        cm.lastSourceMid = "-1,-1,-1"
        cm.lastLogoResolution = 0
        cm.lastLogoDetail = "NONE"
        cm.lastSplitModel = False
        cm.lastBrickType = "NONE"
        cm.lastMatrixSettings = "NONE"
        cm.lastMaterialType = "NONE"
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
