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
from .lego_mesh_generate import *

class Brick:
    # observable properties

    def __init__(self, location=(0,0,0), name='brick', mesh_data=None):
        if mesh_data:
            self.mesh_data = mesh_data
        else:
            self.mesh_data = bpy.data.meshes.new(name + "_mesh")
        self.obj = bpy.data.objects.new(name, self.mesh_data)
        self.update_location(location)
        self.update_name(name)
        self.onTop = False
        self.brick_dimensions = 'UNSET'

    def update_data(self, mesh_data):
        self.obj.data = mesh_data

    def update_location(self, location):
        self.obj.location = location
        self.location = location

    def update_name(self, name):
        self.obj.name = name
        self.name = name

    def remove(self):
        m = self.obj.data
        bpy.data.objects.remove(self.obj, do_unlink=True)
        bpy.data.meshes.remove(m, do_unlink=True)

    def link_to_scene(self, scene):
        bpy.context.scene.objects.link(self.obj)

    def select_brick(self):
        self.obj.select = True

    def set_brick_height(self, height):
        self.height = height
        # TODO: actually update brick obj height

    @staticmethod
    def get_settings(cm):
        """ returns dictionary containing brick detail settings """
        settings = {}
        settings["underside"] = cm.undersideDetail
        settings["logo"] = cm.logoDetail
        settings["numStudVerts"] = cm.studVerts
        return settings

    @staticmethod
    def get_dimensions(height=1, gap_percentage=0.01):
        scale = height/9.6
        brick_dimensions = {}
        brick_dimensions["height"] = scale*9.6
        brick_dimensions["width"] = scale*8
        brick_dimensions["gap"] = scale*9.6*gap_percentage
        brick_dimensions["stud_height"] = scale*1.8
        brick_dimensions["stud_diameter"] = scale*4.8
        brick_dimensions["stud_radius"] = scale*2.4
        brick_dimensions["stud_offset"] = (brick_dimensions["height"] / 2) + (brick_dimensions["stud_height"] / 2)
        brick_dimensions["thickness"] = scale*1.6
        brick_dimensions["tube_thickness"] = scale * 0.855
        brick_dimensions["logo_width"] = scale*3.74
        brick_dimensions["logo_offset"] = (brick_dimensions["height"] / 2) + (brick_dimensions["stud_height"])
        return brick_dimensions

    def set_dimensions(self, height=1, gap_percentage=0.01):
        self.brick_dimensions = self.get_dimensions(height, gap_percentage)
        return self.brick_dimensions

    def new_brick(self, height=1, type=[1,1], logo=False, name="brick"):
        """ create unlinked LEGO Brick at origin """
        scn = bpy.context.scene
        cm = scn.cmlist[scn.cmlist_index]
        settings = Brick.get_settings(cm)
        self.set_dimensions(height)

        bm = bmesh.new()
        brickBM = makeBrick(dimensions=self.brick_dimensions, brickSize=type, numStudVerts=settings["numStudVerts"], detail=cm.undersideDetail)
        studInset = self.brick_dimensions["thickness"] * 0.9
        if logo:
            logoBM = bmesh.new()
            logoBM.from_mesh(logo.data)
            lw = self.brick_dimensions["logo_width"]
            bmesh.ops.scale(logoBM, vec=Vector((lw, lw, lw)), verts=logoBM.verts)
            bmesh.ops.rotate(logoBM, verts=logoBM.verts, cent=(1.0, 0.0, 0.0), matrix=Matrix.Rotation(math.radians(90.0), 3, 'X'))
            bmesh.ops.translate(logoBM, vec=Vector((0, 0, self.brick_dimensions["logo_offset"])), verts=logoBM.verts)
            # add logoBM mesh to bm mesh
            logoMesh = bpy.data.meshes.new('LEGOizer_tempMesh')
            logoObj = bpy.data.objects.new('LEGOizer_tempObj', logoMesh)
            logoBM.to_mesh(logoMesh)
            if cm.logoResolution < 1:
                dMod = logoObj.modifiers.new('Decimate', type='DECIMATE')
                dMod.ratio = cm.logoResolution
                scn.objects.link(logoObj)
                select(logoObj, active=logoObj)
                bpy.ops.object.modifier_apply(apply_as='DATA', modifier='Decimate')
            bm.from_mesh(logoMesh)
            bpy.data.objects.remove(logoObj, do_unlink=True)
            bpy.data.meshes.remove(logoMesh, do_unlink=True)

        # add brick mesh to bm mesh
        cube = bpy.data.meshes.new('legoizer_cube')
        brickBM.to_mesh(cube)
        bm.from_mesh(cube)
        bpy.data.meshes.remove(cube)

        # create apply mesh data to 'legoizer_brick1x1' data
        brick1x1Mesh = bpy.data.meshes.new(name + 'Mesh')
        bm.to_mesh(brick1x1Mesh)
        self.update_data(brick1x1Mesh)

        # return updated brick object
        return self.obj
