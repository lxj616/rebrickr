'''
Copyright (C) 2017 Bricks Brought to Life
http://bblanimation.com/
chris@bblanimation.com

Created by Christopher Gearhart

Code copied from CG Cookie Retopoflow project
https://github.com/CGCookie/retopoflow

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
'''

# System imports
import sys
import math
import os
import time

# Blender imports
import bpy
import bpy
import bgl
from mathutils import Matrix
from bpy.types import Operator, SpaceView3D, bpy_struct
from bpy.app.handlers import persistent, load_post

# Rebrickr imports
from ...functions import *
from ...ui.common import set_cursor
from .ui_drawing import *
from .ui_options import retopoflow_version, options, firsttime_message

StructRNA = bpy.types.bpy_struct
rebrickr_broken = False
def still_registered(self):
    global rebrickr_broken
    if rebrickr_broken: return False
    def is_registered():
        if not hasattr(bpy.ops, 'rebrickr'): return False
        # try:    StructRNA.path_resolve(self, "properties")
        # except: return False
        return True
    if is_registered():
        return True
    else:
        showErrorMessage('Something went wrong. Please try restarting Blender or create an error report with CG Cookie so we can fix it!', wrap=240)
        rebrickr_broken = True
        return False


class Rebrickr_UI():
    bl_category    = "Rebrickr"
    bl_idname      = "rebrickr.ui"
    bl_label       = "Rebrickr UI"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'TOOLS'


    ################################################
    # Blender Operator methods

    @classmethod
    def poll(self, context):
        return True

    def invoke(self, context, event):
        ''' called when the user invokes (calls/runs) our tool '''
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}    # tell Blender to continue running our tool in modal

    def modal(self, context, event):
        return self.framework_start(context, event)

    def check(self, context):
        return True

    #############################################
    # initialization methods

    def __init__(self):
        ''' called once when RFMode plugin is enabled in Blender '''
        self.prev_mode = None

    @staticmethod
    def get_instance():
        if Rebrickr_UI.instance is None:
            Rebrickr_UI.creating = True
            Rebrickr_UI.instance = Rebrickr_UI()
            del Rebrickr_UI.creating
        Rebrickr_UI.instance.reset()
        return Rebrickr_UI.instance

    def reset(self):
        """ runs every time the instance is gotten """
        pass

    instance = None

    ###############################################
    # start up and shut down methods

    def framework_start(self, context):
        ''' called every time RFMode is started (invoked, executed, etc) '''

        # remember current mode and set to object mode so we can control
        # how the target mesh is rendered and so we can push new data
        # into target mesh
        self.prev_mode = {
            'OBJECT':        'OBJECT',          # for some reason, we must
            'EDIT_MESH':     'EDIT',            # translate bpy.context.mode
            'SCULPT':        'SCULPT',          # to something that
            'PAINT_VERTEX':  'VERTEX_PAINT',    # bpy.ops.object.mode_set()
            'PAINT_WEIGHT':  'WEIGHT_PAINT',    # accepts (for ui_end())...
            'PAINT_TEXTURE': 'TEXTURE_PAINT',
            }[bpy.context.mode]                 # WHY DO YOU DO THIS, BLENDER!?!?!?
        if self.prev_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        self.area = context.area

        # self.context_start()
        self.ui_start()

    def framework_end(self):
        '''
        finish up stuff, as our tool is leaving modal mode
        '''
        err = False
        try:
            self.ui_end()
        except:
            print_exception()
            err = True
        # try:    self.context_end()
        # except:
        #     print_exception()
        #     err = True
        if err: handle_exception()

        # restore previous mode
        bpy.ops.object.mode_set(mode=self.prev_mode)

    # def context_start(self):
    #     # should we generate new target object?
    #     if not RFContext.has_valid_target():
    #         print('generating new target')
    #         tar_name = "RetopoFlow"
    #         tar_location = bpy.context.scene.cursor_location
    #         tar_editmesh = bpy.data.meshes.new(tar_name)
    #         tar_object = bpy.data.objects.new(tar_name, tar_editmesh)
    #         tar_object.matrix_world = Matrix.Translation(tar_location)  # place new object at scene's cursor location
    #         tar_object.layers = list(bpy.context.scene.layers)          # set object on visible layers
    #         #tar_object.show_x_ray = get_settings().use_x_ray
    #         bpy.context.scene.objects.link(tar_object)
    #         bpy.context.scene.objects.active = tar_object
    #         tar_object.select = True
    #
    #     tar_object = bpy.context.scene.objects.active
    #
    #     # remember selection and unselect all
    #     self.selected_objects = [o for o in bpy.data.objects if o != tar_object and o.select]
    #     for o in self.selected_objects: o.select = False
    #
    #     tool = self.context_start_tool()
    #     self.rfctx = RFContext(self, tool)
    #
    # def context_start_tool(self): return None
    #
    # def context_end(self):
    #     if hasattr(self, 'rfctx'):
    #         self.rfctx.end()
    #         del self.rfctx
    #
    #     # restore selection
    #     for o in self.selected_objects: o.select = True

    def ui_start(self):
        # report something useful to user
        bpy.context.area.header_text_set('Rebrickr Sculpt Mode')

        # # remember space info and hide all non-renderable items
        # RFRecover.save_window_state()
        self.space_info = {}
        for wm in bpy.data.window_managers:
            for win in wm.windows:
                for area in win.screen.areas:
                    if area.type != 'VIEW_3D': continue
                    for space in area.spaces:
                        if space.type != 'VIEW_3D': continue
                        self.space_info[space] = {
                            'show_only_render': space.show_only_render,
                            'show_manipulator': space.show_manipulator,
                        }
                        space.show_only_render = True
                        space.show_manipulator = False

        # initialize windows
        # self.windows_start()

        # add callback handlers
        self.cb_pr_handle = SpaceView3D.draw_handler_add(self.draw_callback_preview,   (bpy.context, ), 'WINDOW', 'PRE_VIEW')
        self.cb_pv_handle = SpaceView3D.draw_handler_add(self.draw_callback_postview,  (bpy.context, ), 'WINDOW', 'POST_VIEW')
        self.cb_pp_handle = SpaceView3D.draw_handler_add(self.draw_callback_postpixel, (bpy.context, ), 'WINDOW', 'POST_PIXEL')
        # darken other spaces
        self.spaces = [
            bpy.types.SpaceClipEditor,
            bpy.types.SpaceConsole,
            bpy.types.SpaceDopeSheetEditor,
            bpy.types.SpaceFileBrowser,
            bpy.types.SpaceGraphEditor,
            bpy.types.SpaceImageEditor,
            bpy.types.SpaceInfo,
            bpy.types.SpaceLogicEditor,
            bpy.types.SpaceNLA,
            bpy.types.SpaceNodeEditor,
            bpy.types.SpaceOutliner,
            bpy.types.SpaceProperties,
            bpy.types.SpaceSequenceEditor,
            bpy.types.SpaceTextEditor,
            bpy.types.SpaceTimeline,
            #bpy.types.SpaceUVEditor,       # <- does not exist?
            bpy.types.SpaceUserPreferences,
            #'SpaceView3D',                 # <- specially handled
            ]
        self.areas = [ 'WINDOW', 'HEADER' ]
        # ('WINDOW', 'HEADER', 'CHANNELS', 'TEMPORARY', 'UI', 'TOOLS', 'TOOL_PROPS', 'PREVIEW')
        self.cb_pp_tools   = SpaceView3D.draw_handler_add(self.draw_callback_cover, (bpy.context, ), 'TOOLS',      'POST_PIXEL')
        self.cb_pp_props   = SpaceView3D.draw_handler_add(self.draw_callback_cover, (bpy.context, ), 'TOOL_PROPS', 'POST_PIXEL')
        self.cb_pp_ui      = SpaceView3D.draw_handler_add(self.draw_callback_cover, (bpy.context, ), 'UI',         'POST_PIXEL')
        self.cb_pp_header  = SpaceView3D.draw_handler_add(self.draw_callback_cover, (bpy.context, ), 'HEADER',     'POST_PIXEL')
        self.cb_pp_all = [
            (s, a, s.draw_handler_add(self.draw_callback_cover, (bpy.context,), a, 'POST_PIXEL'))
            for s in self.spaces
            for a in self.areas
            ]
        tag_redraw_areas()

        self.maximize_area = False
        self.show_toolshelf = bpy.context.area.regions[1].width > 1
        self.show_properties = bpy.context.area.regions[3].width > 1
        self.region_overlap = bpy.context.user_preferences.system.use_region_overlap
        if self.region_overlap:
            if self.show_toolshelf: bpy.ops.view3d.toolshelf()
            if self.show_properties: bpy.ops.view3d.properties()

        # self.wrap_panels()

    def toggle_maximize_area(self):
        bpy.ops.screen.screen_full_area(use_hide_panels=False)
        self.maximize_area = not self.maximize_area

    def ui_end(self):
        # if not hasattr(self, 'rfctx'): return
        # restore states of meshes
        # self.rfctx.rftarget.restore_state()
        #for rfsource in self.rfctx.rfsources: rfsource.restore_state()

        # if self.rfctx.timer:
        #     bpy.context.window_manager.event_timer_remove(self.rfctx.timer)
        #     self.rfctx.timer = None

        # remove callback handlers
        if hasattr(self, 'cb_pr_handle'):
            SpaceView3D.draw_handler_remove(self.cb_pr_handle, "WINDOW")
            del self.cb_pr_handle
        if hasattr(self, 'cb_pv_handle'):
            SpaceView3D.draw_handler_remove(self.cb_pv_handle, "WINDOW")
            del self.cb_pv_handle
        if hasattr(self, 'cb_pp_handle'):
            SpaceView3D.draw_handler_remove(self.cb_pp_handle, "WINDOW")
            del self.cb_pp_handle
        if hasattr(self, 'cb_pp_tools'):
            SpaceView3D.draw_handler_remove(self.cb_pp_tools,  "TOOLS")
            del self.cb_pp_tools
        if hasattr(self, 'cb_pp_props'):
            SpaceView3D.draw_handler_remove(self.cb_pp_props,  "TOOL_PROPS")
            del self.cb_pp_props
        if hasattr(self, 'cb_pp_ui'):
            SpaceView3D.draw_handler_remove(self.cb_pp_ui,     "UI")
            del self.cb_pp_ui
        if hasattr(self, 'cb_pp_header'):
            SpaceView3D.draw_handler_remove(self.cb_pp_header, "HEADER")
            del self.cb_pp_header
        if hasattr(self, 'cb_pp_all'):
            for s,a,cb in self.cb_pp_all: s.draw_handler_remove(cb, a)
            del self.cb_pp_all

        # if self.region_overlap:
        #     if self.show_toolshelf: bpy.ops.view3d.toolshelf()
        #     if self.show_properties: bpy.ops.view3d.properties()
        if self.maximize_area:
            bpy.ops.screen.screen_full_area(use_hide_panels=False)

        set_cursor('DEFAULT')

        # restore space info
        for space,data in self.space_info.items():
            for k,v in data.items(): space.__setattr__(k, v)

        # remove useful reporting
        self.area.header_text_set()

        tag_redraw_areas()

    def tag_redraw(self):
        if bpy.context.area and bpy.context.area.type == 'VIEW_3D': self.area = bpy.context.area
        self.area.tag_redraw()
        self.area.header_text_set('Rebrickr Sculpt Mode')

    def windows_start(self):
        self.drawing = Drawing.get_instance()
        self.window_manager = UI_WindowManager()

        def get_selected_tool():
            # return self.tool.name()
            return None
        def set_selected_tool(name):
            # for ids,rft in RFTool.get_tools():
            #     if rft.bl_label == name:
            #         self.set_tool(rft.rft_class())
            pass
        def update_tool_collapsed():
            b = options['tools_min']
            self.tool_min.visible = b
            self.tool_max.visible = not b
        def get_tool_collapsed():
            update_tool_collapsed()
            return options['tools_min']
        def set_tool_collapsed(b):
            options['tools_min'] = b
            update_tool_collapsed()
        def show_reporting():
            options['welcome'] = True
            self.window_welcome.visible = options['welcome']
        def hide_reporting():
            options['welcome'] = False
            self.window_welcome.visible = options['welcome']

        def open_github():
            bpy.ops.wm.url_open(url="https://github.com/bblanimation/rebrickr/issues")

        def get_theme():
            options['color theme']
        def set_theme(v):
            options['color theme'] = v
            # self.replace_opts()
        def reset_options():
            options.reset()
            # self.replace_opts()
        def get_instrument():
            return options['instrument']
        def set_instrument(v):
            options['instrument'] = v
        def update_profiler_visible():
            # nonlocal prof_print, prof_reset, prof_disable, prof_enable
            # v = profiler.debug
            # prof_print.visible = v
            # prof_reset.visible = v
            # prof_disable.visible = v
            # prof_enable.visible = not v
            pass
        def enable_profiler():
            # profiler.enable()
            # update_profiler_visible()
            pass
        def disable_profiler():
            # profiler.disable()
            # update_profiler_visible()
            pass
        def get_debug_level():
            # return self.settings.debug
            return 1
        def set_debug_level(v):
            # self.settings.debug = v
            pass


        # self.tool_window = self.window_manager.create_window('Tools', {'sticky':7})
        # self.tool_max = UI_Container(margin=0)
        # self.tool_min = UI_Container(margin=0, vertical=False)
        # self.tool_selection_max = UI_Options(get_selected_tool, set_selected_tool, vertical=True)
        # self.tool_selection_min = UI_Options(get_selected_tool, set_selected_tool, vertical=False)
        # tools_options = []
        # for i,rft_data in enumerate(RFTool.get_tools()):
        #     ids,rft = rft_data
        #     self.tool_selection_max.add_option(rft.bl_label, icon=rft.rft_class().get_ui_icon())
        #     self.tool_selection_min.add_option(rft.bl_label, icon=rft.rft_class().get_ui_icon(), showlabel=False)
        #     ui_options = rft.rft_class().get_ui_options()
        #     if ui_options: tools_options.append((rft.bl_label,ui_options))
        # get_tool_collapsed()
        # self.tool_max.add(self.tool_selection_max)
        #
        # extra = self.tool_max.add(UI_Container())
        # #help_icon = UI_Image('help_32.png')
        # #help_icon.set_size(16, 16)
        # extra.add(UI_Button('Tool Help', self.toggle_tool_help, align=0, margin=0)) # , icon=help_icon
        # extra.add(UI_Button('Collapse', lambda: set_tool_collapsed(True), align=0, margin=0))
        # #extra.add(UI_Checkbox('Collapsed', get_tool_collapsed, set_tool_collapsed))
        # extra.add(UI_Button('Exit', self.quit, align=0, margin=0))
        # self.tool_min.add(self.tool_selection_min)
        # self.tool_min.add(UI_Checkbox(None, get_tool_collapsed, set_tool_collapsed))
        # self.tool_window.add(self.tool_max)
        # self.tool_window.add(self.tool_min)


        window_info = self.window_manager.create_window('Info', {'sticky':1, 'visible':True})
        window_info.add(UI_Label('RetopoFlow %s' % retopoflow_version))
        container = window_info.add(UI_Container(margin=0, vertical=False))
        container.add(UI_Button('Welcome!', show_reporting, align=0))
        container.add(UI_Button('Report Issue', open_github, align=0))
        info_adv = window_info.add(UI_Collapsible('Advanced', collapsed=True))

        fps_save = info_adv.add(UI_Container(vertical=False))
        self.window_debug_fps = fps_save.add(UI_Label('fps: 0.00'))
        self.window_debug_save = fps_save.add(UI_Label('save: inf'))

        container_theme = info_adv.add(UI_Container(vertical=False))
        container_theme.add(UI_Label('Theme:', margin=4))
        opt_theme = container_theme.add(UI_Options(get_theme, set_theme, vertical=False, margin=0))
        opt_theme.add_option('Blue', icon=UI_Image('theme_blue.png'), showlabel=False, align=0)
        opt_theme.add_option('Green', icon=UI_Image('theme_green.png'), showlabel=False, align=0)
        opt_theme.add_option('Orange', icon=UI_Image('theme_orange.png'), showlabel=False, align=0)
        opt_theme.set_option(options['color theme'])

        info_adv.add(UI_IntValue('Debug Level', get_debug_level, set_debug_level))
        info_adv.add(UI_Checkbox('Instrument', get_instrument, set_instrument))

        # info_profiler = info_adv.add(UI_Collapsible('Profiler', collapsed=True, vertical=False))
        # prof_print = info_profiler.add(UI_Button('Print', profiler.printout, align=0))
        # prof_reset = info_profiler.add(UI_Button('Reset', profiler.clear, align=0))
        # prof_disable = info_profiler.add(UI_Button('Disable', disable_profiler, align=0))
        # prof_enable = info_profiler.add(UI_Button('Enable', enable_profiler, align=0))
        # update_profiler_visible()

        info_adv.add(UI_Button('Reset Options', reset_options, align=0))

        window_tool_options = self.window_manager.create_window('Options', {'sticky':9})

        dd_general = window_tool_options.add(UI_Collapsible('General', collapsed=False))
        dd_general.add(UI_Button('Maximize Area', self.toggle_maximize_area, align=0))
        # dd_general.add(UI_Button('Snap All Verts', self.snap_all_verts, align=0))

        # dd_symmetry = window_tool_options.add(UI_Collapsible('Symmetry', equal=True, vertical=False))
        # dd_symmetry.add(UI_Checkbox2('x', lambda: self.get_symmetry('x'), lambda v: self.set_symmetry('x',v), options={'spacing':0}))
        # dd_symmetry.add(UI_Checkbox2('y', lambda: self.get_symmetry('y'), lambda v: self.set_symmetry('y',v), options={'spacing':0}))
        # dd_symmetry.add(UI_Checkbox2('z', lambda: self.get_symmetry('z'), lambda v: self.set_symmetry('z',v), options={'spacing':0}))

        # for tool_name,tool_options in tools_options:
        #     # window_tool_options.add(UI_Spacer(height=5))
        #     ui_options = window_tool_options.add(UI_Collapsible(tool_name))
        #     for tool_option in tool_options: ui_options.add(tool_option)

        self.window_welcome = self.window_manager.create_window('Welcome!', {'sticky':5, 'visible':options['welcome'], 'movable':False, 'bgcolor':(0.2,0.2,0.2,0.95)})
        self.window_welcome.add(UI_Rule())
        self.window_welcome.add(UI_Markdown(firsttime_message))
        self.window_welcome.add(UI_Rule())
        self.window_welcome.add(UI_Button('Close', hide_reporting, align=0, bgcolor=(0.5,0.5,0.5,0.4), margin=2), footer=True)

        # self.window_help = self.window_manager.create_window('Tool Help', {'sticky':5, 'visible':False, 'movable':False, 'bgcolor':(0.2,0.2,0.2,0.95)})
        # self.window_help.add(UI_Rule())
        # self.ui_helplabel = UI_Markdown('help text here!')
        # self.window_help.add(self.ui_helplabel)
        # self.window_help.add(UI_Rule())
        # self.window_help.add(UI_Button('Close', self.toggle_tool_help, align=0, bgcolor=(0.5,0.5,0.5,0.4), margin=2), footer=True)

    ####################################################################
    # Draw handler function

    def draw_callback_preview(self, context):
        if not still_registered(self): return
        bgl.glPushAttrib(bgl.GL_ALL_ATTRIB_BITS)    # save OpenGL attributes
        try:    self.draw_preview()
        except: handle_exception()
        bgl.glPopAttrib()                           # restore OpenGL attributes

    def draw_preview(self):
        # if not self.actions.r3d: return

        bgl.glEnable(bgl.GL_MULTISAMPLE)
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glEnable(bgl.GL_POINT_SMOOTH)
        bgl.glDisable(bgl.GL_DEPTH_TEST)

        bgl.glMatrixMode(bgl.GL_MODELVIEW)
        bgl.glPushMatrix()
        bgl.glLoadIdentity()
        bgl.glMatrixMode(bgl.GL_PROJECTION)
        bgl.glPushMatrix()
        bgl.glLoadIdentity()

        bgl.glBegin(bgl.GL_TRIANGLES)
        for i in range(0,360,10):
            r0,r1 = i*math.pi/180.0, (i+10)*math.pi/180.0
            x0,y0 = math.cos(r0)*2,math.sin(r0)*2
            x1,y1 = math.cos(r1)*2,math.sin(r1)*2
            bgl.glColor4f(0,0,0.01,0.0)
            bgl.glVertex2f(0,0)
            bgl.glColor4f(0,0,0.01,0.8)
            bgl.glVertex2f(x0,y0)
            bgl.glVertex2f(x1,y1)
        bgl.glEnd()

        bgl.glMatrixMode(bgl.GL_PROJECTION)
        bgl.glPopMatrix()
        bgl.glMatrixMode(bgl.GL_MODELVIEW)
        bgl.glPopMatrix()

    def draw_callback_postview(self, context):
        if not still_registered(self): return
        bgl.glPushAttrib(bgl.GL_ALL_ATTRIB_BITS)    # save OpenGL attributes
        bgl.glPopAttrib()                           # restore OpenGL attributes

    def draw_callback_postpixel(self, context):
        if not still_registered(self): return
        bgl.glPushAttrib(bgl.GL_ALL_ATTRIB_BITS)    # save OpenGL attributes
        bgl.glPopAttrib()                           # restore OpenGL attributes
        # run post_poxel for ui windows
        try:
            self.window_manager.draw_postpixel()
        except AttributeError:
            pass

    def draw_callback_cover(self, context):
        if not still_registered(self): return
        bgl.glPushAttrib(bgl.GL_ALL_ATTRIB_BITS)
        bgl.glMatrixMode(bgl.GL_PROJECTION)
        bgl.glPushMatrix()
        bgl.glLoadIdentity()
        bgl.glColor4f(0,0,0,0.5)    # TODO: use window background color??
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glDisable(bgl.GL_DEPTH_TEST)
        bgl.glBegin(bgl.GL_QUADS)   # TODO: not use immediate mode
        bgl.glVertex2f(-1, -1)
        bgl.glVertex2f( 1, -1)
        bgl.glVertex2f( 1,  1)
        bgl.glVertex2f(-1,  1)
        bgl.glEnd()
        bgl.glPopMatrix()
        bgl.glPopAttrib()

    ##################################################################
    # modal method

    # def framework_modal(self, context, event):
    #     '''
    #     Called by Blender while our tool is running modal.
    #     This state checks if navigation is occurring.
    #     This state calls auxiliary wait state to see into which state we transition.
    #     '''
    #
    #     if not still_registered(self):
    #         # something bad happened, so bail!
    #         return {'CANCELLED'}
    #
    #     if self.exception_quit:
    #         # something bad happened, so bail!
    #         self.framework_end()
    #         return {'CANCELLED'}
    #
    #     profiler.printfile()
    #
    #     # TODO: can we not redraw only when necessary?
    #     self.tag_redraw()
    #     #context.area.tag_redraw()       # force redraw
    #
    #     return {'RUNNING_MODAL'}    # tell Blender to continue running our tool in modal

# rfmode_tools = {}
#
# @stats_wrapper
# def setup_tools():
#     for rft in RFTool:
#         def classfactory(rft):
#             rft_name = rft().name()
#             cls_name = 'RFMode_' + rft_name.replace(' ','_')
#             id_name = 'cgcookie.rfmode_' + rft_name.replace(' ','_').lower()
#             print('Creating: ' + cls_name)
#             def context_start_tool(self): return rft()
#             newclass = type(cls_name, (RFMode,),{
#                 "context_start_tool": context_start_tool,
#                 'bl_idname': id_name,
#                 "bl_label": rft_name,
#                 'bl_description': rft().description(),
#                 'rf_icon': rft().icon(),
#                 'rft_class': rft,
#                 })
#             rfmode_tools[id_name] = newclass
#             globals()[cls_name] = newclass
#         classfactory(rft)
#
#     listed,unlisted = [None]*len(RFTool.preferred_tool_order),[]
#     for ids,rft in rfmode_tools.items():
#         name = rft.bl_label
#         if name in RFTool.preferred_tool_order:
#             idx = RFTool.preferred_tool_order.index(name)
#             listed[idx] = (ids,rft)
#         else:
#             unlisted.append((ids,rft))
#     # sort unlisted entries by name
#     unlisted.sort(key=lambda k:k[1].bl_label)
#     listed = [data for data in listed if data]
#     RFTool.order = listed + unlisted
#
# setup_tools()
