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
import math
import numpy as np

# Blender imports
from mathutils import Vector, Matrix

# Rebrickr imports
from .geometric_shapes import *
from .generator_utils import *


def makeSlope(dimensions:dict, brickSize:list, direction:str=None, circleVerts:int=None, detail:str="LOW", stud:bool=True, bme:bmesh=None):
    """
    create slope brick with bmesh

    NOTE: brick created with slope facing +X direction, then translated/rotated as necessary

    Keyword Arguments:
        dimensions  -- dictionary containing brick dimensions
        brickSize   -- size of brick (e.g. 2x3 slope -> [2, 3, 3])
        direction   -- direction slant faces in ["X+", "X-", "Y+", "Y-"]
        circleVerts -- number of vertices per circle of cylinders
        detail      -- level of brick detail (options: ["FLAT", "LOW", "MEDIUM", "HIGH"])
        stud        -- create stud on top of brick
        bme         -- bmesh object in which to create verts

    """
    # create new bmesh object
    bme = bmesh.new() if not bme else bme

    # set direction to longest side if None (defaults to X if sides are the same)
    maxIdx = brickSize.index(max(brickSize[:2]))
    directions = ["X+", "Y+", "X-", "Y-"]
    # default to "X+" if X is larger, "Y+" if Y is larger
    direction = directions[maxIdx] if direction is None else direction
    # verify direction is valid
    assert direction in directions

    # get halfScale
    _, cm, _ = getActiveContextInfo()
    bAndPBrick = "PLATES" in cm.brickType and brickSize[2] == 3
    height = dimensions["height"] * (3 if bAndPBrick else 1)
    d = Vector((dimensions["width"] / 2, dimensions["width"] / 2, height / 2))
    # get scalar for d in positive xyz directions
    adjustedBrickSize = (brickSize[:2] if "X" in direction else brickSize[1::-1]) + brickSize[2:]
    scalar = Vector((adjustedBrickSize[0] * 2 - 1,
                     adjustedBrickSize[1] * 2 - 1,
                     1))
    # get thickness of brick from inside to outside
    thick = Vector([dimensions["thickness"]] * 3)

    # make brick body cube
    coord1 = -d
    coord2 = vector_mult(d, [1, scalar.y, 1])
    v1, v2, d0, d1, v5, v6, v7, v8 = makeCube(coord1, coord2, [1, 1 if detail == "FLAT" else 0, 0, 0, 1, 1], bme=bme)
    # remove bottom verts on slope side
    bme.verts.remove(d0)
    bme.verts.remove(d1)
    # add face to opposite side from slope
    bme.faces.new((v1, v5, v8, v2))

    # create stud
    if stud: addStuds(dimensions, height, [1] + adjustedBrickSize[1:], "CONE", circleVerts, bme, inset=thick.z * 0.9)

    # make square at end of slope
    coord1 = vector_mult(d, [scalar.x, -1, -1])
    coord2 = vector_mult(d, [scalar.x, scalar.y, -1])
    coord2.z += thick.z
    v9, v10, v11, v12 = makeSquare(coord1, coord2, bme=bme)

    # connect square to body cube
    bme.faces.new((v2, v8,  v7, v11, v10))
    bme.faces.new((v9, v12, v6,  v5, v1))
    bme.faces.new((v12, v11, v7, v6))

    # add underside details
    if detail == "FLAT":
        bme.faces.new((v10, v9, v1, v2))
    else:
        # add inside square at end of slope
        coord1 = Vector(( d.x * scalar.x - thick.x,
                         -d.y + thick.y,
                         -d.z))
        coord2 = Vector(( d.x * scalar.x - thick.x,
                          d.y * scalar.y - thick.y,
                         -d.z + thick.z))
        v13, v14, v15, v16 = makeSquare(coord1, coord2, flipNormal=True, bme=bme)
        # add verts next to inside square at end of slope
        if adjustedBrickSize[0] in [3, 4]:
            x = d.x * scalar.x + (thick.x * (adjustedBrickSize[0] - 3))
            x -= (dimensions["tube_thickness"] + dimensions["stud_radius"]) * (adjustedBrickSize[0] - 2)
            v17 = bme.verts.new((x, coord1.y, coord2.z))
            v18 = bme.verts.new((x, coord2.y, coord2.z))
            bme.faces.new((v17, v18, v15, v16))
        else:
            v17 = v16
            v18 = v15
        # add inside verts cube at deepest section
        coord1 = -d
        coord1.xy += thick.xy
        coord2 = vector_mult(d, [1, scalar.y, 1])
        coord2.yz -= thick.yz
        v19, v20, d0, d1, v23, v24, v25, v26 = makeCube(coord1, coord2, [1 if detail != "HIGH" else 0, 1, 0, 1, 0, 0], flipNormals=True, bme=bme)
        # remove bottom verts on slope side
        bme.verts.remove(d0)
        bme.verts.remove(d1)
        # connect side faces from verts created above
        bme.faces.new((v18, v25, v26, v20))
        bme.faces.new((v19, v23, v24, v17))
        if adjustedBrickSize[0] in [3, 4]:
            bme.faces.new((v14, v15, v18, v20))
            bme.faces.new((v16, v13,  v19, v17))
        else:
            bme.faces.new((v14, v18, v20))
            bme.faces.new((v13,  v19, v17))
        # connect face for inner slope
        bme.faces.new((v24, v25, v18, v17))

        # connect inner and outer verts
        bme.faces.new((v13, v14, v10, v9))
        bme.faces.new((v10, v14, v20, v2))
        bme.faces.new((v1, v2, v20, v19))
        bme.faces.new((v13, v9, v1, v19))

        # add supports
        if detail in ["MEDIUM", "HIGH"]:
            # add bars
            if min(brickSize) == 1:
                addBars(dimensions, height, adjustedBrickSize, circleVerts, "SLOPE", detail, d, scalar, thick, bme)
            # add tubes
            else:
                addTubeSupports(dimensions, height, adjustedBrickSize, circleVerts, "SLOPE", detail, d, scalar, thick, bme)
        # add inner cylinders
        if detail == "HIGH":
            addInnerCylinders(dimensions, [1] + adjustedBrickSize[1:], circleVerts, d, v23, v24, v25, v26, bme)


    # # translate slope to adjust for flipped brick
    for v in bme.verts:
        v.co.y -= d.y * (scalar.y - 1) if direction in ["X-", "Y+"] else 0
        v.co.x -= d.x * (scalar.x - 1) if direction in ["X-", "Y-"] else 0
    # rotate slope to the appropriate orientation
    mult = directions.index(direction)
    bmesh.ops.rotate(bme, verts=bme.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90) * mult, 3, 'Z'))

    return bme
