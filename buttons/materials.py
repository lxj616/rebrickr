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

# System imports
import time
import bmesh
import os
import math
import numpy as np

# Blender imports
import bpy
from mathutils import Matrix, Vector, Euler
props = bpy.props

# Addon imports
from ..functions import *
from .delete import BrickerDelete
from ..lib.abs_plastic_materials import getAbsPlasticMaterialNames


class BrickerApplyMaterial(bpy.types.Operator):
    """Apply specified material to all bricks """
    bl_idname = "bricker.apply_material"
    bl_label = "Apply Material"
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
        if not (cm.modelCreated or cm.animated):
            return False
        return True

    def execute(self, context):
        try:
            self.runApplyMaterial(context)
        except:
            handle_exception()
        return{"FINISHED"}

    ################################################
    # initialization method

    def __init__(self):
        self.setAction()

    #############################################
    # class methods

    def setAction(self):
        """ sets self.action """
        scn, cm, _ = getActiveContextInfo()
        if cm.materialType == "SOURCE":
            self.action = "INTERNAL"
        elif cm.materialType == "CUSTOM":
            self.action = "CUSTOM"
        elif cm.materialType == "RANDOM":
            self.action = "RANDOM"

    @timed_call('Total Time Elapsed')
    def runApplyMaterial(self, context):

        # set up variables
        scn, cm, _ = getActiveContextInfo()
        bricksDict, _ = getBricksDict(cm=cm)
        if bricksDict is None:
            self.report({"WARNING"}, "Materials could not be applied manually. Please run 'Update Model'")
            cm.matrixIsDirty = True
            return
        bricks = getBricks()
        zStep = getZStep(cm)
        cm.lastMaterialType = cm.materialType
        if self.action == "CUSTOM":
            matName = cm.materialName
        elif self.action == "INTERNAL":
            matName = cm.internalMatName
        elif self.action == "RANDOM":
            BrickerApplyMaterial.applyRandomMaterial(scn, cm, context, bricks, bricksDict)

        if self.action != "RANDOM":
            # get material from matName
            mat = bpy.data.materials.get(matName)
            if mat is None: self.report({"WARNING"}, "Specified material doesn't exist")

            for brick in bricks:
                if self.action == "CUSTOM" or (self.action == "INTERNAL" and not isOnShell(cm, bricksDict, brick.name.split("__")[-1], zStep=zStep, shellDepth=cm.matShellDepth) and cm.matShellDepth <= cm.lastMatShellDepth):
                    if len(brick.material_slots) == 0:
                        # Assign material to object data
                        brick.data.materials.append(mat)
                        brick.material_slots[0].link = 'OBJECT'
                    elif self.action == "CUSTOM" and len(brick.material_slots) > 1:
                        clearExistingMaterials(brick, from_idx=1)
                    # assign material to mat slot
                    brick.material_slots[0].material = mat
                # update bricksDict mat_name values for split models
                if cm.lastSplitModel:
                    bricksDict[brick.name.split("__")[-1]]["mat_name"] = matName
            # update bricksDict mat_name values for not split models
            if self.action == "CUSTOM" and not cm.lastSplitModel:
                for k in bricksDict.keys():
                    if bricksDict[k]["draw"] and bricksDict[k]["parent"] == "self":
                        bricksDict[k]["mat_name"] = matName

        tag_redraw_areas(["VIEW_3D", "PROPERTIES", "NODE_EDITOR"])
        cm.materialIsDirty = False
        cm.lastMatShellDepth = cm.matShellDepth

    @classmethod
    def applyRandomMaterial(self, scn, cm, context, bricks, bricksDict):
        # initialize list of brick materials
        brick_mats = []
        mats = bpy.data.materials.keys()
        matObj = getMatObject(cm, typ="RANDOM")
        for color in matObj.data.materials.keys():
            brick_mats.append(color)
        if len(brick_mats) == 0:
            return
        randS0 = np.random.RandomState(0)
        # if model is split, apply a random material to each brick
        for i, brick in enumerate(bricks):
            lastMatSlots = list(brick.material_slots.keys())

            if cm.lastSplitModel or len(lastMatSlots) == 0:
                # iterate seed and set random index
                randS0.seed(cm.randomMatSeed + i)
                randIdx = randS0.randint(0, len(brick_mats)) if len(brick_mats) > 1 else 0
                # Assign random material to object
                mat = bpy.data.materials.get(brick_mats[randIdx])
                if len(lastMatSlots) == 0:
                    addMaterial(brick, mat)
                else:
                    brick.material_slots[0].link = 'OBJECT'
                    brick.material_slots[0].material = mat
                if cm.lastSplitModel:
                    bricksDict[brick.name.split("__")[-1]]["mat_name"] = mat.name
            elif len(lastMatSlots) == len(brick_mats):
                brick_mats_dup = brick_mats.copy()
                for i in range(len(lastMatSlots)):
                    # iterate seed and set random index
                    randS0.seed(cm.randomMatSeed + i)
                    if len(brick_mats_dup) == 1:
                        randIdx = 0
                    else:
                        randIdx = randS0.randint(0, len(brick_mats_dup))
                    # Assign random material to object
                    matName = brick_mats_dup.pop(randIdx)
                    mat = bpy.data.materials.get(matName)
                    brick.material_slots[i].material = mat
