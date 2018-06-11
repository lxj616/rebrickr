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
# NONE!

# Blender imports
import bpy
from bpy.props import *

# Addon imports
# NONE!

# Create custom property group
class Bricker_RigidBodySettings(bpy.types.PropertyGroup):
    angular_damping = FloatProperty()
    collision_groups = BoolVectorProperty(size=20)
    collision_margin = FloatProperty()
    collision_shape = StringProperty()
    deactivate_angular_velocity = FloatProperty()
    deactivate_linear_velocity = FloatProperty()
    enabled = BoolProperty()
    friction = FloatProperty()
    kinematic = BoolProperty()
    linear_damping = FloatProperty()
    mass = FloatProperty()
    mesh_source = StringProperty()
    restitution = FloatProperty()
    type = StringProperty()
    use_deactivation = BoolProperty()
    use_deform = BoolProperty()
    use_margin = BoolProperty()
    use_start_deactivated = BoolProperty()


def getRigidBodyProperties():
    return ["angular_damping", "collision_groups", "collision_margin", "collision_shape", "deactivate_angular_velocity", "deactivate_linear_velocity", "enabled", "friction", "kinematic", "linear_damping", "mass", "mesh_source", "restitution", "type", "use_deactivation", "use_deform", "use_margin", "use_start_deactivated"]


def storeRigidBodySettings(obj):
    settings = getRigidBodyProperties()
    for attr in settings:
        setattr(obj.rigid_body_settings, attr, getattr(obj.rigid_body, attr))

def retrieveRigidBodySettings(obj):
    settings = getRigidBodyProperties()
    for attr in settings:
        setattr(obj.rigid_body, attr, getattr(obj.rigid_body_settings, attr))
