bl_info = {
    "name"        : "Rebrickr",
    "author"      : "Christopher Gearhart <chris@bblanimation.com>",
    "version"     : (1, 1, 1),
    "blender"     : (2, 78, 0),
    "description" : "Turn any mesh into a 3D brick sculpture or simulation with the click of a button",
    "location"    : "View3D > Tools > Rebrickr",
    "warning"     : "",  # used for warning icon and text in addons panel
    "wiki_url"    : "https://www.blendermarket.com/creator/products/rebrickr/",
    "tracker_url" : "https://github.com/bblanimation/rebrickr/issues",
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

# System imports
# NONE!

# Blender imports
import bpy
from bpy.props import *

# Rebrickr imports
from .ui import *
from .buttons import *
from .buttons.customize import *
from .operators import *
from .lib.preferences import *
from .lib.Brick.legal_brick_sizes import getLegalBrickSizes
from .lib import keymaps

# updater import
from . import addon_updater_ops

# store keymaps here to access after registration
addon_keymaps = []


def register():
    bpy.utils.register_module(__name__)

    bpy.props.rebrickr_module_name = __name__

    bpy.props.rebrickr_initialized = False
    bpy.props.rebrickr_undoUpdating = False

    bpy.props.rebrickr_version = str(bl_info["version"])[1:-1].replace(", ", ".")

    bpy.types.Object.protected = BoolProperty(name='protected', default=False)
    bpy.types.Object.isBrickifiedObject = BoolProperty(name='Is Brickified Object', default=False)
    bpy.types.Object.isBrick = BoolProperty(name='Is Brick', default=False)
    bpy.types.Object.cmlist_id = IntProperty(name='Custom Model ID', description="ID of cmlist entry to which this object refers", default=-1)
    bpy.types.Material.num_averaged = IntProperty(name='Colors Averaged', description="Number of colors averaged together", default=0)

    bpy.types.Scene.Rebrickr_printTimes = BoolProperty(default=False)

    bpy.types.Scene.Rebrickr_runningOperation = BoolProperty(default=False)
    bpy.types.Scene.Rebrickr_last_layers = StringProperty(default="")
    bpy.types.Scene.Rebrickr_last_cmlist_index = IntProperty(default=-2)
    bpy.types.Scene.Rebrickr_active_object_name = StringProperty(default="")
    bpy.types.Scene.Rebrickr_last_active_object_name = StringProperty(default="")

    bpy.types.Scene.Rebrickr_copy_from_id = IntProperty(default=-1)

    # define legal brick sizes (key:height, val:[width,depth])
    bpy.props.Rebrickr_legal_brick_sizes = getLegalBrickSizes()

    # bpy.types.Scene.Rebrickr_snapping = BoolProperty(
    #     name="Rebrickr Snap",
    #     description="Snap to brick dimensions",
    #     default=False)
    # bpy.types.VIEW3D_HT_header.append(Rebrickr_snap_button)

    # handle the keymap
    wm = bpy.context.window_manager
    # Note that in background mode (no GUI available), keyconfigs are not available either, so we have
    # to check this to avoid nasty errors in background case.
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')
        keymaps.addKeymaps(km)
        addon_keymaps.append(km)

    # other things (UI List)
    bpy.types.Scene.cmlist = CollectionProperty(type=Rebrickr_CreatedModels)
    bpy.types.Scene.cmlist_index = IntProperty(default=-1)

    # addon updater code and configurations
    addon_updater_ops.register(bl_info)


def unregister():
    Scn = bpy.types.Scene

    # addon updater unregister
    addon_updater_ops.unregister()

    del Scn.cmlist_index
    del Scn.cmlist
    # bpy.types.VIEW3D_HT_header.remove(Rebrickr_snap_button)
    # del Scn.Rebrickr_snapping
    del Scn.Rebrickr_copy_from_id
    del Scn.Rebrickr_last_active_object_name
    del Scn.Rebrickr_active_object_name
    del Scn.Rebrickr_last_cmlist_index
    del Scn.Rebrickr_last_layers
    del Scn.Rebrickr_runningOperation
    del Scn.Rebrickr_printTimes
    del bpy.types.Object.isBrick
    del bpy.types.Object.isBrickifiedObject
    del bpy.types.Object.protected
    del bpy.props.rebrickr_version
    del bpy.props.rebrickr_undoUpdating
    del bpy.props.rebrickr_initialized
    del bpy.props.rebrickr_module_name

    # handle the keymaps
    wm = bpy.context.window_manager
    for km in addon_keymaps:
        wm.keyconfigs.addon.keymaps.remove(km)
    addon_keymaps.clear()

    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
