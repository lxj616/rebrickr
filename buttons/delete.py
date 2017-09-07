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
import time
from mathutils import Vector
from ..functions import *
props = bpy.props

class legoizerDelete(bpy.types.Operator):
    """ Delete LEGOized model """                                               # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "scene.legoizer_delete"                                         # unique identifier for buttons and menu items to reference.
    bl_label = "Delete LEGOized model from Blender"                             # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns false) """
        scn = context.scene
        if scn.cmlist_index == -1:
            return False
        return True

    def setModelType(self):
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        if cm.animated:
            self.modelType = "ANIMATION"
        elif cm.modelCreated:
            self.modelType = "MODEL"


    @classmethod
    def cleanUp(cls, modelType, skipSource=False, skipDupes=False, skipParents=False):
        # set up variables
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        source = bpy.data.objects["%(n)s (DO NOT RENAME)" % locals()]
        LEGOizer_bricks_gn = "LEGOizer_%(n)s_bricks" % locals()
        LEGOizer_parent_on = "LEGOizer_%(n)s_parent" % locals()
        LEGOizer_refBricks_gn = "LEGOizer_%(n)s_refBricks" % locals()
        LEGOizer_source_dupes_gn = "LEGOizer_%(n)s_dupes" % locals()
        brickLoc = None
        brickRot = None
        brickScale = None

        # clean up 'LEGOizer_[source name]' group
        if not skipSource:
            # link source to scene
            if not source in list(scn.objects):
                safeLink(source)
            select(source, active=source)
            cm.modelHeight = -1
            # reset source parent to original parent object
            old_parent = bpy.data.objects.get(source["old_parent"])
            if old_parent is not None:
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

        # clean up 'LEGOizer_[source name]_dupes' group
        if groupExists(LEGOizer_source_dupes_gn) and not skipDupes:
            dGroup = bpy.data.groups[LEGOizer_source_dupes_gn]
            dObjects = list(dGroup.objects)
            if len(dObjects) > 0:
                delete(dObjects)
            bpy.data.groups.remove(dGroup, do_unlink=True)

        if not skipParents:
            p = bpy.data.objects.get(LEGOizer_parent_on)
            if modelType == "ANIMATION" or cm.lastSplitModel:
                # store transform data of transformation parent object
                storeTransformData(p)
            if not cm.lastSplitModel and groupExists(LEGOizer_bricks_gn):
                brickGroup = bpy.data.groups[LEGOizer_bricks_gn]
                bgObjects = list(brickGroup.objects)
                b = bgObjects[0]
                scn.update()
                brickLoc = b.matrix_world.to_translation().copy()
                brickRot = b.matrix_world.to_euler().copy()
                brickScale = b.matrix_world.to_scale().copy()
            # clean up LEGOizer_parent objects
            pGroup = bpy.data.groups.get(LEGOizer_parent_on)
            if pGroup:
                for parent in pGroup.objects:
                    m = parent.data
                    bpy.data.objects.remove(parent, True)
                    bpy.data.meshes.remove(m, True)

        # initialize variables for cursor status updates
        wm = bpy.context.window_manager
        wm.progress_begin(0, 100)
        print()

        if modelType == "MODEL":
            # clean up LEGOizer_bricks group
            cm.modelCreated = False
            if groupExists(LEGOizer_bricks_gn):
                brickGroup = bpy.data.groups[LEGOizer_bricks_gn]
                bgObjects = list(brickGroup.objects)
                if not cm.lastSplitModel:
                    storeTransformData(bgObjects[0])
                # remove objects
                for i,obj in enumerate(bgObjects):
                    percent = i/len(bgObjects)
                    if percent < 1:
                        update_progress("Deleting", percent)
                        wm.progress_update(percent*100)
                    m = obj.data
                    bpy.data.objects.remove(obj, True)
                    bpy.data.meshes.remove(m, True)
                bpy.data.groups.remove(brickGroup, do_unlink=True)
        elif modelType == "ANIMATION":
            # clean up LEGOizer_bricks group
            cm.animated = False
            for i in range(cm.lastStartFrame, cm.lastStopFrame + 1):
                percent = (i - cm.lastStartFrame + 1)/(cm.lastStopFrame - cm.lastStartFrame + 1)
                if percent < 1:
                    update_progress("Deleting", percent)
                    wm.progress_update(percent*100)
                LEGOizer_bricks_cur_frame_gn = LEGOizer_bricks_gn + "_frame_" + str(i)
                brickGroup = bpy.data.groups.get(LEGOizer_bricks_cur_frame_gn)
                if brickGroup is not None:
                    bgObjects = list(brickGroup.objects)
                    if len(bgObjects) > 0:
                        delete(bgObjects)
                    bpy.data.groups.remove(brickGroup, do_unlink=True)
        update_progress("Deleting", 1)
        wm.progress_end()

        return source, brickLoc, brickRot, brickScale

    def execute(self, context):
        try:
            scn = context.scene
            scn.runningOperation = True
            cm = scn.cmlist[scn.cmlist_index]
            n = cm.source_name
            source = bpy.data.objects["%(n)s (DO NOT RENAME)" % locals()]
            LEGOizer_last_origin_on = "LEGOizer_%(n)s_last_origin" % locals()
            parentOb = None

            # store last active layers
            lastLayers = list(scn.layers)
            # match source layers to brick layers
            brick = None
            gn = "LEGOizer_%(n)s_bricks" % locals()
            if groupExists(gn) and len(bpy.data.groups[gn].objects) > 0:
                brick = bpy.data.groups[gn].objects[0]
                source.layers = brick.layers
            # set active layers to source layers
            scn.layers = source.layers

            self.setModelType()

            source, brickLoc, brickRot, brickScale = self.cleanUp(self.modelType)

            if (self.modelType == "MODEL" and (cm.applyToSourceObject and cm.lastSplitModel) or not cm.lastSplitModel) or (self.modelType == "ANIMATION" and cm.applyToSourceObject):
                l,r,s = getTransformData()
                if self.modelType == "MODEL":
                    loc = cm.lastSourceMid.split(",")
                    for i in range(len(loc)):
                        loc[i] = float(loc[i])
                    setOriginToObjOrigin(toObj=source, fromLoc=tuple(loc))
                    if brickLoc is not None:
                        if source.parent is not None:
                            parentOb = source.parent
                            source.parent = None
                        source.location = brickLoc
                    else:
                        source.location = Vector(l)
                else:
                    source.location = Vector(l)
                if brickRot is not None and brickScale is not None and self.modelType == "MODEL":
                    source.rotation_euler = brickRot
                    source.scale = brickScale
                    if parentOb is not None:
                        setParentKeepTransform(source, parentOb, scn)
                else:
                    source.rotation_euler = Vector(source.rotation_euler) + Vector(r)
                    source.scale = (source.scale[0] * s[0], source.scale[1] * s[1], source.scale[2] * s[2])

            # set origin to previous origin location
            last_origin_obj = bpy.data.objects.get(LEGOizer_last_origin_on)
            if last_origin_obj is not None:
                safeLink(last_origin_obj)
                scn.update()
                setOriginToObjOrigin(toObj=source, fromObj=last_origin_obj, deleteFromObj=True)

            # select source and return open layers to original
            select(source, active=source)
            scn.runningOperation = False
            scn.layers = lastLayers

            # delete custom properties from source
            customPropNames = ["ignored_mods", "frame_parent_cleared", "old_parent", "previous_location", "previous_rotation", "previous_scale", "before_edit_location", "before_origin_set_location"]
            for cPN in customPropNames:
                try:
                    del source[cPN]
                except:
                    pass

            # reset default values for select items in cmlist
            cm.modelLoc = "-1,-1,-1"
            cm.modelRot = "-1,-1,-1"
            cm.modelScale = "-1,-1,-1"
            cm.modelCreatedOnFrame = -1
            cm.lastSourceMid = "-1,-1,-1"
            cm.lastLogoResolution = 0
            cm.lastLogoDetail = 'None'
            cm.lastSplitModel = False
            cm.animIsDirty = True
            cm.materialIsDirty = True
            cm.modelIsDirty = True
            cm.buildIsDirty = True
            cm.sourceIsDirty = True
            cm.bricksAreDirty = True

            # reset frame (for proper update), update scene and redraw 3D view
            scn.frame_set(scn.frame_current)
            scn.update()
            redraw_areas("VIEW_3D")
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
