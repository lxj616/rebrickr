bl_info = {
    "name"        : "Bricker",
    "author"      : "Christopher Gearhart <chris@bblanimation.com>",
    "version"     : (1, 4, 0),
    "blender"     : (2, 79, 0),
    "description" : "Turn any mesh into a 3D brick sculpture or simulation with the click of a button",
    "location"    : "View3D > Tools > Bricker",
    "warning"     : "",  # used for warning icon and text in addons panel
    "wiki_url"    : "https://www.blendermarket.com/products/rebrickr/",
    "tracker_url" : "https://github.com/bblanimation/rebrickr/issues",
    "category"    : "Object"}

developer_mode = 0  # NOTE: Set to 0 for release, 1 for exposed dictionary, 2 for testBrickGenerators button
# NOTE: Disable "LEGO Logo" for releases?

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

# Addon imports
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

    bpy.props.bricker_module_name = __name__

    bpy.props.bricker_initialized = False
    bpy.props.bricker_undoUpdating = False

    bpy.props.bricker_version = str(bl_info["version"])[1:-1].replace(", ", ".")

    bpy.props.bricker_developer_mode = developer_mode

    bpy.types.Object.protected = BoolProperty(name='protected', default=False)
    bpy.types.Object.isBrickifiedObject = BoolProperty(name='Is Brickified Object', default=False)
    bpy.types.Object.isBrick = BoolProperty(name='Is Brick', default=False)
    bpy.types.Object.cmlist_id = IntProperty(name='Custom Model ID', description="ID of cmlist entry to which this object refers", default=-1)
    bpy.types.Material.num_averaged = IntProperty(name='Colors Averaged', description="Number of colors averaged together", default=0)

    bpy.types.Scene.Bricker_runningBlockingOperation = BoolProperty(default=False)
    bpy.types.Scene.Bricker_printTimes = BoolProperty(default=False)

    bpy.types.Scene.Bricker_last_layers = StringProperty(default="")
    bpy.types.Scene.Bricker_last_cmlist_index = IntProperty(default=-2)
    bpy.types.Scene.Bricker_active_object_name = StringProperty(default="")
    bpy.types.Scene.Bricker_last_active_object_name = StringProperty(default="")

    bpy.types.Scene.Bricker_copy_from_id = IntProperty(default=-1)

    # define legal brick sizes (key:height, val:[width,depth])
    bpy.props.Bricker_legal_brick_sizes = getLegalBrickSizes()

    # bpy.types.Scene.Bricker_snapping = BoolProperty(
    #     name="Bricker Snap",
    #     description="Snap to brick dimensions",
    #     default=False)
    # bpy.types.VIEW3D_HT_header.append(Bricker_snap_button)

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
    bpy.types.Scene.cmlist = CollectionProperty(type=Bricker_CreatedModels)
    bpy.types.Scene.cmlist_index = IntProperty(default=-1)

    # addon updater code and configurations
    addon_updater_ops.register(bl_info)


def unregister():
    Scn = bpy.types.Scene

    # addon updater unregister
    addon_updater_ops.unregister()

    del Scn.cmlist_index
    del Scn.cmlist
    # bpy.types.VIEW3D_HT_header.remove(Bricker_snap_button)
    # del Scn.Bricker_snapping
    del Scn.Bricker_copy_from_id
    del Scn.Bricker_last_active_object_name
    del Scn.Bricker_active_object_name
    del Scn.Bricker_last_cmlist_index
    del Scn.Bricker_last_layers
    del Scn.Bricker_printTimes
    del Scn.Bricker_runningBlockingOperation
    del bpy.types.Material.num_averaged
    del bpy.types.Object.cmlist_id
    del bpy.types.Object.isBrick
    del bpy.types.Object.isBrickifiedObject
    del bpy.types.Object.protected
    del bpy.props.bricker_developer_mode
    del bpy.props.bricker_version
    del bpy.props.bricker_undoUpdating
    del bpy.props.bricker_initialized
    del bpy.props.bricker_module_name

    # handle the keymaps
    wm = bpy.context.window_manager
    for km in addon_keymaps:
        wm.keyconfigs.addon.keymaps.remove(km)
    addon_keymaps.clear()

    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
