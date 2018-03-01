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
import bmesh
import math

# Blender imports
import bpy
from mathutils import Vector

# Bricker imports
from .common import *


def generateLattice(vertDist:Vector, scale:Vector, offset:Vector=(0, 0, 0), visualize:bool=False):
    """ return lattice coordinate matrix surrounding object of size 'scale'

    Keyword arguments:
    vertDist  -- distance between lattice verts in 3D space
    scale     -- lattice scale in 3D space
    offset    -- offset lattice center from origin
    visualize -- draw lattice coordinates in 3D space

    """

    # shift offset to ensure lattice surrounds object
    offset = offset - vec_remainder(offset, vertDist)
    # calculate res of lattice
    res = Vector((round(scale.x / vertDist.x),
                  round(scale.y / vertDist.y),
                  round(scale.z / vertDist.z)))
    # populate coord matrix
    res = Vector(round_up(v, 2) for v in res)
    nx, ny, nz = int(res.x) + 2, int(res.y) + 2, int(res.z) + 2
    create_coord = lambda v: vec_mult(v - res / 2, vertDist) + offset
    coordMatrix = [[[create_coord(Vector((x, y, z))) for z in range(nz)] for y in range(ny)] for x in range(nx)]

    if visualize:
        # create bmesh
        bme = bmesh.new()
        # add vertex for each coordinate
        for x in range(len(coordMatrix)):
            for y in range(len(coordMatrix[0])):
                for z in range(len(coordMatrix[0][0])):
                    bme.verts.new(coordMatrix[x][y][z])
        # draw bmesh verts in 3D space
        drawBMesh(bme)

    return coordMatrix
