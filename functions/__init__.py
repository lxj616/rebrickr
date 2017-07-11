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
from copy import copy, deepcopy
from .crossSection import slices, drawBMesh
from .common_mesh_generate import *
from .common_functions import *
from .binvox_rw import *
from ..classes.Brick import Bricks
from mathutils import Matrix, Vector, geometry
from mathutils.bvhtree import BVHTree
props = bpy.props

# def writeBinvox(obj):
#     ''' creates binvox file and returns filepath '''
#
#     scn = bpy.context.scene
#     binvoxPath = props.binvoxPath
#     projectName = bpy.path.display_name_from_filepath(bpy.data.filepath).replace(" ", "_")
#
#     # export obj to obj_exports_folder
#     objExportPath = None # TODO: Write this code
#
#     # send
#     resolution = props.voxelResolution
#     outputFilePath = props.final_output_folder + "/" + projectName + "_" + scn.voxelResolution + ".obj"
#     binvoxCall = "'%(binvoxPath)s' -pb -d %(resolution)s '%(objExportPath)s'" % locals()
#
#     subprocess.call()
#
#     return binvoxPath
#
def confirmList(objList):
    """ if single object passed, convert to list """
    if type(objList) != list:
        objList = [objList]
    return objList

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
        info.mid = (info.min + info.max) / 2
        info.distance = info.max - info.min
        push_axis.append(info)

    import collections

    originals = dict(zip(['x', 'y', 'z'], push_axis))

    o_details = collections.namedtuple('object_details', 'x y z')
    return o_details(**originals)

# def is_inside(face, co):
#     return bmesh.geometry.intersect_face_point(face, co)
#
# def getMatrix(z, obj, dimensions):
#     # get obj mesh details
#     source_details = bounds(obj)
#     # initialize variables
#     # xScale = math.floor((source_details.x.distance * obj.scale[0])/dimensions["width"])
#     # yScale = math.floor((source_details.y.distance * obj.scale[1])/dimensions["width"])
#     xScale = math.floor((source_details.x.distance)/dimensions["width"])
#     yScale = math.floor((source_details.y.distance)/dimensions["width"])
#     matrix = [[None for y in range(yScale+1)] for x in range(xScale+1)]
#     # set matrix values
#     for x in range(xScale+1):
#         for y in range(yScale+1):
#             xLoc = ((x)/(xScale/2)) + source_details.x.min# * obj.matrix_world)
#             yLoc = ((y)/(yScale/2)) + source_details.y.min
#             matrix[x][y] = (xLoc, yLoc, z)
#     return matrix
#
# def add_vertex_to_intersection(e1, e2):
#     edges = [e for e in bm.edges if e.select]
#
#     if len(edges) == 2:
#         [[v1, v2], [v3, v4]] = [[v.co for v in e.verts] for e in edges]
#
#         iv = geometry.intersect_line_line(v1, v2, v3, v4)
#         iv = (iv[0] + iv[1]) / 2
#         bm.verts.new(iv)
#         bmesh.update_edit_mesh(me)
#
# def ccwz(A,B,C):
#     return (C.y-A.y)*(B.x-A.x) > (B.y-A.y)*(C.x-A.x)
# def ccwy(A,B,C):
#     return (C.z-A.z)*(B.x-A.x) > (B.z-A.z)*(C.x-A.x)
# def ccwx(A,B,C):
#     return (C.z-A.z)*(B.y-A.y) > (B.z-A.z)*(C.y-A.y)
#
# def intersect(A,B,C,D,axis):
#     if axis == "z":
#         return ccwz(A,C,D) != ccwz(B,C,D) and ccwz(A,B,C) != ccwz(A,B,D)
#     if axis == "y":
#         return ccwy(A,C,D) != ccwy(B,C,D) and ccwy(A,B,C) != ccwy(A,B,D)
#     if axis == "x":
#         return ccwx(A,C,D) != ccwx(B,C,D) and ccwx(A,B,C) != ccwx(A,B,D)
#
# def getIntersectedEdgeVerts(bm_tester, bm_subject, axis="z"):
#     intersectedEdgeVerts = []
#     for e1 in bm_tester.edges:
#         for e2 in bm_subject.edges:
#             v1 = e1.verts[0].co
#             v2 = e1.verts[1].co
#             v3 = e2.verts[0].co
#             v4 = e2.verts[1].co
#             if intersect(v1, v2, v3, v4, axis):
#                 for v in e2.verts:
#                     intersectedEdgeVerts.append(v.co.to_tuple())
#     return intersectedEdgeVerts
#
# def are_inside(verts, bm):
#     """
#     input:
#         points
#         - a list of vectors (can also be tuples/lists)
#         bm
#         - a manifold bmesh with verts and (edge/faces) for which the
#           normals are calculated already. (add bm.normal_update() otherwise)
#     returns:
#         a list
#         - a mask lists with True if the point is inside the bmesh, False otherwise
#     """
#
#     rpoints = []
#     addp = rpoints.append
#     bvh = BVHTree.FromBMesh(bm, epsilon=0.0001)
#
#     # return points on polygons
#     for vert in verts:
#         point = vert.co
#         fco, normal, _, _ = bvh.find_nearest(point)
#         if fco == None:
#             print(":(")
#             addp(False)
#             continue
#         else:
#             print("YAYYYYYYY")
#         p2 = fco - Vector(point)
#         v = p2.dot(normal)
#         addp(not v < 0.0)  # addp(v >= 0.0) ?
#
#     return rpoints
# def get_points_inside(verts, bm):
#     """
#     input:
#         points
#         - a list of vectors (can also be tuples/lists)
#         bm
#         - a manifold bmesh with verts and (edge/faces) for which the
#           normals are calculated already. (add bm.normal_update() otherwise)
#     returns:
#         a list
#         - a mask lists with True if the point is inside the bmesh, False otherwise
#     """
#
#     rpoints = []
#     addp = rpoints.append
#     bvh = BVHTree.FromBMesh(bm, epsilon=0.0001)
#
#     # return points on polygons
#     for vert in verts:
#         point = vert.co
#         fco, normal, _, _ = bvh.find_nearest(point)
#         p2 = fco - Vector(point)
#         v = p2.dot(normal)
#         if not v < 0.0:
#             addp(vert)
#
#     return rpoints
#
# def is_inside1(p, obj, max_dist=1.84467e+19):
#     mat = obj.matrix_local.inverted()
#     try:
#         point, normal, face = obj.closest_point_on_mesh(p, max_dist)
#     except:
#         junkBool, point, normal, face = obj.closest_point_on_mesh(p, max_dist)
#     p2 = point-p
#     v = p2.dot(normal)
#     return not(v < 0.0)
#
# def is_inside(ray_origin, ray_destination, obj):
#
#     # the matrix multiplations and inversions are only needed if you
#     # have unapplied transforms, else they could be dropped. but it's handy
#     # to have the algorithm take them into account, for generality.
#     mat = obj.matrix_local.inverted()
#     f = obj.ray_cast(mat * ray_origin, mat * ray_destination)
#     try:
#         junk, loc, normal, face_idx = f
#     except:
#         loc, normal, face_idx = f
#
#     if face_idx == -1:
#         return False
#
#     max_expected_intersections = 1000
#     fudge_distance = 0.0001
#     direction = (ray_destination - loc)
#     dir_len = direction.length
#     amount = fudge_distance / dir_len
#
#     i = 1
#     while (face_idx != -1):
#
#         loc = loc.lerp(direction, amount)
#         f = obj.ray_cast(mat * loc, mat * ray_destination)
#         try:
#             junk, loc, normal, face_idx = f
#         except:
#             loc, normal, face_idx = f
#         if face_idx == -1:
#             break
#         i += 1
#         if i > max_expected_intersections:
#             break
#
#     return (i % 2) != 0
#
# def getInsideVerts(bm_slice, bm_lattice, ignoredVerts, boundingObj=False):
#     insideVerts = []
#     if len(bm_slice.verts) > 2:
#         # points_inside = are_inside(bm_lattice.verts, bm_slice)
#         # bm_lattice.verts.ensure_lookup_table()
#         # for i in range(len(bm_lattice.verts)):
#         #     if points_inside[i] and bm_lattice.verts[i] not in ignoredVerts:
#         #         insideVerts.append(v.co.to_tuple())
#
#         # print("numVertsBefore: " + str(len(bm_lattice.verts)))
#         # bm_source.faces.new(bm_slice.verts)
#         # points_inside = get_points_inside(bm_lattice.verts, bm_slice)
#         # for v in points_inside:
#         #     if v not in ignoredVerts:
#         #         insideVerts.append(v.co.to_tuple())
#
#         for v in bm_lattice.verts:
#             if v not in ignoredVerts:
#                 if is_inside(v.co, Vector((0,0,-2)), boundingObj):
#                     # print("yes!")
#                     insideVerts.append(v.co.to_tuple())
#                 else:
#                     # print("no :(")
#                     pass
#     return insideVerts


def addItemToCMList(name="New Model"):
    scn = bpy.context.scene
    item = scn.cmlist.add()
    item.id = len(scn.cmlist)
    scn.cmlist_index = (len(scn.cmlist)-1)
    if bpy.context.active_object == None:
        item.source_name = ""
    else:
        item.source_name = bpy.context.active_object.name # assign name of selected object
    item.name = name
    return True

def importLogo():
    """ import logo object from legoizer addon folder """
    addonsPath = bpy.utils.user_resource('SCRIPTS', "addons")
    legoizer = props.addon_name
    logoObjPath = "%(addonsPath)s/%(legoizer)s/lego_logo.obj" % locals()
    bpy.ops.import_scene.obj(filepath=logoObjPath)
    logoObj = bpy.context.selected_objects[0]
    return logoObj
#
# def getCrossSection(source, source_details, dimensions):
#     scn = bpy.context.scene
#     cm = scn.cmlist[scn.cmlist_index]
#     if cm.calculationAxis == "Auto":
#         sizes = [source_details.x.distance, source_details.y.distance, source_details.z.distance]
#         m = sizes.index(min(sizes))
#     elif cm.calculationAxis == "X Axis":
#         m = 0
#     elif cm.calculationAxis == "Y Axis":
#         m = 1
#     elif cm.calculationAxis == "Z Axis":
#         m = 2
#     else:
#         print("ERROR: Could not get axis for calculation")
#         m = 0
#     lScale = (source_details.x.distance, source_details.y.distance, source_details.z.distance)
#     if m == 0:
#         axis = "x"
#         # lScale = (0, source_details.y.distance, source_details.z.distance)
#         numSlices = math.ceil(source_details.x.distance/(dimensions["width"] + dimensions["gap"]))
#         CS_slices = slices(source, numSlices, (dimensions["width"] + dimensions["gap"]), axis=axis, drawSlices=False) # get list of horizontal bmesh slices
#     if m == 1:
#         axis = "y"
#         # lScale = (source_details.x.distance, 0, source_details.z.distance)
#         numSlices = math.ceil(source_details.y.distance/(dimensions["width"] + dimensions["gap"]))
#         CS_slices = slices(source, numSlices, (dimensions["width"] + dimensions["gap"]), axis=axis, drawSlices=False) # get list of horizontal bmesh slices
#     if m == 2:
#         axis = "z"
#         # lScale = (source_details.x.distance, source_details.y.distance, 0)
#         numSlices = math.ceil(source_details.z.distance/(dimensions["height"] + dimensions["gap"]))
#         CS_slices = slices(source, numSlices, (dimensions["height"] + dimensions["gap"]), axis=axis, drawSlices=False) # get list of horizontal bmesh slices
#
#     return axis, lScale, CS_slices

def merge(bricks):
    return

# R = resolution, s = 3D scale tuple, o = offset lattice center from origin
def generateLattice(R, s, o=(0,0,0)):
    # TODO: Raise exception if R is less than 2
    bme = bmesh.new()
    # initialize variables
    coordMatrix = []
    xR = R[0]
    yR = R[1]
    zR = R[2]
    xS = s[0]
    yS = s[1]
    zS = s[2]
    xL = int(round((xS)/xR))+1
    if xL != 1: xL += 1
    yL = int(round((yS)/yR))+1
    if yL != 1: yL += 1
    zL = int(round((zS)/zR))+1
    if zL != 1: zL += 1
    # iterate through x,y,z dimensions and create verts/connect with edges
    for x in range(xL):
        coordList1 = []
        xCO = (x-(xS/(2*xR)))*xR
        for y in range(yL):
            coordList2 = []
            yCO = (y-(yS/(2*yR)))*yR
            for z in range(zL):
                # create verts
                zCO = (z-(zS/(2*zR)))*zR
                p = (xCO, yCO, zCO)
                v = bme.verts.new(tupleAdd(p, o))
                coordList2.append(v.co.copy())
                # create new edge parallel x axis
                # if z != 0:
                #     e = bme.edges.new((coordList2[z], coordList2[z-1]))
            coordList1.append(coordList2)
            # if y != 0:
            #     for z in range(zL):
            #         e = bme.edges.new((coordList1[y][z], coordList1[y-1][z]))
        coordMatrix.append(coordList1)
        # if x != 0:
        #     for y in range(yL):
        #         for z in range(zL):
        #             e = bme.edges.new((vertMatrix[x][y][z], vertMatrix[x-1][y][z]))
    # return bmesh
    return coordMatrix

def getBrickMatrix(sourceBM, coordMatrix):
    brickFreqMatrix = [[[0 for _ in range(len(coordMatrix[0][0]))] for _ in range(len(coordMatrix[0]))] for _ in range(len(coordMatrix))]
    bm = bmesh.new()
    for x in range(len(coordMatrix)):
        for y in range(len(coordMatrix[x])):
            for z in range(len(coordMatrix[x][y])):
                orig = coordMatrix[x][y][z]
                nextVerts = []
                for i in range(3):
                    if i == 0:
                        try:
                            rayEnd = coordMatrix[x+1][y][z]
                        except:
                            continue
                    elif i == 1:
                        try:
                            rayEnd = coordMatrix[x][y+1][z]
                        except:
                            continue
                    elif i == 2:
                        try:
                            rayEnd = coordMatrix[x][y][z+1]
                        except:
                            continue
                    rayX = rayEnd[0] - orig[0]
                    rayY = rayEnd[1] - orig[1]
                    rayZ = rayEnd[2] - orig[2]
                    ray = Vector((rayX, rayY, rayZ))

                    for f in sourceBM.faces:
                        v1 = f.verts[0].co.copy()
                        v2 = f.verts[1].co.copy()
                        v3 = f.verts[2].co.copy()
                        pointOfIntersection = geometry.intersect_ray_tri(v1, v2, v3, ray, orig)
                        # print(type(pointOfIntersection), pointOfIntersection)
                        if pointOfIntersection:
                            # TODO: calculate this earlier so it doesn't have to be calculated every time
                            edgeLen = (orig - rayEnd).length
                            if i == 0:
                                if (orig - pointOfIntersection).length <= edgeLen:
                                    bm.verts.new(pointOfIntersection)
                                    brickFreqMatrix[x][y][z] += (orig - pointOfIntersection).length/edgeLen
                                    brickFreqMatrix[x+1][y][z] += (rayEnd - pointOfIntersection).length/edgeLen
                            elif i == 1:
                                if (orig - pointOfIntersection).length <= edgeLen:
                                    bm.verts.new(pointOfIntersection)
                                    brickFreqMatrix[x][y][z] += (orig - pointOfIntersection).length/edgeLen
                                    brickFreqMatrix[x][y+1][z] += (rayEnd - pointOfIntersection).length/edgeLen
                            elif i == 2:
                                if (orig - pointOfIntersection).length <= edgeLen:
                                    bm.verts.new(pointOfIntersection)
                                    brickFreqMatrix[x][y][z] += (orig - pointOfIntersection).length/edgeLen
                                    brickFreqMatrix[x][y][z+1] += (rayEnd - pointOfIntersection).length/edgeLen
    # drawBMesh(bm)
    return brickFreqMatrix

def getCOList(brickFreqMatrix, coordMatrix):
    coList = []
    for x in range(len(coordMatrix)):
        for y in range(len(coordMatrix[x])):
            for z in range(len(coordMatrix[x][y])):
                if brickFreqMatrix[x][y][z] > 0:
                    coList.append(coordMatrix[x][y][z])
    return coList

def uniquify3DMatrix(matrix):
    for i in range(len(matrix)):
        for j in range(len(matrix[i])):
            matrix[i][j] = uniquify(matrix[i][j], lambda x: (round(x[0], 2), round(x[1], 2), round(x[2], 2)))
    return matrix

def makeBricks(refBrick, source, source_details, dimensions, R, preHollow=False):
    """ Make bricks """
    scn = bpy.context.scene
    # initialize temporary object
    tempMesh = bpy.data.meshes.new('tempM')
    tempObj = bpy.data.objects.new('temp', tempMesh)

    # get lattice bmesh
    lScale = (source_details.x.distance, source_details.y.distance, source_details.z.distance)
    offset = (source_details.x.mid, source_details.y.mid, source_details.z.mid)
    coordMatrix = generateLattice(R, lScale, offset)
    latticeBM = makeLattice(R, lScale, offset)
    # drawBMesh(makeLattice(R, lScale, offset))
    coordMatrixLast = deepcopy(coordMatrix)
    # coordMatrix = uniquify3DMatrix(coordMatrix)
    # convert source to bmesh and convert faces to tri's
    sourceBM = bmesh.new()
    sourceBM.from_mesh(source.data)
    bmesh.ops.triangulate(sourceBM, faces=sourceBM.faces)
    # select(source)
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
    # get coList from source and lattice intersections
    brickFreqMatrix = getBrickMatrix(sourceBM, coordMatrix)
    # b = bmesh.new()
    # for x in range(len(coordMatrix)):
    #     for y in range(len(coordMatrix[x])):
    #         for z in range(len(coordMatrix[x][y])):
    #             if brickFreqMatrix[x][y][z] == 1:
    #                 b.verts.new(coordMatrix[x][y][z])
    # drawBMesh(b)
    # print(coordMatrixLast == coordMatrix)
    # print(brickFreqMatrix)
    # # print()
    # # print(coordMatrixLast)
    # # print()
    # # print(coordMatrix)
    # # print()
    # print(coordMatrixLast == coordMatrix)
    coList = getCOList(brickFreqMatrix, coordMatrix)

    # for sl in slicesList:
    #     slices = sl["slices"]
    #     lScale = sl["lScale"]
    #     R = sl["R"]
    #     axis = sl["axis"]
    #
    #     # for each slice
    #     latticeBM = makeLattice(R, lScale, offset)
    #     for bm in slices:
    #         drawBMesh(bm) # draw the slice (for testing purposes)
    #         # create lattice bmesh
    #         # TODO: lattice BM can be created outside of for loop and transformed each time, if that's more efficient
    #         bm.verts.ensure_lookup_table()
    #         if axis == "z":
    #             offset = (source_details.x.mid, source_details.y.mid, bm.verts[0].co.z)
    #         elif axis == "y":
    #             offset = (source_details.x.mid, bm.verts[0].co.y, source_details.z.mid)
    #         else:
    #             offset = ( bm.verts[0].co.x, source_details.y.mid, source_details.z.mid)
    #         latticeBM = makeLattice(R, lScale, offset)
    #         drawBMesh(latticeBM) # draw the lattice (for testing purposes)
    #         coListNew = getIntersectedEdgeVerts(bm, latticeBM, axis)
    #         insideVerts = getInsideVerts(bm, latticeBM, coListNew, source)
    #         try:
    #             if lastcoList and lastInsideVerts:
    #                 pass
    #         except:
    #             lastcoList = coListNew
    #             lastInsideVerts = insideVerts
    #         if preHollow and len(lastcoList) != 0:
    #             print(len(insideVerts))
    #             # bmJunk = bmesh.new()
    #             # for co in insideVerts:
    #             #     v2 = bmJunk.verts.new((co))
    #             #     if axis == "z":
    #             #         v2.co.z = lastcoList[0][2]
    #             #     if axis == "y":
    #             #         v2.co.y = lastcoList[0][1]
    #             #     else:
    #             #         v2.co.x = lastcoList[0][0]
    #             #
    #             #     if v2.co.to_tuple() not in lastcoList and v2.co.to_tuple() not in lastInsideVerts:
    #             #         print("yes!")
    #             #         coListNew.append(co)
    #         else:
    #             pass
    #             # coList += insideVerts
    #         print("len(coListNew): " + str(len(coListNew)))
    #         coList += coListNew
    #         lastcoList = coListNew
    #         lastInsideVerts = insideVerts
    #     coList += insideVerts

    # uniquify coList
    coList = uniquify(coList, lambda x: (round(x[0], 2), round(x[1], 2), round(x[2], 2)))

    # create group for lego bricks
    cm = scn.cmlist[scn.cmlist_index]
    n = cm.source_name
    LEGOizer_bricks = 'LEGOizer_%(n)s_bricks' % locals()
    if groupExists(LEGOizer_bricks):
        bpy.data.groups.remove(group=bpy.data.groups[LEGOizer_bricks], do_unlink=True)
    bGroup = bpy.data.groups.new(LEGOizer_bricks)
    # if no coords in coList, add a coord at center of source
    if len(coList) == 0:
        coList.append((source_details.x.mid, source_details.y.mid, source_details.z.mid))
    # make bricks at determined locations
    bricks = Bricks()
    for i,co in enumerate(coList):
        bNum = i + 1
        brick = bricks.new(name='LEGOizer_%(n)s_brick_%(bNum)s' % locals(), location=Vector(co), mesh_data=refBrick.data)
        brick.link_to_scene(scn)
        bGroup.objects.link(brick.obj)

    select(bricks.getAllObjs())

    scn.update()

    # return list of created Brick objects
    return bricks
