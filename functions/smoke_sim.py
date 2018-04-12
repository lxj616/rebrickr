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

# Addon imports
from .common import *
from .general import *

# code adapted from https://github.com/bwrsandman/blender-addons/blob/master/render_povray/render.py
def getSmokeInfo(smoke_obj):
    smoke_data = None
    # Search smoke domain target for smoke modifiers
    for mod in smoke_obj.modifiers:
        if hasattr(mod, "smoke_type") and mod.smoke_type == 'DOMAIN':
            # Blender version 2.71 supports direct access to smoke data structure
            smoke_data = mod.domain_settings
            break

    if smoke_data is not None:
        # get channel data
        density_grid = list(smoke_data.density_grid)
        flame_grid = list(smoke_data.flame_grid)
        color_grid = list(smoke_data.color_grid)
        # get resolution
        smoke_res = getSmokeRes(smoke_data)
        adapt = smoke_data.use_adaptive_domain
        res = Vector(smoke_data.domain_resolution)
        max_res_i = smoke_data.resolution_max
        max_res = Vector(res) * (max_res_i / max(res))
        return density_grid, flame_grid, color_grid, smoke_res, adapt, res, max_res
    else:
        return None, None, None, None


def getSmokeRes(smoke_data):
    smoke_res = list(smoke_data.domain_resolution)
    if smoke_data.use_high_resolution:
        smoke_res = [int((smoke_data.amplify + 1) * i) for i in smoke_res]
    return smoke_res
