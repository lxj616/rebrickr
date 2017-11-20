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

# Rebrickr imports
from ..lib.caches import *
from ..functions.common import *

class clearCache(bpy.types.Operator):
    """Clear brick mesh and matrix cache (Brick Mods will be lost)"""           # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "rebrickr.clear_cache"                                          # unique identifier for buttons and menu items to reference.
    bl_label = "Clear Cache"                                                    # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            scn = context.scene

            # clear light caches
            for key in rebrickr_bm_cache:
                rebrickr_bm_cache[key] = None
            for key in rebrickr_bfm_cache:
                rebrickr_bfm_cache[key] = None
                cm = getItemByID(scn.cmlist, key)
                cm.matrixIsDirty = True

            # clear deep matrix caches
            for cm in scn.cmlist:
                cm.BFMCache = ""

        except:
            handle_exception()

        return{"FINISHED"}
