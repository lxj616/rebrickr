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

# Addon imports
from ..functions import *


class exportModelData(Operator):
    """send bricksDict to external file"""
    bl_idname = "bricker.export_model_data"
    bl_label = "Export Model Data"
    bl_options = {"REGISTER", "UNDO"}

    ################################################
    # Blender Operator methods

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns False) """
        return True

    def execute(self, context):
        try:
            scn, cm, n = getActiveContextInfo()
            path = getExportPath(cm, n, ".py")
            bType = "Frames" if cm.animated else "Bricks"
            numBs = len([b for b in bricksDict if not hasattr(b, "draw") or b.draw])
            # get model info
            modelInfoStrings = ["# Model Name:  " + cm.name,
                                "# Bricker Version:  " + cm.version,
                                "# Brick Height:  " + str(round(cm.brickHeight, 3)),
                                "# Gap Between Bricks:  " + str(round(cm.gap, 3)) + "\n",
                                "# Number of %(bType)s:  %(numBs)s" % locals(),
                                ""]
            # get bricksDict and separate into strings
            bricksDict, _ = getBricksDict(cm=cm)
            bricksDictStrings = json.dumps(bricksDict).split("}, ")
            for i,string in enumerate(bricksDictStrings):
                whitespace = " " if string.startswith("\"") else ""
                bricksDictStrings[i] = "%(whitespace)s%(string)s}," % locals()
            strings = modelInfoStrings + bricksDictStrings
            # write these strings to the specified filepath
            self.writeToFile(strings, path)
            self.report({"INFO"}, "Model data saved to '%(path)s'" % locals())
        except:
            handle_exception()
        return{"FINISHED"}

    #############################################
    # class methods

    def writeToFile(self, strings, filePath):
        # write error to log text object
        f = open(filePath, "w")
        for string in strings:
            f.write(string + "\n")
        f.close()

    #############################################
