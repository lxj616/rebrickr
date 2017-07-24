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
        scn = context.scene
        try:
            cm = scn.cmlist[scn.cmlist_index]
            if bpy.data.objects[cm.source_name].type == 'MESH':
                return True
        except:
            return False
        return False

    action = bpy.props.EnumProperty(
        items=(
            ("CREATE", "Create", ""),
            ("UPDATE_MODEL", "Update Model", ""),
            ("UPDATE_ANIM", "Update Animation", ""),
            ("ANIMATE", "Animate", ""),
            ("RUN_MODAL", "Run Modal Operator", "")
        )
    )

    def getObjectToLegoize(self):
        scn = bpy.context.scene
        if self.action in ["CREATE","ANIMATE"]:
            if bpy.data.objects.find(scn.cmlist[scn.cmlist_index].source_name) == -1:
                objToLegoize = bpy.context.active_object
            else:
                objToLegoize = bpy.data.objects[scn.cmlist[scn.cmlist_index].source_name]
        else:
            cm = scn.cmlist[scn.cmlist_index]
            n = cm.source_name
            objToLegoize = bpy.data.groups["LEGOizer_%(n)s" % locals()].objects[0]
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

    def getParent(self, LEGOizer_parent_gn, source, loc):
        if groupExists(LEGOizer_parent_gn) and len(bpy.data.groups[LEGOizer_parent_gn].objects) > 0:
            pGroup = bpy.data.groups[LEGOizer_parent_gn]
            parent = pGroup.objects[0]
            source_details = self.getDimensionsAndBounds(source, skipDimensions=True)
            parent.location = loc
        else:
            if groupExists(LEGOizer_parent_gn):
                bpy.data.groups.remove(bpy.data.groups[LEGOizer_parent_gn], True)
            # create new empty 'parent' object and add to new group
            parent = bpy.data.objects.new(LEGOizer_parent_gn, source.data)
            source_details = self.getDimensionsAndBounds(source, skipDimensions=True)
            parent.location = loc
            pGroup = bpy.data.groups.new(LEGOizer_parent_gn)
            pGroup.objects.link(parent)
        return parent


    def getRefLogo(self):
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        # update refLogo
        if cm.logoDetail == "None":
            refLogo = None
        else:
            decimate = False
            if groupExists("LEGOizer_refLogo") and len(bpy.data.groups["LEGOizer_refLogo"].objects) > 0:
                rlGroup = bpy.data.groups["LEGOizer_refLogo"]
                r = cm.logoResolution
                success = False
                for obj in rlGroup.objects:
                    if obj.name == "LEGOizer_refLogo_%(r)s" % locals():
                        refLogo = obj
                        success = True
                        break
                if not success:
                    refLogoImport = rlGroup.objects[0]
                    rlGroup.objects.unlink(rlGroup.objects[1])
                    refLogo = bpy.data.objects.new("LEGOizer_refLogo_%(r)s" % locals(), refLogoImport.data.copy())
                    rlGroup.objects.link(refLogo)
                    decimate = True
            else:
                # import refLogo and add to group
                refLogoImport = importLogo()
                scn.objects.unlink(refLogoImport)
                rlGroup = bpy.data.groups.new("LEGOizer_refLogo")
                rlGroup.objects.link(refLogoImport)
                r = cm.logoResolution
                refLogo = bpy.data.objects.new("LEGOizer_refLogo_%(r)s" % locals(), refLogoImport.data.copy())
                rlGroup.objects.link(refLogo)
                decimate = True
            # decimate refLogo
            # TODO: Speed this up, if possible
            if refLogo is not None and decimate and cm.logoResolution < 1:
                dMod = refLogo.modifiers.new('Decimate', type='DECIMATE')
                dMod.ratio = cm.logoResolution * 1.6
                scn.objects.link(refLogo)
                select(refLogo, active=refLogo)
                bpy.ops.object.modifier_apply(apply_as='DATA', modifier='Decimate')
                scn.objects.unlink(refLogo)
                print("decimated")

        return refLogo

    def createNewBricks(self, source, parent, source_details, dimensions, refLogo, curFrame=None):
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        if cm.brickType == "Custom":
            customObj = bpy.data.objects[cm.customObjectName]
            select(customObj, active=customObj)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            customObj_details = bounds(customObj)
            scale = cm.brickHeight/customObj_details.z.distance
            R = (scale * customObj_details.x.distance + dimensions["gap"], scale * customObj_details.y.distance + dimensions["gap"], scale * customObj_details.z.distance + dimensions["gap"])
            print(R)
        else:
            customObj_details = None
            R = (dimensions["width"]+dimensions["gap"], dimensions["width"]+dimensions["gap"], dimensions["height"]+dimensions["gap"])
        bricksDict = makeBricksDict(source, source_details, dimensions, R)
        if curFrame:
            group_name = 'LEGOizer_%(n)s_bricks_frame_%(curFrame)s' % locals()
        else:
            group_name = None
        makeBricks(parent, refLogo, dimensions, bricksDict, cm.splitModel, R=R, customObj=customObj, customObj_details=customObj_details, group_name=group_name, frameNum=curFrame)
        if int(round((source_details.x.distance)/(dimensions["width"]+dimensions["gap"]))) == 0:
            self.report({"WARNING"}, "Model is too small on X axis for an accurate calculation. Try scaling up your model or decreasing the brick size for a more accurate calculation.")
        if int(round((source_details.y.distance)/(dimensions["width"]+dimensions["gap"]))) == 0:
            self.report({"WARNING"}, "Model is too small on Y axis for an accurate calculation. Try scaling up your model or decreasing the brick size for a more accurate calculation.")
        if int(round((source_details.z.distance)/(dimensions["height"]+dimensions["gap"]))) == 0:
            self.report({"WARNING"}, "Model is too small on Z axis for an accurate calculation. Try scaling up your model or decreasing the brick size for a more accurate calculation.")
        return group_name

    def isValid(self, cm, source, LEGOizer_bricks_gn,):
        if cm.brickType == "Custom":
            if bpy.data.objects.find(cm.customObjectName) == -1:
                self.report({"WARNING"}, "Custom brick type object could not be found in file.")
                return False
            if bpy.data.objects[cm.customObjectName].type != "MESH":
                self.report({"WARNING"}, "Custom brick type object is not of type 'MESH'. Please select another object (or press 'ALT-C to convert object to mesh).")
                return False

        if self.action in ["CREATE", "ANIMATE"]:
            # verify function can run
            if groupExists(LEGOizer_bricks_gn):
                self.report({"WARNING"}, "LEGOized Model already created.")
                return False
            # verify source exists and is of type mesh
            if source == None:
                self.report({"WARNING"}, "Please select a mesh to LEGOize")
                return False
            if source.type != "MESH":
                self.report({"WARNING"}, "Only 'MESH' objects can be LEGOized. Please select another object (or press 'ALT-C to convert object to mesh).")
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
        return True

    def legoizeAnimation(self):
        # set up variables
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        cm.splitModel = False
        n = cm.source_name
        LEGOizer_bricks_gn = "LEGOizer_%(n)s_bricks" % locals()
        LEGOizer_parent_gn = "LEGOizer_%(n)s_parent" % locals()
        LEGOizer_source_gn = "LEGOizer_%(n)s" % locals()
        LEGOizer_source_dupes_gn = "LEGOizer_%(n)s_dupes" % locals()

        # if bpy.data.objects.find(scn.cmlist[scn.cmlist_index].source_name) == -1:
        #     sourceOrig = bpy.context.active_object
        # else:
        #     sourceOrig = bpy.data.objects[scn.cmlist[scn.cmlist_index].source_name]
        #
        sourceOrig = self.getObjectToLegoize()
        if self.action == "UPDATE_ANIM":
            scn.objects.link(sourceOrig)

        # if there are no changes to apply, simply return "FINISHED"
        if not cm.modelIsDirty and not cm.buildIsDirty and not cm.bricksAreDirty:
            return "FINISHED"

        # delete old bricks if present
        if self.action == "UPDATE_ANIM":
            legoizerDelete.cleanUp("ANIMATION")
        dGroup = bpy.data.groups.new(LEGOizer_source_dupes_gn)
        pGroup = bpy.data.groups.new(LEGOizer_parent_gn)

        parent0 = self.getParent(LEGOizer_parent_gn, sourceOrig, sourceOrig.location.to_tuple())

        refLogo = self.getRefLogo()

        # iterate through frames of animation and generate lego model
        for i in range(cm.stopFrame - cm.startFrame + 1):
            # duplicate source for current frame and apply transformation data
            # scn.layers = getLayersList(0)
            # source = bpy.data.objects.new(sourceOrig.name + "_" + str(i), sourceOrig.data.copy())
            # copyAnimationData(sourceOrig, source)
            select(sourceOrig, active=sourceOrig)
            bpy.ops.object.duplicate()
            source = scn.objects.active
            dGroup.objects.link(source)
            source.name = sourceOrig.name + "_" + str(i)
            # source.layers = getLayersList(i+1)
            # scn.layers = getLayersList(i+1)
            # apply animated transform data
            curFrame = cm.startFrame + i
            scn.frame_set(curFrame)
            source.matrix_world = sourceOrig.matrix_world
            source.animation_data_clear()
            scn.update()
            # scn.layers[0] = False
            # scn.objects.link(source)
            source["previous_location"] = source.location.to_tuple()
            select(source, active=source)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            scn.update()
            scn.objects.unlink(source)

            # get source_details and dimensions
            source_details, dimensions = self.getDimensionsAndBounds(source)

            # set up parent for this layer
            # TODO: Remove these from memory in the delete function, or don't use them at all
            parent = bpy.data.objects.new(LEGOizer_parent_gn + "_" + str(i), source.data.copy())
            if "Fluidsim" in sourceOrig.modifiers:
                parent.location = (source_details.x.mid + source["previous_location"][0] - parent0.location.x, source_details.y.mid + source["previous_location"][1] - parent0.location.y, source_details.z.mid + source["previous_location"][2] - parent0.location.z)
            else:
                parent.location = (source_details.x.mid - parent0.location.x, source_details.y.mid - parent0.location.y, source_details.z.mid - parent0.location.z)
            parent.parent = parent0
            pGroup = bpy.data.groups[LEGOizer_parent_gn] # TODO: This line was added to protect against segmentation fault in version 2.78. Once you're running 2.79, try it without this line!
            pGroup.objects.link(parent)
            scn.objects.link(parent)
            scn.update()
            scn.objects.unlink(parent)

            # create new bricks
            group_name = self.createNewBricks(source, parent, source_details, dimensions, refLogo, curFrame=curFrame)
            for obj in bpy.data.groups[group_name].objects:
                obj.hide = True

            print("completed frame " + str(curFrame))

        # create new source group and add source
        if not groupExists(LEGOizer_source_gn):
            # link source to new 'source' group
            sGroup = bpy.data.groups.new(LEGOizer_source_gn)
            sGroup.objects.link(sourceOrig)
        scn.objects.unlink(sourceOrig)
        cm.lastStartFrame = cm.startFrame
        cm.lastStopFrame = cm.stopFrame
        scn.frame_set(cm.lastStartFrame)
        cm.animated = True

    def legoizeModel(self):
        # set up variables
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        source = self.getObjectToLegoize()
        n = cm.source_name
        LEGOizer_bricks_gn = "LEGOizer_%(n)s_bricks" % locals()
        LEGOizer_parent_gn = "LEGOizer_%(n)s_parent" % locals()
        LEGOizer_source_gn = "LEGOizer_%(n)s" % locals()

        # if there are no changes to apply, simply return "FINISHED"
        if not (self.action == "CREATE" or cm.modelIsDirty or cm.buildIsDirty or cm.bricksAreDirty or (self.action == "UPDATE_MODEL" and len(bpy.data.groups[LEGOizer_bricks_gn].objects) == 0)):
            return{"FINISHED"}

        # delete old bricks if present
        if self.action == "UPDATE_MODEL":
            legoizerDelete.cleanUp("MODEL", skipDupes=True, skipParents=True, skipSource=True)

        if self.action == "CREATE":
            source["previous_location"] = source.location.to_tuple()
            rot = source.rotation_euler.copy()
            s = source.scale.to_tuple()
            source.location = (0,0,0)
            select(source, active=source)
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
            scn.update()

        # update scene so mesh data is available for ray casting
        if self.action == "UPDATE_MODEL":
            scn.objects.link(source)
            scn.update()
            scn.objects.unlink(source)
        else:
            scn.update()

        # if nonexistent, create new source group and add source
        if not groupExists(LEGOizer_source_gn):
            # link source to new 'source' group
            sGroup = bpy.data.groups.new(LEGOizer_source_gn)
            sGroup.objects.link(source)
            # unlink source from scene
            scn.objects.unlink(source)

        # get source_details and dimensions
        source_details, dimensions = self.getDimensionsAndBounds(source)

        parentLoc = (source_details.x.mid + source["previous_location"][0], source_details.y.mid + source["previous_location"][1], source_details.z.mid + source["previous_location"][2])
        parent = self.getParent(LEGOizer_parent_gn, source, parentLoc)

        # update refLogo
        refLogo = self.getRefLogo()

        # create new bricks
        self.createNewBricks(source, parent, source_details, dimensions, refLogo)

        cm.modelCreated = True

    def execute(self, context):
        # get start time
        startTime = time.time()

        # set up variables
        scn = context.scene
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        LEGOizer_bricks_gn = "LEGOizer_%(n)s_bricks" % locals()
        # LEGOizer_parent_gn = "LEGOizer_%(n)s_parent" % locals()
        # LEGOizer_source_gn = "LEGOizer_%(n)s" % locals()

        source = self.getObjectToLegoize()
        if not self.isValid(cm, source, LEGOizer_bricks_gn):
            return {"CANCELLED"}

        if self.action not in ["ANIMATE", "UPDATE_ANIM"]:
            self.legoizeModel()
        else:
            self.legoizeAnimation()

        # # set final variables
        stopAnimationModal()
        cm.lastLogoResolution = cm.logoResolution
        cm.lastLogoDetail = cm.logoDetail
        cm.lastSplitModel = cm.splitModel
        cm.modelIsDirty = False
        cm.buildIsDirty = False
        cm.bricksAreDirty = False

        disableRelationshipLines()

        # STOPWATCH CHECK
        stopWatch("Total Time Elapsed", time.time()-startTime)

        return{"FINISHED"}
