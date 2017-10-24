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
import bpy
import bmesh
import random
import time
import numpy as np

# Blender imports
from mathutils import Vector, Matrix

# Rebrickr imports
from .brick_mesh_generate import *
from ...functions import *

class Bricks:
    def __init__(self):
        self.objects = {}

    def __getitem__(self, string):
        return self.objects[string]

    # def new(self, name, location=(0,0,0), mesh_data=None):
    #     self.objects[name] = Brick(location, name, mesh_data)
    #     return self.objects[name]
    #
    def getAllObjs(self):
        brickObjs = []
        for o in self.objects.values():
            brickObjs.append(o.obj)
        return brickObjs

    @staticmethod
    def new_mesh(dimensions, type=[1,1,3], logo=False, all_vars=False, logo_type=None, logo_details=None, logo_scale=None, logo_resolution=None, logo_inset=None, undersideDetail="Flat", stud=True, numStudVerts=None):
        """ create unlinked Brick at origin """

        bm = bmesh.new()

        brickBM = makeBrick(dimensions=dimensions, brickSize=type, numStudVerts=numStudVerts, detail=undersideDetail, stud=stud)
        if logo and stud:
            # get logo rotation angle based on type of brick
            rot_mult = 180
            rot_vars = 2
            rot_add = 0
            if type[0] == 1 and type[1] == 1:
                rot_mult = 90
                rot_vars = 4
            elif type[0] == 2 and type[1] > 2:
                rot_add = 90
            elif type[1] == 2 and type[0] > 2:
                pass
            elif type[0] == 2 and type[1] == 2:
                pass
            elif type[0] == 1:
                rot_add = 90
            # set zRot to random rotation angle
            if all_vars:
                zRots = []
                for i in range(rot_vars):
                    zRots.append(i * rot_mult + rot_add)
            else:
                randomSeed = int(time.time()*10**6) % 10000
                randS0 = np.random.RandomState(randomSeed)
                zRots = [randS0.randint(0,rot_vars) * rot_mult + rot_add]
            lw = dimensions["logo_width"] * logo_scale
            logoBM_ref = bmesh.new()
            logoBM_ref.from_mesh(logo.data)
            if logo_type == "LEGO Logo":
                # smooth faces
                for f in logoBM_ref.faces:
                    f.smooth = True
                # transform logo into place
                bmesh.ops.scale(logoBM_ref, vec=Vector((lw, lw, lw)), verts=logoBM_ref.verts)
                bmesh.ops.rotate(logoBM_ref, verts=logoBM_ref.verts, cent=(1.0, 0.0, 0.0), matrix=Matrix.Rotation(math.radians(90.0), 3, 'X'))
            else:
                # transform logo to origin (transform was (or should be at least) applied, origin is at center)
                xOffset = logo_details.x.mid
                yOffset = logo_details.y.mid
                zOffset = logo_details.z.mid
                for v in logoBM_ref.verts:
                    v.co.x -= xOffset
                    v.co.y -= yOffset
                    v.co.z -= zOffset
                    v.select = True
                # scale logo
                distMax = max(logo_details.x.distance, logo_details.y.distance)
                bmesh.ops.scale(logoBM_ref, vec=Vector((lw/distMax, lw/distMax, lw/distMax)), verts=logoBM_ref.verts)

            bms = []
            for zRot in zRots:
                bm_cur = bm.copy()
                for x in range(type[0]):
                    for y in range(type[1]):
                        logoBM = logoBM_ref.copy()
                        # rotate logo around stud
                        if zRot != 0:
                            bmesh.ops.rotate(logoBM, verts=logoBM.verts, cent=(0.0, 0.0, 1.0), matrix=Matrix.Rotation(math.radians(zRot), 3, 'Z'))
                        # transform logo to appropriate position
                        zOffset = dimensions["logo_offset"]
                        if logo_type != "LEGO Logo" and logo_details is not None:
                            zOffset += ((logo_details.z.distance * (lw/distMax)) / 2) * (1-(logo_inset * 2))
                        xyOffset = dimensions["width"]+dimensions["gap"]
                        for v in logoBM.verts:
                            v.co = ((v.co.x + x*(xyOffset)), (v.co.y + y*(xyOffset)), (v.co.z + zOffset))
                        # add logoBM mesh to bm mesh
                        junkMesh = bpy.data.meshes.new('Rebrickr_junkMesh')
                        logoBM.to_mesh(junkMesh)
                        bm_cur.from_mesh(junkMesh)
                        bpy.data.meshes.remove(junkMesh, do_unlink=True)
                bms.append(bm_cur)
        else:
            bms = [bm]

        # add brick mesh to bm mesh
        junkMesh = bpy.data.meshes.new('Rebrickr_junkMesh')
        brickBM.to_mesh(junkMesh)
        for bm in bms:
            bm.from_mesh(junkMesh)
        bpy.data.meshes.remove(junkMesh, do_unlink=True)

        # return bmesh objects
        return bms

    @staticmethod
    def get_dimensions(height=1, zScale=1, gap_percentage=0.01):
        scale = height/9.6
        brick_dimensions = {}
        brick_dimensions["height"] = round(scale*9.6*zScale, 8)
        brick_dimensions["width"] = round(scale*8, 8)
        brick_dimensions["gap"] = round(scale*9.6*gap_percentage, 8)
        brick_dimensions["stud_height"] = round(scale*1.8, 8)
        brick_dimensions["stud_diameter"] = round(scale*4.8, 8)
        brick_dimensions["stud_radius"] = round(scale*2.4, 8)
        brick_dimensions["stud_offset"] = round((brick_dimensions["height"] / 2) + (brick_dimensions["stud_height"] / 2), 8)
        brick_dimensions["stud_offset_triple"] = round(((brick_dimensions["height"]*3) / 2) + (brick_dimensions["stud_height"] / 2), 8)
        brick_dimensions["thickness"] = round(scale*1.6, 8)
        brick_dimensions["tube_thickness"] = round(scale*0.855, 8)
        brick_dimensions["bar_radius"] = round(scale*1.6, 8)
        brick_dimensions["logo_width"] = round(scale*4.8, 8) # originally round(scale*3.74, 8)
        brick_dimensions["support_width"] = round(scale*0.8, 8)
        brick_dimensions["tick_width"] = round(scale*0.6, 8)
        brick_dimensions["tick_depth"] = round(scale*0.3, 8)
        brick_dimensions["support_height"] = round(brick_dimensions["height"]*0.65, 8)
        brick_dimensions["support_height_triple"] = round((brick_dimensions["height"]*3)*0.65, 8)

        brick_dimensions["logo_offset"] = round((brick_dimensions["height"] / 2) + (brick_dimensions["stud_height"]), 8)
        return brick_dimensions
#
# class Brick:
#
#     def __init__(self, location=(0,0,0), name="brick", mesh_data=None):
#         # if mesh_data:
#         #     self.mesh_data = mesh_data
#         # else:
#         #     self.mesh_data = bpy.data.meshes.new(name + "_mesh")
#         # self.obj = bpy.data.objects.new(name, self.mesh_data)
#         # self.update_location(location)
#         # self.update_name(name)
#         # self.brick_dimensions = 'UNSET'
#         pass
#
#     def update_data(self, mesh_data):
#         self.obj.data = mesh_data
#
#     def update_location(self, location):
#         self.obj.location = location
#         self.location = location
#
#     def update_name(self, name):
#         self.obj.name = name
#         self.name = name
#
#     def remove(self):
#         m = self.obj.data
#         bpy.data.objects.remove(self.obj, do_unlink=True)
#         bpy.data.meshes.remove(m, do_unlink=True)
#
#     def link_to_scene(self, scene):
#         bpy.context.scene.objects.link(self.obj)
#
#     def link_to_group(self, group):
#         group.objects.link(self.obj)
#
#     def obj_select(self):
#         self.obj.select = True
#
#     def set_height(self, height):
#         self.height = height
#         # TODO: actually update brick obj height
#
#     @staticmethod
#     def get_settings(cm):
#         """ returns dictionary containing brick detail settings """
#         settings = {}
#         # settings["underside"] = cm.undersideDetail
#         settings["logo"] = cm.logoDetail
#         settings["numStudVerts"] = cm.studVerts
#         return settings
#
#     def get_dimensions(self):
#         return self.brick_dimensions
#
#     def set_dimensions(self, height=1, zScale=1, gap_percentage=0.01):
#         self.brick_dimensions = Bricks.get_dimensions(height, zScale, gap_percentage)
#         return self.brick_dimensions
