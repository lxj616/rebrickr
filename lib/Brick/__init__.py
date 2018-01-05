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
import bpy
import bmesh
import random
import time
import numpy as np

# Blender imports
from mathutils import Vector, Matrix

# Rebrickr imports
from .brick_mesh_generate import *
from ...functions.general import *
from ...functions.common import *

class Bricks:
    @staticmethod
    def new_mesh(dimensions, size=[1,1,3], logo=False, all_vars=False, logo_type=None, logo_details=None, logo_scale=None, logo_resolution=None, logo_inset=None, undersideDetail="Flat", stud=True, numStudVerts=None):
        """ create unlinked Brick at origin """

        bm = bmesh.new()

        brickBM = makeBrick(dimensions=dimensions, brickSize=size, numStudVerts=numStudVerts, detail=undersideDetail, stud=stud)
        if logo and stud:
            # get logo rotation angle based on size of brick
            rot_mult = 180
            rot_vars = 2
            rot_add = 0
            if size[0] == 1 and size[1] == 1:
                rot_mult = 90
                rot_vars = 4
            elif size[0] == 2 and size[1] > 2:
                rot_add = 90
            elif size[1] == 2 and size[0] > 2:
                pass
            elif size[0] == 2 and size[1] == 2:
                pass
            elif size[0] == 1:
                rot_add = 90
            # set zRot to random rotation angle
            if all_vars:
                zRots = []
                for i in range(rot_vars):
                    zRots.append(i * rot_mult + rot_add)
            else:
                randomSeed = int(time.time()*10**6) % 10000
                randS0 = np.random.RandomState(randomSeed)
                zRots = [randS0.randint(0,rot_vars) * rot_mult + rot_add]
            lw = dimensions["logo_width"] * logo_scale
            logoBM_ref = bmesh.new()
            logoBM_ref.from_mesh(logo.data)
            if logo_type == "LEGO Logo":
                # smooth faces
                for f in logoBM_ref.faces:
                    f.smooth = True
                # transform logo into place
                bmesh.ops.scale(logoBM_ref, vec=Vector((lw, lw, lw)), verts=logoBM_ref.verts)
                bmesh.ops.rotate(logoBM_ref, verts=logoBM_ref.verts, cent=(1.0, 0.0, 0.0), matrix=Matrix.Rotation(math.radians(90.0), 3, 'X'))
            else:
                # transform logo to origin (transform was (or should be at least) applied, origin is at center)
                xOffset = logo_details.x.mid
                yOffset = logo_details.y.mid
                zOffset = logo_details.z.mid
                for v in logoBM_ref.verts:
                    v.co.x -= xOffset
                    v.co.y -= yOffset
                    v.co.z -= zOffset
                    v.select = True
                # scale logo
                distMax = max(logo_details.x.dist, logo_details.y.dist)
                bmesh.ops.scale(logoBM_ref, vec=Vector((lw/distMax, lw/distMax, lw/distMax)), verts=logoBM_ref.verts)

            bms = []
            for zRot in zRots:
                bm_cur = bm.copy()
                for x in range(size[0]):
                    for y in range(size[1]):
                        logoBM = logoBM_ref.copy()
                        # rotate logo around stud
                        if zRot != 0:
                            bmesh.ops.rotate(logoBM, verts=logoBM.verts, cent=(0.0, 0.0, 1.0), matrix=Matrix.Rotation(math.radians(zRot), 3, 'Z'))
                        # transform logo to appropriate position
                        zOffset = dimensions["logo_offset"]
                        if logo_type != "LEGO Logo" and logo_details is not None:
                            zOffset += ((logo_details.z.dist * (lw/distMax)) / 2) * (1-(logo_inset * 2))
                        xyOffset = dimensions["width"]+dimensions["gap"]
                        for v in logoBM.verts:
                            v.co = ((v.co.x + x*(xyOffset)), (v.co.y + y*(xyOffset)), (v.co.z + zOffset))
                        # add logoBM mesh to bm mesh
                        junkMesh = bpy.data.meshes.new('Rebrickr_junkMesh')
                        logoBM.to_mesh(junkMesh)
                        bm_cur.from_mesh(junkMesh)
                        bpy.data.meshes.remove(junkMesh, do_unlink=True)
                bms.append(bm_cur)
        else:
            bms = [bm]

        # add brick mesh to bm mesh
        junkMesh = bpy.data.meshes.new('Rebrickr_junkMesh')
        brickBM.to_mesh(junkMesh)
        for bm in bms:
            bm.from_mesh(junkMesh)
        bpy.data.meshes.remove(junkMesh, do_unlink=True)

        # return bmesh objects
        return bms

    @staticmethod
    def splitAll(bricksDict, keys=None, cm=None):
        if cm is None:
            scn, cm, _ = getActiveContextInfo()
        if keys is None:
            keys = list(bricksDict.keys())
        zStep = getZStep(cm)
        for key in keys:
            # set all bricks as unmerged
            if bricksDict[key]["draw"]:
                bricksDict[key]["parent_brick"] = "self"
                bricksDict[key]["size"] = [1, 1, zStep]

    def split(bricksDict, key, loc=None, cm=None, v=True, h=True):
        # set up unspecified paramaters
        if cm is None:
            scn, cm, _ = getActiveContextInfo()
        if loc is None:
            loc = strToList(key)
        # initialize vars
        size = bricksDict[key]["size"]
        newSize = [1, 1, size[2]]
        zStep = getZStep(cm)
        if cm.brickType == "Bricks and Plates":
            if not v:
                zStep = 3
            else:
                newSize[2] = 1
        if not h:
            newSize[0] = size[0]
            newSize[1] = size[1]
            size[0] = 1
            size[1] = 1
        splitKeys = []
        x,y,z = loc
        # split brick into individual bricks
        for x0 in range(x, x + size[0]):
            for y0 in range(y, y + size[1]):
                for z0 in range(z, z + size[2], zStep):
                    curKey = listToStr([x0,y0,z0])
                    bricksDict[curKey]["size"] = newSize
                    bricksDict[curKey]["parent_brick"] = "self"
                    bricksDict[curKey]["top_exposed"] = bricksDict[key]["top_exposed"]
                    bricksDict[curKey]["bot_exposed"] = bricksDict[key]["bot_exposed"]
                    # add curKey to list of split keys
                    splitKeys.append(curKey)
        return splitKeys

    @staticmethod
    def get_dimensions(height=1, zScale=1, gap_percentage=0.01):
        scale = height/9.6
        brick_dimensions = {}
        brick_dimensions["height"] = round(scale*9.6*zScale, 8)
        brick_dimensions["width"] = round(scale*8, 8)
        brick_dimensions["gap"] = round(scale*9.6*gap_percentage, 8)
        brick_dimensions["stud_height"] = round(scale*1.8, 8)
        brick_dimensions["stud_diameter"] = round(scale*4.8, 8)
        brick_dimensions["stud_radius"] = round(scale*2.4, 8)
        brick_dimensions["stud_offset"] = round((brick_dimensions["height"] / 2) + (brick_dimensions["stud_height"] / 2), 8)
        brick_dimensions["stud_offset_triple"] = round(((brick_dimensions["height"]*3) / 2) + (brick_dimensions["stud_height"] / 2), 8)
        brick_dimensions["thickness"] = round(scale*1.6, 8)
        brick_dimensions["tube_thickness"] = round(scale*0.855, 8)
        brick_dimensions["bar_radius"] = round(scale*1.6, 8)
        brick_dimensions["logo_width"] = round(scale*4.8, 8) # originally round(scale*3.74, 8)
        brick_dimensions["support_width"] = round(scale*0.8, 8)
        brick_dimensions["tick_width"] = round(scale*0.6, 8)
        brick_dimensions["tick_depth"] = round(scale*0.3, 8)
        brick_dimensions["support_height"] = round(brick_dimensions["height"]*0.65, 8)
        brick_dimensions["support_height_triple"] = round((brick_dimensions["height"]*3)*0.65, 8)

        brick_dimensions["logo_offset"] = round((brick_dimensions["height"] / 2) + (brick_dimensions["stud_height"]), 8)
        return brick_dimensions
