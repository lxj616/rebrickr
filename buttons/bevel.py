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

# Addon imports
from ..functions import *


class BrickerBevel(bpy.types.Operator):
    """Execute bevel modifier to all bricks with above settings"""
    bl_idname = "bricker.bevel"
    bl_label = "Bevel Bricks"
    bl_options = {"REGISTER", "UNDO"}

    ################################################
    # Blender Operator methods

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

    def execute(self, context):
        try:
            cm = getActiveContextInfo()[1]
            # set bevel action to add or remove
            action = "REMOVE" if cm.bevelAdded else "ADD"
            # get bricks to bevel
            bricks = getBricks()
            # create or remove bevel
            BrickerBevel.runBevelAction(bricks, cm, action, setBevel=True)
        except:
            handle_exception()
        return{"FINISHED"}

    #############################################
    # class methods

    @staticmethod
    def runBevelAction(bricks, cm, action="ADD", setBevel=False):
        """ chooses whether to add or remove bevel """
        if cm.bevelWidth == -1 or setBevel:
            # auto-set bevel width
            cm.bevelWidth = cm.brickHeight/100
        if action == "REMOVE":
            BrickerBevel.removeBevelMods(bricks)
            cm.bevelAdded = False
        elif action == "ADD":
            BrickerBevel.createBevelMods(cm, bricks)
            cm.bevelAdded = True

    @classmethod
    def removeBevelMods(self, objs):
        """ removes bevel modifier 'obj.name + "_bvl"' for objects in 'objs' """
        objs = confirmList(objs)
        for obj in objs:
            obj.modifiers.remove(obj.modifiers[obj.name + "_bvl"])

    @classmethod
    def createBevelMods(self, cm, objs):
        """ runs 'createBevelMod' on objects in 'objs' """
        # get objs to bevel
        objs = confirmList(objs)
        # create bevel modifiers for each object
        for obj in objs:
            segments = cm.bevelSegments
            profile = cm.bevelProfile
            vGroupName = obj.name + "_bvl"
            self.createBevelMod(obj=obj, width=cm.bevelWidth, segments=segments, profile=profile, limitMethod="VGROUP", vertexGroup=vGroupName, offsetType='WIDTH', angleLimit=1.55334)

    @classmethod
    def createBevelMod(self, obj, width=1, segments=1, profile=0.5, onlyVerts=False, limitMethod='NONE', angleLimit=0.523599, vertexGroup=None, offsetType='OFFSET'):
        """ create bevel modifier for 'obj' with given parameters """
        dMod = obj.modifiers.get(obj.name + '_bvl')
        if not dMod:
            dMod = obj.modifiers.new(obj.name + '_bvl', 'BEVEL')
            eMod = obj.modifiers.get('Edge Split')
            if eMod:
                obj.modifiers.remove(eMod)
                obj.modifiers.new('Edge Split', 'EDGE_SPLIT')
        # only update values if necessary (prevents multiple updates to mesh)
        if dMod.use_only_vertices != onlyVerts:
            dMod.use_only_vertices = onlyVerts
        if dMod.width != width:
            dMod.width = width
        if dMod.segments != segments:
            dMod.segments = segments
        if dMod.profile != profile:
            dMod.profile = profile
        if dMod.limit_method != limitMethod:
            dMod.limit_method = limitMethod
        if vertexGroup and dMod.vertex_group != vertexGroup:
            try:
                dMod.vertex_group = vertexGroup
            except Exception as e:
                print("[Bricker]", e)
                dMod.limit_method = "ANGLE"
        if dMod.angle_limit != angleLimit:
            dMod.angle_limit = angleLimit
        if dMod.offset_type != offsetType:
            dMod.offset_type = offsetType

    #############################################
