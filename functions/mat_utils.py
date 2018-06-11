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

def clearExistingMaterials(obj, from_idx=0, from_data=False):
    if from_data:
        brick.data.materials.clear(1)
    else:
        select(obj, active=True)
        obj.active_material_index = from_idx
        for i in range(from_idx, len(obj.material_slots)):
            # remove material slots
            bpy.ops.object.material_slot_remove()

def addMaterial(obj, mat, to_data=False):
    obj.data.materials.append(mat)
    if not to_data:
        obj.material_slots[-1].link = 'OBJECT'
        obj.material_slots[-1].material = mat
