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
import os

# Blender imports
import bpy
props = bpy.props

# Bricker imports
from .customize.undo_stack import *
from ..lib.caches import *
from ..functions.common import *


class Caches(bpy.types.Operator):
    """Clear brick mesh and matrix cache (Model customizations will be lost)"""
    bl_idname = "rebrickr.clear_cache"
    bl_label = "Clear Cache"
    bl_options = {"REGISTER", "UNDO"}

    ################################################
    # Blender Operator methods

    @classmethod
    def poll(self, context):
        if not bpy.props.rebrickr_initialized:
            return False
        return True

    def execute(self, context):
        try:
            if self.clearAll:
                self.clearCaches()
                scn, cm, _ = getActiveContextInfo()
                self.undo_stack.iterateStates(cm)
                cm.matrixIsDirty = True
        except:
            handle_exception()

        return{"FINISHED"}

    ################################################
    # initialization method

    def __init__(self):
        self.undo_stack = UndoStack.get_instance()
        self.undo_stack.undo_push('clear_cache')

    ###################################################
    # class variables

    clearAll = bpy.props.BoolProperty(
        name="Clear Caches",
        description="Clear all caches stored for current file",
        default=False)

    #############################################
    # class methods

    @staticmethod
    def clearCache(cm, brick_mesh=True, light_matrix=True, deep_matrix=True):
        """clear caches for cmlist item"""
        # clear light brick mesh cache
        if brick_mesh:
            rebrickr_bm_cache[cm.id] = None
        # clear light matrix cache
        if light_matrix:
            rebrickr_bfm_cache[cm.id] = None
        # clear deep matrix cache
        if deep_matrix:
            cm.BFMCache = ""

    @staticmethod
    def clearCaches(brick_mesh=True, light_matrix=True, deep_matrix=True):
        """clear all caches in cmlist"""
        scn = bpy.context.scene
        for cm in scn.cmlist:
            clearCache(cm, brick_mesh=brick_mesh, light_matrix=light_matrix, deep_matrix=deep_matrix)

    @staticmethod
    def cacheExists(cm=None):
        """check if light or deep matrix cache exists for cmlist item"""
        cm = cm or getActiveContextInfo()[1]
        return rebrickr_bfm_cache.get(cm.id) is not None or cm.BFMCache != ""
