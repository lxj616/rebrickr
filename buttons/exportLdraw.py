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

# Bricker imports
from ..functions import *
from ..lib.Brick import *
from ..lib.abs_plastic_materials import *


class exportLdraw(Operator):
    """export bricksDict to ldraw file"""
    bl_idname = "bricker.export_ldraw"
    bl_label = "Export to Ldraw File"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns False) """
        return True

    def execute(self, context):
        try:
            scn, cm, n = getActiveContextInfo()
            bricksDict, _ = getBricksDict(dType="MODEL" if cm.modelCreated else "ANIM", curFrame=scn.frame_current, cm=cm, restrictContext=True)
            filePath = os.path.join(getLibraryPath(), "test_file.ldr")
            self.writeLdrawFile(bricksDict, filePath, n)
            self.report({"INFO"}, "Ldraw file saved to '%(filePath)s'" % locals())
        except:
            handle_exception()
        return{"FINISHED"}

    def writeLdrawFile(self, bricksDict, path, n):
        cm = getActiveContextInfo()[1]
        f = open(path, "w")
        f.write("0 %(n)s\n" % locals())
        f.write("0 Name:\n" % locals())
        f.write("0 Author: Unknown\n" % locals())
        legalBricks = getLegalBricks()
        absMatCodes = getAbsPlasticMatCodes()
        for key in bricksDict.keys():
            if bricksDict[key]["draw"] and bricksDict[key]["parent_brick"] == "self":
                co = blendToLdrawUnits(cm, bricksDict[key])
                size = bricksDict[key]["size"]
                mat_name = bricksDict[key]["mat_name"]
                rgba = bricksDict[key]["rgba"]
                if mat_name:
                    color = absMatCodes[mat_name]
                elif rgba:
                    rgb = [rgba[0] * 255, rgba[1] * 255, rgba[2] * 255]
                    color = "0x2{hex}".format(hex=rgbToHex(rgb))
                else:
                    color = 0
                typ = bricksDict[key]["type"]
                matrices = [" 0 0 -1 0 1 0  1 0  0",
                            " 1 0  0 0 1 0  0 0  1",
                            " 0 0  1 0 1 0 -1 0  0",
                            "-1 0  0 0 1 0  0 0 -1"]
                idx = 0 if typ == "SLOPE" else 1
                idx += 2 if size[0] > size[1] else 0
                idx -= 2 if bricksDict[key]["flipped"] and typ == "SLOPE" else 0
                idx -= 1 if bricksDict[key]["rotated"] and typ == "SLOPE" else 0
                if typ == "SLOPE":
                    print(idx)
                matrix = matrices[idx]
                parts = legalBricks[size[2]][typ]
                for i,part in enumerate(parts):
                    if parts[i]["s"] in [size[:2], size[1::-1]]:
                        part = parts[i]["pt"]
                        break
                brickFile = "%(part)s.dat" % locals()
                f.write("1 {color} {x} {y} {z} {matrix} {brickFile}\n".format(color=color, x=int(co.x), y=int(co.y), z=int(co.z), matrix=matrix, brickFile=brickFile))
        f.close()


def blendToLdrawUnits(cm, brickD):
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
    if brickD["type"] == "SLOPE" and sum(size[:2]) == 2:
        loc.z -= ((size[2] - 2) * 8)
    else:
        loc.z += ((size[2] - 1) * 8)
    # convert to right-handed co-ordinate system where -Y is "up"
    loc = Vector((loc.x, -loc.z, loc.y))
    return loc


def rgbToHex(rgb):
    def clamp(x):
        return max(0, min(x, 255))
    r, g, b = rgb
    return "{0:02x}{1:02x}{2:02x}".format(clamp(r), clamp(g), clamp(b))
