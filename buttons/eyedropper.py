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

# Blender imports
from bpy_extras.view3d_utils import region_2d_to_location_3d, region_2d_to_origin_3d, region_2d_to_vector_3d
from bpy.props import StringProperty

# Rebrickr imports
from ..functions import *

class EyeDropper(bpy.types.Operator):
    '''Use Eyedropper To pick object from scene'''
    bl_idname = "rebrickr.eye_dropper"                                            # unique identifier for buttons and menu items to reference
    bl_label = "Eye Dropper"                                                    # display name in the interface
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    target_prop = StringProperty(default = '')

    def __init__(self):
        FSM = {}

        '''
        main, nav, and wait states are automatically added in initialize function, called below.
        '''

        self.ob = None

    # from CG Cookie's retopoflow plugin
    def hover_scene(self,context,x,y,source_name):
        """ casts ray through point x,y and sets self.ob if obj intersected """
        scn = context.scene
        region = context.region
        rv3d = context.region_data
        coord = x, y
        ray_max = 10000
        view_vector = region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = region_2d_to_origin_3d(region, rv3d, coord)
        ray_target = ray_origin + (view_vector * ray_max)

        result, loc, normal, idx, ob, mx = scn.ray_cast(ray_origin, ray_target)

        if result and not ob.name.startswith('Rebrickr_' + source_name):
            self.ob = ob
            context.area.header_text_set('Target object: ' + ob.name)
        else:
            self.ob = None
            context.area.header_text_set('Target object: None')

    def modal(self, context, event):
        """ casts rays through mouse position, sets target_prop on LEFTMOUSE click """
        scn = context.scene

        if event.type == 'MOUSEMOVE':
            bpy.context.window.cursor_set("EYEDROPPER")
            x, y = event.mouse_region_x, event.mouse_region_y
            cm = scn.cmlist[scn.cmlist_index]
            self.hover_scene(context, x, y, cm.source_name)

        if event.type == 'LEFTMOUSE':
            bpy.context.window.cursor_set("DEFAULT")
            if self.ob is None:
                self.report({"INFO"}, "No object selected")
            else:
                scn.cmlist[scn.cmlist_index][self.target_prop] = self.ob.name
                redraw_areas("VIEW_3D")
            context.area.header_text_set()
            return {"FINISHED"}

        return {"PASS_THROUGH"}

    def execute(self, context):
        # run modal
        context.window_manager.modal_handler_add(self)
        return{"RUNNING_MODAL"}
