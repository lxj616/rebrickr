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

# Rebrickr imports
from ..functions import *


class sendDictionaryToFile(Operator):
    """send bricksDict to external file"""
    bl_idname = "rebrickr.send_dictionary_to_file"
    bl_label = "Send Dictionary to File"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(self, context):
        """ ensures operator can execute (if not, returns False) """
        return True

    def execute(self, context):
        try:
            scn, cm, _ = getActiveContextInfo()
            bricksDict, _ = getBricksDict(cm=cm, restrictContext=True)
            bricksDictString = json.dumps(bricksDict)
            bricksDictStrings = bricksDictString.split("}, ")
            for i,string in enumerate(bricksDictStrings):
                whitespace = " " if string.startswith("\"") else ""
                bricksDictStrings[i] = "%(whitespace)s%(string)s}," % locals()
            filePath = os.path.join(getLibraryPath(), "bricksDict_dump.py")
            self.writeToFile(bricksDictStrings, filePath)
            self.report({"INFO"}, "Bricks Dictionary saved to '%(filePath)s'" % locals())
        except:
            handle_exception()
        return{"FINISHED"}

    def writeToFile(self, strings, filePath):
        # write error to log text object
        f = open(filePath, "w")
        for string in strings:
            f.write("\n" + string)
        f.close()
