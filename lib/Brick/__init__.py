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

# Bricker imports
from .mesh_generators import *
from .get_brick_dimensions import *
from ...functions.general import *
from ...functions.common import *

class Bricks:
    @staticmethod
    def new_mesh(dimensions:list, size:list=[1,1,3], type:str="BRICK", flip:bool=False, rotate90:bool=False, logo=False, all_vars=False, logo_type=None, logo_details=None, logo_scale=None, logo_inset=None, undersideDetail:str="FLAT", stud:bool=True, circleVerts:int=16, cm=None):
        """ create unlinked Brick at origin """
        cm = cm or getActiveContextInfo()[1]

        # create brick mesh
        if type in ["BRICK", "PLATE", "CUSTOM"]:
            brickBM = makeStandardBrick(dimensions=dimensions, brickSize=size, type=type, circleVerts=circleVerts, detail=undersideDetail, stud=stud, cm=cm)
        elif type in ["CYLINDER", "CONE", "STUD", "STUD_HOLLOW"]:
            brickBM = makeRound1x1(dimensions=dimensions, circleVerts=circleVerts, type=type, detail=undersideDetail, cm=cm)
        elif type in ["TILE", "TILE_GRILL"]:
            brickBM = makeTile(dimensions=dimensions, brickSize=size, circleVerts=circleVerts, type=type, detail=undersideDetail, cm=cm)
        elif type in ["SLOPE", "TALL_SLOPE"]:
            # determine brick direction
            directions = ["X+", "Y+", "X-", "Y-"]
            maxIdx = size.index(max(size[:2]))
            maxIdx -= 2 if flip else 0
            maxIdx += 1 if rotate90 else 0
            # make slope brick bmesh
            brickBM = makeSlope(dimensions=dimensions, brickSize=size, circleVerts=circleVerts, direction=directions[maxIdx], detail=undersideDetail, stud=stud, cm=cm)
        else:
            raise ValueError("'new_mesh' function received unrecognized value for parameter 'type': '" + str(type) + "'")

        # create list of brick bmesh variations
        if logo and stud and type in ["BRICK", "PLATE", "STUD", "SLOPE"]:
            bms = makeLogoVariations(dimensions, size, directions[maxIdx] if type == "SLOPE" else "", all_vars, logo, logo_type, logo_details, logo_scale, logo_inset)
        else:
            bms = [bmesh.new()]

        # add brick mesh to bm mesh
        junkMesh = bpy.data.meshes.new('Bricker_junkMesh')
        brickBM.to_mesh(junkMesh)
        for bm in bms:
            bm.from_mesh(junkMesh)
        bpy.data.meshes.remove(junkMesh, do_unlink=True)

        # return bmesh objects
        return bms

    @staticmethod
    def splitAll(bricksDict, keys=None, cm=None):
        cm = cm or getActiveContextInfo()[1]
        keys = keys or list(bricksDict.keys())
        for key in keys:
            # set all bricks as unmerged
            if bricksDict[key]["draw"]:
                bricksDict[key]["parent_brick"] = "self"
                bricksDict[key]["size"] = [1, 1, getZStep(cm)]

    def split(bricksDict, key, loc=None, cm=None, v=True, h=True):
        """split brick vertically and/or horizontally

        Keyword Arguments:
        bricksDict -- Matrix of bricks in model
        key        -- key for brick in matrix
        loc        -- xyz location of brick in matrix
        cm         -- cmlist item of model
        v          -- split brick vertically
        h          -- split brick horizontally
        """
        # set up unspecified paramaters
        cm = cm or getActiveContextInfo()[1]
        loc = loc or strToList(key)
        # initialize vars
        size = bricksDict[key]["size"]
        newSize = [1, 1, size[2]]
        zStep = getZStep(cm)
        if "PLATES" in cm.brickType:
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
                    bricksDict[curKey]["type"] = "BRICK" if newSize[2] == 3 else "PLATE"
                    bricksDict[curKey]["parent_brick"] = "self"
                    bricksDict[curKey]["top_exposed"] = bricksDict[key]["top_exposed"]
                    bricksDict[curKey]["bot_exposed"] = bricksDict[key]["bot_exposed"]
                    # add curKey to list of split keys
                    splitKeys.append(curKey)
        return splitKeys

    @staticmethod
    def get_dimensions(height=1, zScale=1, gap_percentage=0.01):
        return get_brick_dimensions(height, zScale, gap_percentage)

def makeLogoVariations(dimensions, size, direction, all_vars, logo, logo_type, logo_details, logo_scale, logo_inset):
    cm = getActiveContextInfo()[1]
    # get logo rotation angle based on size of brick
    rot_mult = 180
    rot_vars = 2
    rot_add = 0
    if direction != "":
        directions = ["X+", "Y+", "X-", "Y-"]
        rot_add = 90 * (directions.index(direction) + 1)
        rot_vars = 1
    elif size[0] == 1 and size[1] == 1:
        rot_mult = 90
        rot_vars = 4
    elif size[0] == 2 and size[1] > 2:
        rot_add = 90
    elif ((size[1] == 2 and size[0] > 2) or
          (size[0] == 2 and size[1] == 2)):
        pass
    elif size[0] == 1:
        rot_add = 90
    # set zRot to random rotation angle
    if all_vars:
        zRots = [i * rot_mult + rot_add for i in range(rot_vars)]
    else:
        randomSeed = int(time.time()*10**6) % 10000
        randS0 = np.random.RandomState(randomSeed)
        zRots = [randS0.randint(0,rot_vars) * rot_mult + rot_add]
    lw = dimensions["logo_width"] * logo_scale
    logoBM_ref = bmesh.new()
    logoBM_ref.from_mesh(logo.data)
    if logo_type == "LEGO":
        smoothFaces(list(logoBM_ref.faces))
        # transform logo into place
        bmesh.ops.scale(logoBM_ref, vec=Vector((lw, lw, lw)), verts=logoBM_ref.verts)
        bmesh.ops.rotate(logoBM_ref, verts=logoBM_ref.verts, cent=(1.0, 0.0, 0.0), matrix=Matrix.Rotation(math.radians(90.0), 3, 'X'))
    else:
        # transform logo to origin (transform was (or should be at least) applied, origin is at center)
        for v in logoBM_ref.verts:
            v.co -= Vector((logo_details.x.mid, logo_details.y.mid, logo_details.z.mid))
            v.select = True
        # scale logo
        distMax = max(logo_details.x.dist, logo_details.y.dist)
        bmesh.ops.scale(logoBM_ref, vec=Vector((lw/distMax, lw/distMax, lw/distMax)), verts=logoBM_ref.verts)

    # create new bmeshes for each logo variation
    bms = [bmesh.new() for zRot in zRots]
    # cap x/y ranges so logos aren't created over slopes
    xR0 = size[0] - 1 if direction == "X-" else 0
    yR0 = size[1] - 1 if direction == "Y-" else 0
    xR1 = 1 if direction == "X+" else size[0]
    yR1 = 1 if direction == "Y+" else size[1]
    # add logos on top of each stud
    for i,zRot in enumerate(zRots):
        for x in range(xR0, xR1):
            for y in range(yR0, yR1):
                logoBM = logoBM_ref.copy()
                # rotate logo around stud
                if zRot != 0:
                    bmesh.ops.rotate(logoBM, verts=logoBM.verts, cent=(0.0, 0.0, 1.0), matrix=Matrix.Rotation(math.radians(zRot), 3, 'Z'))
                # transform logo to appropriate position
                zOffset = dimensions["logo_offset"] + (dimensions["height"] if "PLATES" in cm.brickType and size[2] == 3 else 0)
                if logo_type != "LEGO" and logo_details is not None:
                    zOffset += ((logo_details.z.dist * (lw / distMax)) / 2) * (1 - logo_inset * 2)
                xyOffset = dimensions["width"] + dimensions["gap"]
                for v in logoBM.verts:
                    v.co += Vector((x * xyOffset, y * xyOffset, zOffset))
                # add logoBM mesh to bm mesh
                junkMesh = bpy.data.meshes.new('Bricker_junkMesh')
                logoBM.to_mesh(junkMesh)
                bms[i].from_mesh(junkMesh)
                bpy.data.meshes.remove(junkMesh, do_unlink=True)
    return bms
