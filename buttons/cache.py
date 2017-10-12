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
from ..lib.rebrickr_caches import rebrickr_bm_cache


class clearCache(bpy.types.Operator):
    """Clear cache of brick meshes and matrices (try if you're experiencing slow UI or odd addon behaviors)""" # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "scene.rebrickr_clear_cache"                                   # unique identifier for buttons and menu items to reference.
    bl_label = "Clear Cache"                                                   # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            scn = context.scene

            # clear rebrickr_bm_cache
            rebrickr_bm_cache = {}

            # clear matrix caches
            for cm in scn.cmlist:
                cm.BFMCache = ""

        except:
            self.handle_exception()

        return{"FINISHED"}

    def handle_exception(self):
        errormsg = print_exception('Rebrickr_log')
        # if max number of exceptions occur within threshold of time, abort!
        print('\n'*5)
        print('-'*100)
        print("Something went wrong. Please start an error report with us so we can fix it! (press the 'Report a Bug' button under the 'Brick Models' dropdown menu of the Rebrickr)")
        print('-'*100)
        print('\n'*5)
        showErrorMessage("Something went wrong. Please start an error report with us so we can fix it! (press the 'Report a Bug' button under the 'Brick Models' dropdown menu of the Rebrickr)", wrap=240)
