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
import bmesh
import random
from mathutils import Vector, Matrix
from .lego_mesh_generate import *
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
    def new_mesh(dimensions, name='new_brick', gap_percentage=0.01, type=[1,1,3], transform=False, logo=False, undersideDetail="Flat", stud=True, returnType="mesh", brickMesh=None):
        """ create unlinked LEGO Brick at origin """
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        bm = bmesh.new()
        if cm.brickType == "Plates" or cm.brickType == "Bricks and Plates":
            zScale = 0.33
        elif cm.brickType == "Bricks":
            zScale = 1

        brickBM = makeBrick(dimensions=dimensions, brickSize=type, numStudVerts=cm.studVerts, detail=undersideDetail, stud=stud)
        if logo and stud:
            # get logo rotation angle based on type of brick
            if type[0] == 1 and type[1] == 1:
                zRot = random.randint(0,3) * 90
            elif type[0] == 2 and type[1] > 2:
                zRot = random.randint(0,1) * 180 + 90
            elif type[1] == 2 and type[0] > 2:
                zRot = random.randint(0,1) * 180
            elif type[0] == 2 and type[1] == 2:
                zRot = random.randint(0,1) * 180
            elif type[0] == 1:
                zRot = random.randint(0,1) * 180 + 90
            elif type[1] == 1:
                zRot = random.randint(0,1) * 180
            else:
                print("shouldn't get here")
                print(type)
            for x in range(type[0]):
                for y in range(type[1]):
                    logoBM = bmesh.new()
                    logoBM.from_mesh(logo.data)
                    for f in logoBM.faces:
                        f.smooth = True
                    lw = dimensions["logo_width"]
                    # transform logo into place
                    bmesh.ops.scale(logoBM, vec=Vector((lw, lw, lw)), verts=logoBM.verts)
                    bmesh.ops.rotate(logoBM, verts=logoBM.verts, cent=(1.0, 0.0, 0.0), matrix=Matrix.Rotation(math.radians(90.0), 3, 'X'))
                    # rotate logo around stud
                    if zRot != 0:
                        bmesh.ops.rotate(logoBM, verts=logoBM.verts, cent=(0.0, 0.0, 1.0), matrix=Matrix.Rotation(math.radians(zRot), 3, 'Z'))
                    for v in logoBM.verts:
                        v.co = ((v.co.x + x*(dimensions["width"]+dimensions["gap"])), (v.co.y + y*(dimensions["width"]+dimensions["gap"])), (v.co.z + dimensions["logo_offset"]*0.998))
                    lastLogoBM = logoBM
                    # add logoBM mesh to bm mesh
                    logoMesh = bpy.data.meshes.new('LEGOizer_tempMesh')
                    logoBM.to_mesh(logoMesh)
                    bm.from_mesh(logoMesh)
                    bpy.data.meshes.remove(logoMesh, do_unlink=True)

        # add brick mesh to bm mesh
        cube = bpy.data.meshes.new('legoizer_cube')
        brickBM.to_mesh(cube)
        bm.from_mesh(cube)
        bpy.data.meshes.remove(cube)

        if transform:
            for v in bm.verts:
                v.co = (v.co[0] + transform[0], v.co[1] + transform[1], v.co[2] + transform[2])

        if returnType == "mesh":
            # create apply mesh data to 'legoizer_brick1x1' data
            if not brickMesh:
                brickMesh = bpy.data.meshes.new(name + 'Mesh')
            bm.to_mesh(brickMesh)
            # return updated brick object
            return brickMesh
        else:
            # return bmesh object
            return bm

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
        brick_dimensions["thickness"] = round(scale*1.6, 8)
        brick_dimensions["tube_thickness"] = round(scale*0.855, 8)
        brick_dimensions["bar_radius"] = round(scale*1.6, 8)
        brick_dimensions["logo_width"] = round(scale*3.74, 8)
        brick_dimensions["support_width"] = round(scale*0.8, 8)
        brick_dimensions["tick_width"] = round(scale*0.6, 8)
        brick_dimensions["tick_depth"] = round(scale*0.3, 8)
        brick_dimensions["support_height"] = round(brick_dimensions["height"]*0.65, 8)

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
