bl_info = {
    "name"        : "LEGOizer",
    "author"      : "Christopher Gearhart <chris@bblanimation.com>",
    "version"     : (0, 1, 0),
    "blender"     : (2, 78, 0),
    "description" : "Turn any mesh into LEGO bricks with the click of a button",
    "location"    : "View3D > Tools > LEGO Build",
    "warning"     : "Work in progress",
    "wiki_url"    : "",
    "tracker_url" : "",
    "category"    : "Object"}

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

# system imports
import bpy
from bpy.props import *
from .ui import *
from .buttons import *
props = bpy.props

def register():
    bpy.utils.register_module(__name__)

    bpy.types.Scene.preHollow = BoolProperty(
        name="Pre Hollow",
        description="Hollow out LEGO model with user defined shell thickness",
        default=True)

    bpy.types.Scene.shellThickness = IntProperty(
        name="Shell Thickness",
        description="Thickness of the LEGO shell",
        min=1, max=10,
        default=1)

    bpy.types.Scene.resolution = IntProperty(
        name="Resolution",
        description="Resolution of the final LEGO model",
        min=1, max=500,
        default=10)

    bpy.types.Scene.source_object = StringProperty(
        name="Source Object",
        description="Source Object",
        default="")

    # session properties

    # FILEPATHS
    addonsPath = bpy.utils.user_resource('SCRIPTS', "addons")
    props.obj_exports_folder = "%(addonsPath)s/legoizer/binvox/obj_exports/" % locals()
    props.final_output_folder = "%(addonsPath)s/voxelized_files/" % locals()
    props.binvox_path = "%(addonsPath)s/legoizer/binvox/binvox" % locals()
    props.scaleMesh_path = "%(addonsPath)s/legoizer/binvox/scaleMesh.py" % locals()
    props.backups_path = "%(addonsPath)s/legoizer/binvox/binvox_backups/" % locals()


def unregister():
    Scn = bpy.types.Scene

    del Scn.voxelResolution
    del Scn.shellThickness
    del Scn.preHollow

    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
