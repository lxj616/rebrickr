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
from ..functions import *
props = bpy.props

class legoizerRunAnimation(bpy.types.Operator):
    """Manages animations created by the LEGOizer add on"""                     # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "scene.legoizer_run_animation"                                  # unique identifier for buttons and menu items to reference.
    bl_label = "Run LEGOized Animations"                                        # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}
    #
    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns false) """
        if modalRunning():
            return False
        return True

    def modal(self, context, event):
        """ ??? """
        scn = context.scene

        if len(self.lastFrame) != len(scn.cmlist):
            self.lastFrame = [scn.frame_current-1]*len(scn.cmlist)

        for i,cm in enumerate(scn.cmlist):
            if cm.animated:
                if context.scene.frame_current != self.lastFrame[i]:
                    fn0 = self.lastFrame[i]
                    fn1 = scn.frame_current
                    if fn1 < cm.lastStartFrame:
                        fn1 = cm.lastStartFrame
                    elif fn1 > cm.lastStopFrame:
                        fn1 = cm.lastStopFrame
                    self.lastFrame[i] = fn1
                    if self.lastFrame[i] == fn0:
                        continue
                    n = cm.source_name

                    try:
                        curBricks = bpy.data.groups["LEGOizer_%(n)s_bricks_frame_%(fn1)s" % locals()]
                        for brick in curBricks.objects:
                            brick.hide = False
                            # scn.objects.link(brick)
                    except Exception as e:
                        print(e)
                    try:
                        lastBricks = bpy.data.groups["LEGOizer_%(n)s_bricks_frame_%(fn0)s" % locals()]
                        for brick in lastBricks.objects:
                            brick.hide = True
                            # scn.objects.unlink(brick)
                            brick.select = False
                    except Exception as e:
                        print(e)

        if event.type in {"ESC"} and event.shift:
            scn.modalRunning = False
            bpy.context.window_manager["modal_running"] = False
            self.report({"INFO"}, "Modal Finished")
            return{"FINISHED"}
        # if scn.cmlist_index == -1:
        #     scn.modalRunning = False
        #     bpy.context.window_manager["modal_running"] = False
        #     self.report({"INFO"}, "Modal Finished")
        #     return{"FINISHED"}
        return {"PASS_THROUGH"}

    def execute(self, context):
        scn = context.scene
        self.lastFrame = []
        bpy.context.window_manager["modal_running"] = True
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def cancel(self, context):
        scn = context.scene
        bpy.context.window_manager["modal_running"] = False
