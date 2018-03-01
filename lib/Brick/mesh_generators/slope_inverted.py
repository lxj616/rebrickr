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
from mathutils import Vector
from bpy.types import CollectionProperty

# Bricker imports
from .geometric_shapes import *


def makeInvertedSlope(dimensions:dict, brickSize:list, circleVerts:int=None, detail:str="LOW", stud:bool=True, cm:CollectionProperty=None, bme:bmesh=None):
    """
    create inverted slope brick with bmesh

    Keyword Arguments:
        dimensions  -- dictionary containing brick dimensions
        brickSize   -- size of brick (e.g. standard 2x4 -> [2, 4, 3])
        circleVerts -- number of vertices per circle of cylinders
        type        -- type of round 1x1 brick in ["CONE", "CYLINDER", "STUD", "STUD_HOLLOW"]
        detail      -- level of brick detail (options: ["FLAT", "LOW", "MEDIUM", "HIGH"])
        stud        -- create stud on top of brick
        cm          -- cmlist item of model
        bme         -- bmesh object in which to create verts

    """
    # create new bmesh object
    bme = bmesh.new() if not bme else bme
    cm = cm or getActiveContextInfo()[1]


    return bme
