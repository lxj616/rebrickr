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
from .delete import BrickinatorDelete
from mathutils import Matrix, Vector, Euler
props = bpy.props

class BrickinatorApplyMaterial(bpy.types.Operator):
    """Apply specified material to all bricks """                        # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "scene.brickinator_apply_material"                                 # unique identifier for buttons and menu items to reference.
    bl_label = "Apply Material"                                         # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns false) """
        scn = bpy.context.scene
        if scn.cmlist_index == -1:
            return False
        cm = scn.cmlist[scn.cmlist_index]
        if not (cm.modelCreated or cm.animated):
            return False
        return True

    def setAction(self):
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        if cm.materialType == "Use Source Materials":
            self.action = "INTERNAL"
        elif cm.materialType == "Custom":
            self.action = "CUSTOM"
        elif cm.materialType == "Random":
            self.action = "RANDOM"

    def execute(self, context):
        try:
            # get start time
            startTime = time.time()

            self.setAction()

            # set up variables
            scn = bpy.context.scene
            cm = scn.cmlist[scn.cmlist_index]
            n = cm.source_name
            Brickinator_bricks_gn = "Brickinator_%(n)s_bricks" % locals()
            bricks = list(bpy.data.groups[Brickinator_bricks_gn].objects)
            if self.action == "CUSTOM":
                matName = cm.materialName
            elif self.action == "INTERNAL":
                matName = cm.internalMatName
            mat = bpy.data.materials.get(matName)
            if mat is None:
                self.report({"WARNING"}, "Specified material doesn't exist")

            for brick in bricks:
                # if materials exist, remove them
                if brick.data.materials:
                    if self.action == "CUSTOM":
                        brick.data.materials.clear(1)
                        # Assign it to object
                        brick.data.materials.append(mat)
                    elif self.action == "INTERNAL":
                        brick.data.materials.pop(0)
                        # Assign it to object
                        brick.data.materials.append(mat)
                        for i in range(len(brick.data.materials)-1):
                            brick.data.materials.append(brick.data.materials.pop(0))

            cm.materialIsDirty = False

            # STOPWATCH CHECK
            stopWatch("Total Time Elapsed", time.time()-startTime)
        except:
            self.handle_exception()

        return{"FINISHED"}

    def handle_exception(self):
        errormsg = print_exception('Brickinator_log')
        # if max number of exceptions occur within threshold of time, abort!
        curtime = time.time()
        print('\n'*5)
        print('-'*100)
        print("Something went wrong. Please start an error report with us so we can fix it! (press the 'Report a Bug' button under the 'Brick Models' dropdown menu of the Brickinator)")
        print('-'*100)
        print('\n'*5)
        showErrorMessage("Something went wrong. Please start an error report with us so we can fix it! (press the 'Report a Bug' button under the 'Brick Models' dropdown menu of the Brickinator)", wrap=240)
