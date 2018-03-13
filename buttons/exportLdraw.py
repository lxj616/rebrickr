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
import time
import os
import json

# Blender imports
import bpy
from bpy.types import Operator
from bpy.props import StringProperty, CollectionProperty

# Bricker imports
from ..functions import *
from ..lib.Brick import *
from ..lib.abs_plastic_materials import *


class exportLdraw(Operator):
    """export bricksDict to ldraw file"""
    bl_idname = "bricker.export_ldraw"
    bl_label = "Export to Ldraw File"
    bl_options = {"REGISTER", "UNDO"}

    ################################################
    # Blender Operator methods

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns False) """
        return True

    def execute(self, context):
        try:
            self.writeLdrawFile()
        except:
            handle_exception()
        return{"FINISHED"}

    #############################################
    # class methods

    def writeLdrawFile(self):
        """ create and write Ldraw file """
        scn, cm, n = getActiveContextInfo()
        path = getExportFolder(filename=n + ".ldr")
        f = open(path, "w")
        f.write("0 %(n)s\n" % locals())
        f.write("0 Name:\n" % locals())
        f.write("0 Author: Unknown\n" % locals())
        legalBricks = getLegalBricks()
        absMatCodes = getAbsPlasticMatCodes()
        bricksDict, _ = getBricksDict(dType="MODEL" if cm.modelCreated else "ANIM", curFrame=scn.frame_current, cm=cm, restrictContext=True)
        for key in bricksDict.keys():
            if not bricksDict[key]["draw"] or bricksDict[key]["parent_brick"] != "self":
                continue
            size = bricksDict[key]["size"]
            typ = bricksDict[key]["type"]
            matrices = [" 0 0 -1 0 1 0  1 0  0",
                        " 1 0  0 0 1 0  0 0  1",
                        " 0 0  1 0 1 0 -1 0  0",
                        "-1 0  0 0 1 0  0 0 -1"]
            if typ == "SLOPE":
                idx = 0
                idx -= 2 if bricksDict[key]["flipped"] else 0
                idx -= 1 if bricksDict[key]["rotated"] else 0
                idx += 2 if (size[:2] in [[1, 2], [1, 3], [1, 4], [2, 3]] and not bricksDict[key]["rotated"]) or size[:2] == [2, 4] else 0
            else:
                idx = 1
            idx += 1 if size[1] > size[0] else 0
            matrix = matrices[idx]
            co = self.blendToLdrawUnits(cm, bricksDict[key], idx)
            mat_name = bricksDict[key]["mat_name"]
            rgba = bricksDict[key]["rgba"]
            if mat_name not in [None, ""]:
                color = absMatCodes[mat_name]
            elif rgba not in [None, ""]:
                rgb = [rgba[0] * 255, rgba[1] * 255, rgba[2] * 255]
                color = "0x2{hex}".format(hex=self.rgbToHex(rgb))
            else:
                color = 0
            parts = legalBricks[size[2]][typ]
            for i,part in enumerate(parts):
                if parts[i]["s"] in [size[:2], size[1::-1]]:
                    part = parts[i]["pt2" if typ == "SLOPE" and size[:2] in [[4, 2], [2, 4], [3, 2], [2, 3]] and bricksDict[key]["rotated"] else "pt"]
                    break
            brickFile = "%(part)s.dat" % locals()
            f.write("1 {color} {x} {y} {z} {matrix} {brickFile}\n".format(color=color, x=int(co.x), y=int(co.y), z=int(co.z), matrix=matrix, brickFile=brickFile))
        f.close()
        self.report({"INFO"}, "Ldraw file saved to '%(path)s'" % locals())

    def blendToLdrawUnits(self, cm, brickD, idx):
        """ convert location of brick from blender units to ldraw units """
        loc = Vector(brickD["co"])
        size = brickD["size"]
        zStep = getZStep(cm)
        dimensions = Bricks.get_dimensions(cm.brickHeight, zStep, cm.gap)
        h = 8 * (zStep % 4)
        loc.x = loc.x * (20 / (dimensions["width"] + dimensions["gap"]))
        loc.y = loc.y * (20 / (dimensions["width"] + dimensions["gap"]))
        loc.z = loc.z * (h  / (dimensions["height"] + dimensions["gap"]))
        loc.x += ((size[0] - 1) * 20) / 2
        loc.y += ((size[1] - 1) * 20) / 2
        if brickD["type"] == "SLOPE":
            if idx == 0:
                loc.x -= ((size[0] - 1) * 20) / 2
            elif idx in [1, -3]:
                loc.y += ((size[1] - 1) * 20) / 2
            elif idx in [2, -2]:
                loc.x += ((size[0] - 1) * 20) / 2
            elif idx in [3, -1]:
                loc.y -= ((size[1] - 1) * 20) / 2
        if brickD["type"] == "SLOPE" and sum(size[:2]) == 2:
            loc.z -= ((size[2] - 2) * 8)
        else:
            loc.z += ((size[2] - 1) * 8)
        # convert to right-handed co-ordinate system where -Y is "up"
        loc = Vector((loc.x, -loc.z, loc.y))
        return loc

    def rgbToHex(rgb):
        """ convert RGB list to HEX string """
        def clamp(x):
            return max(0, min(x, 255))
        r, g, b = rgb
        return "{0:02x}{1:02x}{2:02x}".format(clamp(r), clamp(g), clamp(b))

    #############################################
