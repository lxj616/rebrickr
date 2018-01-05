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
import time
import bmesh
import os
import math

# Blender imports
import bpy
from mathutils import Matrix, Vector
props = bpy.props

# Rebrickr imports
from ..functions import *


def createBevelMod(obj, width=1, segments=1, profile=0.5, onlyVerts=False, limitMethod='NONE', angleLimit=0.523599, vertexGroup=None, offsetType='OFFSET'):
    """ create bevel modifier for 'obj' with given parameters """
    dMod = obj.modifiers.get(obj.name + '_bevel')
    if not dMod:
        dMod = obj.modifiers.new(obj.name + '_bevel', 'BEVEL')
        eMod = obj.modifiers.get('Edge Split')
        if eMod:
            obj.modifiers.remove(eMod)
            obj.modifiers.new('Edge Split', 'EDGE_SPLIT')
    dMod.use_only_vertices = onlyVerts
    dMod.width = width
    dMod.segments = segments
    dMod.profile = profile
    dMod.limit_method = limitMethod
    if vertexGroup:
        try:
            dMod.vertex_group = vertexGroup
        except Exception as e:
            print(e)
            dMod.limit_method = "ANGLE"
    dMod.angle_limit = angleLimit
    dMod.offset_type = offsetType


def createBevelMods(objs):
    """ runs 'createBevelMod' on objects in 'objs' """
    objs = confirmList(objs)
    scn, cm, _ = getActiveContextInfo()
    for obj in objs:
        segments = cm.bevelSegments
        profile = cm.bevelProfile
        vGroupName = obj.name + "_bevel"
        createBevelMod(obj=obj, width=cm.bevelWidth, segments=segments, profile=profile, limitMethod="VGROUP", vertexGroup=vGroupName, offsetType='WIDTH', angleLimit=1.55334)


def removeBevelMods(objs):
    """ removes bevel modifier 'obj.name + "_bevel"' for objects in 'objs' """
    objs = confirmList(objs)
    for obj in objs:
        obj.modifiers.remove(obj.modifiers[obj.name + "_bevel"])


class RebrickrBevel(bpy.types.Operator):
    """Execute bevel modifier to all bricks with above settings"""
    bl_idname = "rebrickr.bevel"
    bl_label = "Bevel Bricks"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns false) """
        scn = context.scene
        try:
            cm = scn.cmlist[scn.cmlist_index]
        except IndexError:
            return False
        n = cm.source_name
        if cm.modelCreated or cm.animated:
            return True
        return False

    @staticmethod
    def runBevelAction(bricks, cm, action="ADD"):
        if action == "REMOVE":
            removeBevelMods(objs=bricks)
            cm.bevelAdded = False
        elif action == "ADD":
            createBevelMods(objs=bricks)
            cm.bevelAdded = True

    def execute(self, context):
        try:
            scn, cm, n = getActiveContextInfo()

            # set bevel action to add or remove
            action = "REMOVE" if cm.bevelAdded else "ADD"

            # auto-set bevel width
            cm.bevelWidth = cm.brickHeight/100

            # get bricks to bevel
            bricks = getBricks()
            # create or remove bevel
            RebrickrBevel.runBevelAction(bricks, cm, action)
        except:
            handle_exception()
        return{"FINISHED"}
