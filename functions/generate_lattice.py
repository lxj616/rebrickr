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

# Blender imports
import bpy
from mathutils import Vector

# Rebrickr imports
from .common import drawBMesh


def generateLattice(vertDist:Vector, scale:Vector, offset:Vector=(0, 0, 0)):
    """ return lattice coordinate matrix surrounding object of size 'scale'

    Keyword arguments:
    vertDist -- distance between lattice verts in 3D space
    scale    -- lattice scale in 3D space
    offset   -- offset lattice center from origin

    """

    # create bmesh for visualizing the lattice coordinates
    bme = bmesh.new()
    # shift offset to ensure lattice surrounds object
    offset = offset - (vertDist / 2)
    # calculate res of lattice
    res = Vector((round(scale.x / vertDist.x),
                  round(scale.y / vertDist.y),
                  round(scale.z / vertDist.z)))
    # populate coord matrix
    nx, ny, nz = int(res.x) + 2, int(res.y) + 2, int(res.z) + 2
    coordMatrix = [[[Vector((((x - res.x / 2) * vertDist.x),
                             ((y - res.y / 2) * vertDist.y),
                             ((z - res.z / 2) * vertDist.z))) + offset
                       for z in range(nz)
                    ] for y in range(ny)
                   ] for x in range(nx)
                  ]
    # create bmesh vertex for each coordinate
    for x in range(len(coordMatrix)):
        for y in range(len(coordMatrix[0])):
            for z in range(len(coordMatrix[0][0])):
                bme.verts.new(coordMatrix[x][y][z])
    # draw bmesh object with vertices at coordinate locations
    drawBMesh(bme)
    return coordMatrix
