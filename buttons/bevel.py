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
        except:
            dMod.limit_method = "ANGLE"
    dMod.angle_limit = angleLimit
    dMod.offset_type = offsetType

def setBevelMods(bricks):
    bricks = confirmList(bricks)
    # get bricks to bevel
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    n = cm.source_name
    for brick in bricks:
        segments = cm.bevelSegments
        profile = cm.bevelProfile
        if not cm.lastSplitModel:
            vGroupName = "Brickinator_%(n)s_bricks_combined_bevel" % locals()
        else:
            vGroupName = brick.name + "_bevel"
        createBevelMod(obj=brick, width=cm.bevelWidth, segments=segments, profile=profile, limitMethod="VGROUP", vertexGroup=vGroupName, offsetType='WIDTH', angleLimit=1.55334)

def removeBevelMods(objs):
    objs = confirmList(objs)
    for obj in objs:
        obj.modifiers.remove(obj.modifiers[obj.name + "_bevel"])

class BrickinatorBevel(bpy.types.Operator):
    """Execute bevel modifier to all bricks with above settings"""              # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "scene.brickinator_bevel"                                          # unique identifier for buttons and menu items to reference.
    bl_label = "Bevel Bricks"                                                   # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns false) """
        scn = context.scene
        try:
            cm = scn.cmlist[scn.cmlist_index]
            n = cm.source_name
            if cm.modelCreated or cm.animated:
                return True
        except:
            return False
        return False

    @staticmethod
    def runBevelAction(bGroup, cm, action="ADD"):
        if bGroup is not None:
            bricks = list(bGroup.objects)
            if action == "REMOVE":
                removeBevelMods(objs=bricks)
                cm.bevelAdded = False
            elif action == "ADD":
                setBevelMods(bricks)
                cm.bevelAdded = True

    def execute(self, context):
        try:
            # get bricks to bevel
            scn = context.scene
            cm = scn.cmlist[scn.cmlist_index]
            n = cm.source_name

            # set bevel action to add or remove
            if not cm.bevelAdded:
                action = "ADD"
            else:
                action = "REMOVE"

            # auto-set bevel width
            cm.bevelWidth = cm.brickHeight/100

            # create or remove bevel
            if cm.modelCreated:
                bGroup = bpy.data.groups.get("Brickinator_%(n)s_bricks" % locals())
                BrickinatorBevel.runBevelAction(bGroup, cm, action)
            elif cm.animated:
                for cf in range(cm.lastStartFrame, cm.lastStopFrame+1):
                    bGroup = bpy.data.groups.get("Brickinator_%(n)s_bricks_frame_%(cf)s" % locals())
                    BrickinatorBevel.runBevelAction(bGroup, cm, action)
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
