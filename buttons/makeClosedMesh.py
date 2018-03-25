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
# import time
# import bmesh
# import os
# import math
# from mathutils import Matrix, Vector, Euler
import subprocess
import webbrowser
import sys

# Blender imports
import bpy
from addon_utils import check, paths, enable
props = bpy.props

# Bricker imports
from ..functions import *


class MakeClosedMesh(bpy.types.Operator):
    """Make source into single closed mesh (may take a while)"""
    bl_idname = "bricker.make_closed_mesh"
    bl_label = "Make Closed Mesh"
    bl_options = {"REGISTER", "UNDO"}

    # @classmethod
    # def poll(self, context):
    #     """ ensures operator can execute (if not, returns false) """
    #     addon = 'object_boolean_tools'
    #     is_enabled, is_loaded = check(addon)
    #     if not is_enabled:
    #         return False
    #     return True

    def execute(self, context):
        try:
            scn, cm, _ = getActiveContextInfo()
            source = bpy.data.objects.get(cm.source_name)

            # separate source by loose parts
            setActiveObj(source)
            bpy.ops.mesh.separate(type='LOOSE')

            separatedObjs = bpy.context.selected_objects

            obj = separatedObjs[0]
            for i in range(1, len(separatedObjs)):
                bMod = obj.modifiers.new('Bricker_Boolean', type='BOOLEAN')
                bMod.object = separatedObjs[i]
                bMod.operation = 'UNION'
                setActiveObj(obj)
                bpy.ops.object.modifier_apply(apply_as='DATA', modifier='Bricker_Boolean')
                obj = scn.objects.active
                delete(separatedObjs[i])

            scn.objects.active.name = cm.source_name
        except:
            handle_exception()
        return{"FINISHED"}
