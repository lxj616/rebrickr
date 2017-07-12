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
from mathutils import Matrix, Vector
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
            ("UPDATE", "Update", ""),
        )
    )

    def getObjectToLegoize(self):
        scn = bpy.context.scene
        if self.action == "CREATE":
            if bpy.data.objects.find(scn.cmlist[scn.cmlist_index].source_name) == -1:
                objToLegoize = bpy.context.active_object
            else:
                objToLegoize = bpy.data.objects[scn.cmlist[scn.cmlist_index].source_name]
        else:
            cm = scn.cmlist[scn.cmlist_index]
            n = cm.source_name
            objToLegoize = bpy.data.groups["LEGOizer_%(n)s" % locals()].objects[0]
        return objToLegoize

    def unhide(self, context):
        # clean up 'LEGOizer_hidden' group
        if groupExists("LEGOizer_hidden"):
            hiddenGroup = bpy.data.groups["LEGOizer_hidden"]
            unhide(list(hiddenGroup.objects))
            # select(list(hiddenGroup.objects), deselect=True)
            bpy.data.groups.remove(hiddenGroup, do_unlink=True)

    def modal(self, context, event):
        """ When pressed, 'legoize mode' (loose concept) is deactivated """
        if event.type in {"RET", "NUMPAD_ENTER"} and event.shift:
            self.report({"INFO"}, "changes committed")
            self.unhide(context)
            n = context.scene.cmlist[context.scene.cmlist_index].source_name
            sourceGroup = bpy.data.groups["LEGOizer_%(n)s" % locals()]
            sourceGroup.objects[0].draw_type = 'WIRE'
            sourceGroup.objects[0].hide_render = True

            return{"FINISHED"}

        if context.scene.cmlist_index == -1 or not context.scene.cmlist[context.scene.cmlist_index].changesToCommit:
            self.unhide(context)
            return{"FINISHED"}
        return {"PASS_THROUGH"}

    def isValid(self, LEGOizer_bricks, source):
        if self.action == "CREATE":
            # verify function can run
            if groupExists("LEGOizer_hidden"):
                self.report({"INFO"}, "Commit changes to last LEGOized model by pressing SHIFT-ENTER.")
            if groupExists(LEGOizer_bricks):
                self.report({"WARNING"}, "LEGOized Model already created. To create a new LEGOized model, first press 'Commit LEGOized Mesh'.")
                return False
            # verify source exists and is of type mesh
            if source == None:
                self.report({"WARNING"}, "Please select a mesh to LEGOize")
                return False
            if source.type != "MESH":
                self.report({"WARNING"}, "Only 'MESH' objects can be LEGOized. Please select another object (or press 'ALT-C to convert object to mesh).")
                return False

        if self.action == "UPDATE":
            # make sure 'LEGOizer_[source name]_bricks' group exists
            if not groupExists(LEGOizer_bricks):
                self.report({"WARNING"}, "LEGOized Model doesn't exist. Create one with the 'LEGOize Object' button.")
                return False

        return True

    def execute(self, context):
        # get start time
        startTime = time.time()

        # set up variables
        scn = context.scene
        cm = scn.cmlist[scn.cmlist_index]
        source = self.getObjectToLegoize()
        n = cm.source_name
        LEGOizer_bricks = "LEGOizer_%(n)s_bricks" % locals()

        if not self.isValid(LEGOizer_bricks, source):
             return {"CANCELLED"}

        if not groupExists("LEGOizer_%(n)s"):
            # create 'LEGOizer_[cm.source_name]' group with source object
            sGroup = bpy.data.groups.new("LEGOizer_%(n)s" % locals())
            sGroup.objects.link(source)

        # get cross section
        source_details = bounds(source)
        dimensions = Bricks.get_dimensions(cm.brickHeight, cm.gap)
        # axis, lScale, CS_slices = getCrossSection(source, source_details, dimensions)

        # update refLogo
        if cm.logoDetail == "None":
            refLogo = None
        elif groupExists("LEGOizer_refLogo"):
            refLogoImport = bpy.data.groups["LEGOizer_refLogo"].objects[0]
            refLogo = bpy.data.objects.new(refLogoImport.name+"2", refLogoImport.data.copy())
        else:
            # import refLogo and add to group
            refLogoImport = importLogo()
            scn.objects.unlink(refLogoImport)
            rlGroup = bpy.data.groups.new("LEGOizer_refLogo")
            rlGroup.objects.link(refLogoImport)
            refLogo = bpy.data.objects.new(refLogoImport.name+"2", refLogoImport.data.copy())

        # # decimate refLogo
        # if refLogo and cm.logoResolution < 1:
        #     dMod = refLogo.modifiers.new('Decimate', type='DECIMATE')
        #     dMod.ratio = cm.logoResolution
        #     scn.objects.link(refLogo)
        #     select(refLogo, active=refLogo)
        #     bpy.ops.object.modifier_apply(apply_as='DATA', modifier='Decimate')


        # set up refLogoHidden and refLogoExposed based on cm.logoDetail
        if cm.logoDetail == "On Exposed Bricks":
            refLogoHidden = None
            refLogoExposed = refLogo
            print("exposed")
        elif cm.logoDetail == "On All Bricks":
            refLogoHidden = refLogo
            refLogoExposed = refLogo
            print("all")
        elif cm.logoDetail == "None":
            refLogoHidden = None
            refLogoExposed = None
            print("none")
        if groupExists("LEGOizer_%(n)s_refBricks" % locals()) and len(bpy.data.groups["LEGOizer_%(n)s_refBricks" % locals()].objects) > 0:
                rbGroup = bpy.data.groups["LEGOizer_%(n)s_refBricks" % locals()]
                # get 1x1 refBrick from group
                refBrickHidden = rbGroup.objects[0]
                refBrickUpper = rbGroup.objects[1]
                refBrickLower = rbGroup.objects[2]
                refBrickUpperLower = rbGroup.objects[3]
                rbGroup.objects.unlink(refBrickHidden)
                rbGroup.objects.unlink(refBrickUpper)
                rbGroup.objects.unlink(refBrickLower)
                rbGroup.objects.unlink(refBrickUpperLower)
                # update that refBrick
                m0 = Bricks.new_mesh(name=refBrickHidden.name, height=dimensions["height"], type=[1,1], undersideDetail=cm.hiddenUndersideDetail, logo=refLogoHidden)
                refBrickHidden.data = m0
                m1 = Bricks().new_mesh(name=refBrickUpper.name, height=dimensions["height"], type=[1,1], undersideDetail=cm.hiddenUndersideDetail, logo=refLogoExposed)
                refBrickUpper.data = m1
                m2 = Bricks().new_mesh(name=refBrickLower.name, height=dimensions["height"], type=[1,1], undersideDetail=cm.exposedUndersideDetail, logo=refLogoHidden)
                refBrickLower.data = m2
                m3 = Bricks().new_mesh(name=refBrickUpperLower.name, height=dimensions["height"], type=[1,1], undersideDetail=cm.exposedUndersideDetail, logo=refLogoExposed)
                refBrickUpperLower.data = m3
                # link refBricks to new group
                rbGroup.objects.link(refBrickHidden)
                rbGroup.objects.link(refBrickUpper)
                rbGroup.objects.link(refBrickLower)
                rbGroup.objects.link(refBrickUpperLower)
        else:
            # make 1x1 refBrick
            m0 = Bricks.new_mesh(name="LEGOizer_%(n)s_refBrickHidden" % locals(), height=dimensions["height"], type=[1,1], undersideDetail=cm.hiddenUndersideDetail, logo=refLogoHidden)
            refBrickHidden = bpy.data.objects.new(m0.name, m0)
            m1 = Bricks().new_mesh(name="LEGOizer_%(n)s_refBrickUpper" % locals(), height=dimensions["height"], type=[1,1], undersideDetail=cm.hiddenUndersideDetail, logo=refLogoExposed)
            refBrickUpper = bpy.data.objects.new(m1.name, m1)
            m2 = Bricks().new_mesh(name="LEGOizer_%(n)s_refBrickLower" % locals(), height=dimensions["height"], type=[1,1], undersideDetail=cm.exposedUndersideDetail, logo=refLogoHidden)
            refBrickLower = bpy.data.objects.new(m2.name, m2)
            m3 = Bricks().new_mesh(name="LEGOizer_%(n)s_refBrickUpperLower" % locals(), height=dimensions["height"], type=[1,1], undersideDetail=cm.exposedUndersideDetail, logo=refLogoExposed)
            refBrickUpperLower = bpy.data.objects.new(m3.name, m3)
            # create new refbricks group
            if groupExists("LEGOizer_%(n)s_refBricks" % locals()):
                rbGroup = bpy.data.groups["LEGOizer_%(n)s_refBricks" % locals()]
            else:
                rbGroup = bpy.data.groups.new("LEGOizer_%(n)s_refBricks" % locals())
            # link refBricks to new group
            rbGroup.objects.link(refBrickHidden)
            rbGroup.objects.link(refBrickUpper)
            rbGroup.objects.link(refBrickLower)
            rbGroup.objects.link(refBrickUpperLower)

        if self.action == "CREATE":
            # hide all bricks in scene
            if not groupExists("LEGOizer_hidden"):
                hGroup = bpy.data.groups.new("LEGOizer_hidden")
            else:
                hGroup = bpy.data.groups["LEGOizer_hidden"]
            selectAll()
            for o in bpy.context.selected_objects:
                hGroup.objects.link(o)
            hide(bpy.context.selected_objects)

        # check last source data and transformation
        try:
            lastSourceDataRef = bpy.data.objects["LEGOizer_%(n)s_lastSourceDataRef" % locals()]
            identicalTransforms = lastSourceDataRef.matrix_world == source.matrix_world
            meshComparasin = source.data.unit_test_compare(lastSourceDataRef.data)
        except:
            meshComparasin = 'Error'
            identicalTransforms = False

        # if any related source data or settings have changed
        if cm.brickHeight != cm.lastBrickHeight or cm.gap != cm.lastGap or cm.preHollow != cm.lastPreHollow or cm.shellThickness != cm.lastShellThickness or meshComparasin != 'Same' or not identicalTransforms or cm.lastCalculationAxes != cm.calculationAxes or cm.lastLogoDetail != cm.logoDetail:
            # delete old bricks if present
            if groupExists(LEGOizer_bricks):
                bricks = list(bpy.data.groups[LEGOizer_bricks].objects)
                delete(bricks)
            # create new bricks
            R = (dimensions["width"]+dimensions["gap"], dimensions["width"]+dimensions["gap"], dimensions["height"]+dimensions["gap"])
            # slicesDict = [{"slices":CS_slices, "axis":axis, "R":R, "lScale":lScale}]
            refBricks = list(rbGroup.objects)
            makeBricks(refBricks, source, source_details, dimensions, R, cm.preHollow)

        # set final variables
        cm.lastBrickHeight = cm.brickHeight
        cm.lastGap = cm.gap
        cm.lastPreHollow = cm.preHollow
        cm.lastShellThickness = cm.shellThickness
        cm.lastCalculationAxes = cm.calculationAxes
        # cm.lastLogoResolution = cm.logoResolution
        cm.lastLogoDetail = cm.logoDetail
        cm.changesToCommit = True

        # store last source data
        try:
            o = bpy.data.objects["LEGOizer_%(n)s_lastSourceDataRef" % locals()]
            o.data = source.data.copy()
        except:
            o = bpy.data.objects.new("LEGOizer_%(n)s_lastSourceDataRef" % locals(), source.data.copy())
        o.matrix_world = source.matrix_world

        # STOPWATCH CHECK
        stopWatch("Time Elapsed", time.time()-startTime)

        if self.action == "CREATE":
            context.window_manager.modal_handler_add(self)
            return{"RUNNING_MODAL"}
        else:
            return{"FINISHED"}
