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
import os
import numpy as np
import colorsys

# Blender imports
import bpy

# Addon imports
from .general import *
from ..lib.bricksDict.generate import *


def getLDRBrickInfo(line):
    if line[0] == 0:
        return None
    elif line[0] == 0:
        vals = line.split(" ")
        #TODO: get size of brick
        size = ???
        #TODO: move loc to furthest negative based on size of brick
        loc = Vector(int(vals[2]) / 100, int(vals[4]) / 100, -int(vals[4]) / 100)
        color = vals[5:14]
        typ = vals[15]
        typ[0]
    return loc, color, typ

# from import_ldraw plugin
def locate(pattern):
    """Check if each part exists."""
    partName = pattern.replace("\\", os.path.sep)

    for path in paths:
        # Perform a direct check
        fname = os.path.join(path, partName)
        if os.path.exists(fname):
            return (fname, False)
        else:
            # Perform a normalized check
            fname = os.path.join(path, partName.lower())
            if os.path.exists(fname):
                return (fname, False)

    debugPrint("[Bricker] Could not find file {0}".format(fname))
    # FIXME: v1.2 rewrite - Wrong! return error to caller, (#35)
    # for example by returning an empty string!
    return ("ERROR, FILE NOT FOUND", False)

def parse_line(self, line):
    """Harvest the information from each line."""
    verts = []
    color = line[1]

    if color == '16':
        color = self.colour

    num_points = int((len(line) - 2) / 3)
    for i in range(num_points):
            self.points.append(
                (self.mat * mathutils.Vector((float(line[i * 3 + 2]),
                 float(line[i * 3 + 3]), float(line[i * 3 + 4])))).
                to_tuple())
            verts.append(len(self.points) - 1)
    self.faces.append(verts)
    self.material_index.append(color)


def readModelFromFile(path, name):
    file_name = __name__
    paths[0] = os.path.dirname(file_name)

    bricksDict = {}
    f = open('r', os.path.joins(path, name))
    modelName = f.readline()[2:]
    d = {}
    locs = []
    for line in f.readlines():
        loc, color, typ = getLDRBrickInfo(line)
        d[loc] = {'color':color, 'type':typ}
        locs.append(loc)

    lowest = Vector((0,0,0))
    lowest.x = min([loc[0] for loc in locs])
    lowest.y = min([loc[1] for loc in locs])
    lowest.z = min([loc[2] for loc in locs])

    for i,loc in enumerate(locs):
        dictLoc = loc - lowest
        dictLoc = vec_div(dictLoc, Vector((0.2, 0.2, 0.08)))
        key = listToStr(dictLoc)

        bricksDict[key] = createBricksDictEntry(
            name= "Bricker_%(modelName)s_brick__%(key)s" % locals(),
            draw= True,
            val=  1,
            co=   tuple(loc),
            size=
            type= d[loc]['type'],
        )

    cm.numBricksCreated = i
    cm.brickType = "BRICKS AND PLATES"
    cm.brickHeight = 0.08
