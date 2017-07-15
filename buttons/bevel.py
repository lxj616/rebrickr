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

def createBevelMod(obj, width=1, segments=1, profile=0.5, onlyVerts=False, limitMethod='NONE', angleLimit=0.523599, vertexGroup=None, offsetType='OFFSET'):
    dMod = obj.modifiers.get(obj.name + '_bevel')
    if not dMod:
        dMod = obj.modifiers.new(obj.name + '_bevel', 'BEVEL')
    dMod.use_only_vertices = onlyVerts
    dMod.width = width
    dMod.segments = segments
    dMod.profile = profile
    dMod.limit_method = limitMethod
    dMod.angle_limit = angleLimit
    dMod.offset_type = offsetType

def removeBevelMods(objs):
    objs = confirmList(objs)
    for obj in objs:
        obj.modifiers.remove(obj.modifiers[obj.name + "_bevel"])

class legoizerBevel(bpy.types.Operator):
    """Add a bevel modifier to all bricks with the following settings"""        # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "scene.legoizer_bevel"                                          # unique identifier for buttons and menu items to reference.
    bl_label = "Bevel Bricks"                                                   # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns false) """
        scn = context.scene
        try:
            cm = scn.cmlist[scn.cmlist_index]
            n = cm.source_name
            if groupExists("LEGOizer_%(n)s_bricks" % locals()):
                return True
        except:
            return False
        return False

    action = bpy.props.EnumProperty(
        items=(
            ("CREATE", "Create", ""),
            ("UPDATE", "Update", ""),
            ("APPLY", "Apply", ""),
            ("REMOVE", "Remove", ""),
        ),
        default="CREATE"
    )

    @staticmethod
    def setBevelMods(bricks):
        bricks = confirmList(bricks)
        # get bricks to bevel
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        for brick in bricks:
            createBevelMod(obj=brick, width=cm.bevelWidth, segments=cm.bevelResolution, limitMethod="ANGLE", angleLimit=0.5236)

    def execute(self, context):
        # get bricks to bevel
        scn = context.scene
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        cm.bevelWidth = cm.brickHeight/100
        # cm.bevelResolution = round(cm.studVerts/10)
        bricks = list(bpy.data.groups["LEGOizer_%(n)s_bricks" % locals()].objects)

        if self.action == "REMOVE" or self.action == "APPLY":
            removeBevelMods(objs=bricks)
        else:
            legoizerBevel.setBevelMods(bricks)

        return{"FINISHED"}
