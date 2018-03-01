'''
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
'''

# System imports
import sys
import math
import os
import time
import copy

# Blender imports
import bpy
import bpy
import bgl
from mathutils import Matrix
from bpy.types import Operator, SpaceView3D, bpy_struct
from bpy.app.handlers import persistent, load_post

# Bricker imports
from ...functions import *
from ...lib.caches import bricker_bfm_cache

python_undo_state = {}


class UndoStack():
    bl_category = "Bricker"
    bl_idname = "bricker.undo_stack"
    bl_label = "Undo Stack"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    @staticmethod
    def get_instance():
        if UndoStack.instance is None:
            UndoStack.creating = True
            UndoStack.instance = UndoStack()
            del UndoStack.creating
        UndoStack.instance.reset()
        return UndoStack.instance

    def reset(self):
        """ runs every time the instance is gotten """
        pass

    ################################################
    # initialization method

    def __init__(self):
        assert hasattr(UndoStack, 'creating'), 'Do not create new UndoStack directly!  Use UndoStack.new()'
        self.undo = []  # undo stack of causing actions, FSM state, tool states, and rftargets
        self.redo = []  # redo stack of causing actions, FSM state, tool states, and rftargets
        scn = bpy.context.scene
        for cm in scn.cmlist:
            cm.blender_undo_state = 0

    ###################################################
    # class variables

    instance = None
    undo_depth = 500    # set in User Preferences?

    ###################################################
    # undo / redo stack operations

    @staticmethod
    def iterateStates(cm):
        """ iterate undo states """
        scn = bpy.context.scene
        global python_undo_state
        bpy.props.bricker_undoUpdating = True
        if cm.id not in python_undo_state:
            python_undo_state[cm.id] = 0
        python_undo_state[cm.id] += 1
        cm.blender_undo_state += 1
        bpy.props.bricker_undoUpdating = False

    def matchPythonToBlenderState(self):
        scn = bpy.context.scene
        for cm in scn.cmlist:
            python_undo_state[cm.id] = cm.blender_undo_state

    def getLength(self): return len(self.undo)

    def isUpdating(self): return bpy.props.bricker_undoUpdating

    def _create_state(self, action):
        return {
            'action':       action,
            'bfm_cache':    copy.deepcopy(bricker_bfm_cache),
            }

    def _restore_state(self, state):
        global bricker_bfm_cache
        for key in state['bfm_cache'].keys():
            bricker_bfm_cache[key] = state['bfm_cache'][key]

    def undo_push(self, action, repeatable=False):
        # skip pushing to undo if action is repeatable and we are repeating actions
        if repeatable and self.undo and self.undo[-1]['action'] == action:
            return
        # skip pushing to undo if bricker not initialized
        if not bpy.props.bricker_initialized:
            return
        self.undo.append(self._create_state(action))
        while len(self.undo) > self.undo_depth:
            self.undo.pop(0)  # limit stack size
        self.redo.clear()
        self.instrument_write(action)

    def undo_pop(self):
        if not self.undo:
            return
        self.redo.append(self._create_state('undo'))
        self._restore_state(self.undo.pop())
        self.instrument_write('undo')
        # iterate undo states
        global python_undo_state
        scn, cm, _ = getActiveContextInfo()
        python_undo_state[cm.id] -= 1

    def undo_pop_clean(self):
        if not self.undo:
            return
        self.undo.pop()

    def undo_cancel(self):
        self._restore_state(self.undo.pop())
        self.instrument_write('cancel (undo)')

    def redo_pop(self):
        if not self.redo:
            return
        self.undo.append(self._create_state('redo'))
        self._restore_state(self.redo.pop())
        self.instrument_write('redo')
        # iterate undo states
        global python_undo_state
        scn, cm, _ = getActiveContextInfo()
        python_undo_state[cm.id] += 1

    def instrument_write(self, action):
        if True:
            return # disabled for now...
        tb_name = 'RetopoFlow_instrumentation'
        if tb_name not in bpy.data.texts:
            bpy.data.texts.new(tb_name)
        tb = bpy.data.texts[tb_name]

        target_json = self.rftarget.to_json()
        data = {'action': action, 'target': target_json}
        data_str = json.dumps(data, separators=[',', ':'])

        # write data to end of textblock
        tb.write('')        # position cursor to end
        tb.write(data_str)
        tb.write('\n')
