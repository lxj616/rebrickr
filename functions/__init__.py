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
import math
from .crossSection import slices, drawBMesh
from .meshGenerate import *
from mathutils import Vector
props = bpy.props

def stopWatch(text, value):
    '''From seconds to Days;Hours:Minutes;Seconds'''

    valueD = (((value/365)/24)/60)
    Days = int(valueD)

    valueH = (valueD-Days)*365
    Hours = int(valueH)

    valueM = (valueH - Hours)*24
    Minutes = int(valueM)

    valueS = (valueM - Minutes)*60
    Seconds = int(valueS)

    # valueMs = (valueS - Seconds)*60
    # Miliseconds = int(valueMs)
    #
    print(str(text) + ": " + str(Days) + ";" + str(Hours) + ":" + str(Minutes) + ";" + str(Seconds)) # + ";;" + str(Miliseconds))

def writeBinvox(obj):
    ''' creates binvox file and returns filepath '''

    scn = bpy.context.scene
    binvoxPath = props.binvoxPath
    projectName = bpy.path.display_name_from_filepath(bpy.data.filepath).replace(" ", "_")

    # export obj to obj_exports_folder
    objExportPath = None # TODO: Write this code

    # send
    resolution = props.voxelResolution
    outputFilePath = props.final_output_folder + "/" + projectName + "_" + scn.voxelResolution + ".obj"
    binvoxCall = "'%(binvoxPath)s' -pb -d %(resolution)s '%(objExportPath)s'" % locals()

    subprocess.call()

    return binvoxPath

def groupExists(groupName):
    """ check if group exists in blender's memory """

    groupExists = False
    for group in bpy.data.groups:
        if group.name == groupName:
            groupExists = True
    return groupExists

def deselectAll():
    bpy.ops.object.select_all(action='DESELECT')
def selectAll():
    bpy.ops.object.select_all(action='SELECT')

def confirmList(objList):
    """ if single object passed, convert to list """
    if type(objList) != list:
        objList = [objList]
    return objList

def hide(objList):
    objList = confirmList(objList)
    for obj in objList:
        obj.hide = True
def unhide(objList):
    objList = confirmList(objList)
    for obj in objList:
        obj.hide = False

def select(objList=[], active=None, action="select", exclusive=True):
    """ selects objs in list and deselects the rest """
    objList = confirmList(objList)
    try:
        if action == "select":
            # deselect all if selection is exclusive
            if exclusive and len(objList) > 0:
                deselectAll()
            # select objects in list
            for obj in objList:
                obj.select = True
        elif action == "deselect":
            # deselect objects in list
            for obj in objList:
                obj.select = False

        # set active object
        if active:
            try:
                bpy.context.scene.objects.active = active
            except:
                print("argument passed to 'active' parameter not valid (" + str(active) + ")")
    except:
        return False
    return True

def delete(objs):
    if select(objs):
        unhide(objs)
        bpy.ops.object.delete()

def getBrickDimensions(height):
    scale = height/9.6
    brick_dimensions = {}
    brick_dimensions["height"] = scale*9.6
    brick_dimensions["width"] = scale*8
    brick_dimensions["stud_height"] = scale*1.8
    brick_dimensions["stud_diameter"] = scale*4.8
    brick_dimensions["stud_radius"] = scale*2.4
    brick_dimensions["stud_offset"] = (brick_dimensions["height"] / 2) + (brick_dimensions["stud_height"] / 2)
    brick_dimensions["logo_width"] = scale*3.74
    brick_dimensions["logo_offset"] = (brick_dimensions["height"] / 2) + (brick_dimensions["stud_height"])
    return brick_dimensions

def bounds(obj, local=False):

    local_coords = obj.bound_box[:]
    om = obj.matrix_world

    if not local:
        worldify = lambda p: om * Vector(p[:])
        coords = [worldify(p).to_tuple() for p in local_coords]
    else:
        coords = [p[:] for p in local_coords]

    rotated = zip(*coords[::-1])

    push_axis = []
    for (axis, _list) in zip('xyz', rotated):
        info = lambda: None
        info.max = max(_list)
        info.min = min(_list)
        info.distance = info.max - info.min
        push_axis.append(info)

    import collections

    originals = dict(zip(['x', 'y', 'z'], push_axis))

    o_details = collections.namedtuple('object_details', 'x y z')
    return o_details(**originals)

# def is_inside(p, obj):
#     max_dist = 1.84467e+19
#     return bmesh.geometry.intersect_face_point(face, co)

# def getMatrix(z, obj, dimensions):
#     source_details = bounds(obj)
#     xScale = math.floor(source_details.x.distance/dimensions["width"])
#     yScale = math.floor(source_details.y.distance/dimensions["width"])
#     matrix = [[None for x in range(xScale+1)] for y in range(yScale+1)]
#     for x in range(xScale+1):
#         for y in range(yScale+1):
#             xLoc = (((x)/(xScale/2)) + source_details.x.min)
#             yLoc = (((y)/(yScale/2)) + source_details.y.min)
#             # print(xIndex, yIndex)
#             matrix[x][y] = (xLoc, yLoc, z)
#
#     return matrix

# def add_vertex_to_intersection():
#
#     obj = bpy.context.object
#     me = obj.data
#     bm = bmesh.from_edit_mesh(me)
#
#     edges = [e for e in bm.edges if e.select]
#
#     if len(edges) == 2:
#         [[v1, v2], [v3, v4]] = [[v.co for v in e.verts] for e in edges]
#
#         iv = geometry.intersect_line_line(v1, v2, v3, v4)
#         iv = (iv[0] + iv[1]) / 2
#         bm.verts.new(iv)
#         bmesh.update_edit_mesh(me)

def importLogo():
    """ import logo object from legoizer addon folder """
    addonsPath = bpy.utils.user_resource('SCRIPTS', "addons")
    legoizer = props.addon_name
    logoObjPath = "%(addonsPath)s/%(legoizer)s/lego_logo.obj" % locals()
    bpy.ops.import_scene.obj(filepath=logoObjPath)
    logoObj = bpy.context.selected_objects[0]
    return logoObj

def makeBricks(slices, refBrick, dimensions, source):
    """ Make bricks """

    # tempMesh = bpy.data.meshes.new('tempM')
    # tempObj = bpy.data.objects.new('temp', tempMesh)
    #
    # # assemble coordinates for each layer into coList
    # coList = []
    # for bm in slices:
    #     drawBMesh(bm)
    #     bm.verts.ensure_lookup_table()
    #     z = bm.verts[0].co.z
    #     matrix = getMatrix(z, source, dimensions)
    #     face = bm.faces.new(bm.verts)
    #     for i in range(len(matrix)):
    #         for co in matrix[i]:
    #             # if bmesh.geometry.intersect_face_point(face, co):
    #             #     coList.append(co)
    #             # is_inside(Vector(j),tempObj)
    #
    #
    # bpy.data.objects.remove(tempObj)

    # make bricks at determined locations
    bricks = []
    coList = [(0.1,0.1,0.1),(-0.1,-0.1,-0.1)]
    for i,co in enumerate(coList):
        brickMesh = bpy.data.meshes.new('LEGOizer_brickMesh_' + str(i+1))
        brick = bpy.data.objects.new('LEGOizer_brick_' + str(i+1), brickMesh)
        brick.location = Vector(co)
        brick.data = refBrick.data
        bpy.context.scene.objects.link(brick)
        bricks.append(brick)
    bpy.context.scene.update()
    # add bricks to 'LEGOizer_bricks' group
    select(bricks)
    if not groupExists('LEGOizer_bricks'):
        bpy.ops.group.create(name='LEGOizer_bricks')
    else:
        bpy.data.groups.remove(group=bpy.data.groups['LEGOizer_bricks'], do_unlink=True)
        bpy.ops.group.create(name='LEGOizer_bricks')
    # return list of created objects
    return bricks
