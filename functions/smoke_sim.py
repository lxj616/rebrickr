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

# code adapted from https://github.com/bwrsandman/blender-addons/blob/master/render_povray/render.py
def getSmokeInfo(smoke_obj):
    # Search smoke domain target for smoke modifiers
    for mod in smoke_obj.modifiers:
        if mod.name == 'Smoke':
            if mod.smoke_type == 'FLOW':
                if mod.flow_settings.smoke_flow_type == 'BOTH':
                    flowtype = 2
                else:
                    if mod.flow_settings.smoke_flow_type == 'SMOKE':
                        flowtype = 0
                    else:
                        if mod.flow_settings.smoke_flow_type == 'FIRE':
                            flowtype = 1

            if mod.smoke_type == 'DOMAIN':
                domain = smoke_obj
                smoke_modifier = mod

    if domain is not None:
        # Blender version 2.71 supports direct access to smoke data structure
        set = mod.domain_settings
        # get channel data
        density_grid = [v.real for v in set.density_grid]  # TODO: is this necessary or can I just copy it?
        color_grid = [v.real for v in set.color_grid]  # TODO: is this necessary or can I just copy it?
        # get resolution
        resolution = set.resolution_max
        big_res = Vector(tuple(set.domain_resolution))
        if set.use_high_resolution:
            big_res = vec_mult(big_res, [set.amplify + 1]*3)
        return density_grid, color_grid, big_res
    else:
        return None, None, None
