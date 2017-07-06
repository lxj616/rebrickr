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
from .mesh_generate import *
from .common_functions import *
from mathutils import Vector, geometry
from mathutils.bvhtree import BVHTree
props = bpy.props

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

def confirmList(objList):
    """ if single object passed, convert to list """
    if type(objList) != list:
        objList = [objList]
    return objList

def getBrickSettings():
    """ returns dictionary containing brick detail settings """
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    settings = {}
    settings["underside"] = cm.undersideDetail
    settings["logo"] = cm.logoDetail
    settings["numStudVerts"] = cm.studVerts
    return settings

def make1x1(dimensions, refLogo, scale="1x2", name='brick1x1'):
    """ create unlinked 1x1 LEGO Brick at origin """
    settings = getBrickSettings()
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]

    bm = bmesh.new()
    brickBM = makeBrick(dimensions=dimensions, brickSize=[1,1], numStudVerts=settings["numStudVerts"], detail=cm.undersideDetail)
    studInset = dimensions["thickness"] * 0.9
    cylinderBM = makeCylinder(r=dimensions["stud_radius"], N=settings["numStudVerts"], h=dimensions["stud_height"]+studInset, co=(0,0,dimensions["stud_offset"]-(studInset/2)), botFace=False)
    if refLogo:
        logoBM = bmesh.new()
        logoBM.from_mesh(refLogo.data)
        lw = dimensions["logo_width"]
        bmesh.ops.scale(logoBM, vec=Vector((lw, lw, lw)), verts=logoBM.verts)
        bmesh.ops.rotate(logoBM, verts=logoBM.verts, cent=(1.0, 0.0, 0.0), matrix=Matrix.Rotation(math.radians(90.0), 3, 'X'))
        bmesh.ops.translate(logoBM, vec=Vector((0, 0, dimensions["logo_offset"])), verts=logoBM.verts)
        # add logoBM mesh to bm mesh
        logoMesh = bpy.data.meshes.new('LEGOizer_tempMesh')
        logoObj = bpy.data.objects.new('LEGOizer_tempObj', logoMesh)
        logoBM.to_mesh(logoMesh)
        if cm.logoResolution < 1:
            scn.objects.link(logoObj)
            select(logoObj, active=logoObj)
            bpy.ops.object.modifier_add(type='DECIMATE')
            logoObj.modifiers['Decimate'].ratio = cm.logoResolution
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier='Decimate')
        bm.from_mesh(logoMesh)
        bpy.data.objects.remove(logoObj, do_unlink=True)
        bpy.data.meshes.remove(logoMesh, do_unlink=True)

    # add brick mesh to bm mesh
    cube = bpy.data.meshes.new('legoizer_cube')
    cylinder = bpy.data.meshes.new('legoizer_cylinder')
    brickBM.to_mesh(cube)
    cylinderBM.to_mesh(cylinder)
    bm.from_mesh(cube)
    bm.from_mesh(cylinder)
    bpy.data.meshes.remove(cube)
    bpy.data.meshes.remove(cylinder)

    # create apply mesh data to 'legoizer_brick1x1' data
    if bpy.data.objects.find(name) == -1:
        brick1x1Mesh = bpy.data.meshes.new(name + 'Mesh')
        brick1x1 = bpy.data.objects.new(name, brick1x1Mesh)
    else:
        brick1x1 = bpy.data.objects[name]
    bm.to_mesh(brick1x1.data)

    # return 'legoizer_brick1x1' object
    return brick1x1

def getBrickDimensions(height, gap_percentage):
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

def is_inside(face, co):
    return bmesh.geometry.intersect_face_point(face, co)

def getMatrix(z, obj, dimensions):
    # get obj mesh details
    source_details = bounds(obj)
    # initialize variables
    # xScale = math.floor((source_details.x.distance * obj.scale[0])/dimensions["width"])
    # yScale = math.floor((source_details.y.distance * obj.scale[1])/dimensions["width"])
    xScale = math.floor((source_details.x.distance)/dimensions["width"])
    yScale = math.floor((source_details.y.distance)/dimensions["width"])
    matrix = [[None for y in range(yScale+1)] for x in range(xScale+1)]
    # set matrix values
    for x in range(xScale+1):
        for y in range(yScale+1):
            xLoc = ((x)/(xScale/2)) + source_details.x.min# * obj.matrix_world)
            yLoc = ((y)/(yScale/2)) + source_details.y.min
            matrix[x][y] = (xLoc, yLoc, z)
    return matrix

def add_vertex_to_intersection(e1, e2):
    edges = [e for e in bm.edges if e.select]

    if len(edges) == 2:
        [[v1, v2], [v3, v4]] = [[v.co for v in e.verts] for e in edges]

        iv = geometry.intersect_line_line(v1, v2, v3, v4)
        iv = (iv[0] + iv[1]) / 2
        bm.verts.new(iv)
        bmesh.update_edit_mesh(me)

def ccwz(A,B,C):
    return (C.y-A.y)*(B.x-A.x) > (B.y-A.y)*(C.x-A.x)
def ccwy(A,B,C):
    return (C.z-A.z)*(B.x-A.x) > (B.z-A.z)*(C.x-A.x)
def ccwx(A,B,C):
    return (C.z-A.z)*(B.y-A.y) > (B.z-A.z)*(C.y-A.y)

def intersect(A,B,C,D,axis):
    if axis == "z":
        return ccwz(A,C,D) != ccwz(B,C,D) and ccwz(A,B,C) != ccwz(A,B,D)
    if axis == "y":
        return ccwy(A,C,D) != ccwy(B,C,D) and ccwy(A,B,C) != ccwy(A,B,D)
    if axis == "x":
        return ccwx(A,C,D) != ccwx(B,C,D) and ccwx(A,B,C) != ccwx(A,B,D)

def getIntersectedEdgeVerts(bm_tester, bm_subject, axis="z"):
    intersectedEdgeVerts = []
    for e1 in bm_tester.edges:
        for e2 in bm_subject.edges:
            v1 = e1.verts[0].co
            v2 = e1.verts[1].co
            v3 = e2.verts[0].co
            v4 = e2.verts[1].co
            if intersect(v1, v2, v3, v4, axis):
                for v in e2.verts:
                    intersectedEdgeVerts.append(v.co.to_tuple())
    return intersectedEdgeVerts

def are_inside(verts, bm):
    """
    input:
        points
        - a list of vectors (can also be tuples/lists)
        bm
        - a manifold bmesh with verts and (edge/faces) for which the
          normals are calculated already. (add bm.normal_update() otherwise)
    returns:
        a list
        - a mask lists with True if the point is inside the bmesh, False otherwise
    """

    rpoints = []
    addp = rpoints.append
    bvh = BVHTree.FromBMesh(bm, epsilon=0.0001)

    # return points on polygons
    for vert in verts:
        point = vert.co
        fco, normal, _, _ = bvh.find_nearest(point)
        if fco == None:
            print(":(")
            addp(False)
            continue
        else:
            print("YAYYYYYYY")
        p2 = fco - Vector(point)
        v = p2.dot(normal)
        addp(not v < 0.0)  # addp(v >= 0.0) ?

    return rpoints
def get_points_inside(verts, bm):
    """
    input:
        points
        - a list of vectors (can also be tuples/lists)
        bm
        - a manifold bmesh with verts and (edge/faces) for which the
          normals are calculated already. (add bm.normal_update() otherwise)
    returns:
        a list
        - a mask lists with True if the point is inside the bmesh, False otherwise
    """

    rpoints = []
    addp = rpoints.append
    bvh = BVHTree.FromBMesh(bm, epsilon=0.0001)

    # return points on polygons
    for vert in verts:
        point = vert.co
        fco, normal, _, _ = bvh.find_nearest(point)
        p2 = fco - Vector(point)
        v = p2.dot(normal)
        if not v < 0.0:
            addp(vert)

    return rpoints

def is_inside1(p, obj, max_dist=1.84467e+19):
    mat = obj.matrix_local.inverted()
    try:
        point, normal, face = obj.closest_point_on_mesh(p, max_dist)
    except:
        junkBool, point, normal, face = obj.closest_point_on_mesh(p, max_dist)
    p2 = point-p
    v = p2.dot(normal)
    return not(v < 0.0)

def is_inside(ray_origin, ray_destination, obj):

    # the matrix multiplations and inversions are only needed if you
    # have unapplied transforms, else they could be dropped. but it's handy
    # to have the algorithm take them into account, for generality.
    mat = obj.matrix_local.inverted()
    f = obj.ray_cast(mat * ray_origin, mat * ray_destination)
    try:
        junk, loc, normal, face_idx = f
    except:
        loc, normal, face_idx = f

    if face_idx == -1:
        return False

    max_expected_intersections = 1000
    fudge_distance = 0.0001
    direction = (ray_destination - loc)
    dir_len = direction.length
    amount = fudge_distance / dir_len

    i = 1
    while (face_idx != -1):

        loc = loc.lerp(direction, amount)
        f = obj.ray_cast(mat * loc, mat * ray_destination)
        try:
            junk, loc, normal, face_idx = f
        except:
            loc, normal, face_idx = f
        if face_idx == -1:
            break
        i += 1
        if i > max_expected_intersections:
            break

    if i > 2:
        print(i)
    return (i % 2) != 0

def getInsideVerts(bm_slice, bm_lattice, ignoredVerts, boundingObj=False):
    insideVerts = []
    if len(bm_slice.verts) > 2:
        # points_inside = are_inside(bm_lattice.verts, bm_slice)
        # bm_lattice.verts.ensure_lookup_table()
        # for i in range(len(bm_lattice.verts)):
        #     if points_inside[i] and bm_lattice.verts[i] not in ignoredVerts:
        #         insideVerts.append(v.co.to_tuple())

        # print("numVertsBefore: " + str(len(bm_lattice.verts)))
        # bm_source.faces.new(bm_slice.verts)
        # points_inside = get_points_inside(bm_lattice.verts, bm_slice)
        # for v in points_inside:
        #     if v not in ignoredVerts:
        #         insideVerts.append(v.co.to_tuple())

        for v in bm_lattice.verts:
            if v not in ignoredVerts:
                if is_inside(v.co, Vector((0,0,-2)), boundingObj):
                    # print("yes!")
                    insideVerts.append(v.co.to_tuple())
                else:
                    # print("no :(")
                    pass
    return insideVerts


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

def getCrossSection(source, source_details, dimensions):
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]
    if cm.calculationAxis == "Auto":
        sizes = [source_details.x.distance, source_details.y.distance, source_details.z.distance]
        m = sizes.index(min(sizes))
    elif cm.calculationAxis == "X Axis":
        m = 0
    elif cm.calculationAxis == "Y Axis":
        m = 1
    elif cm.calculationAxis == "Z Axis":
        m = 2
    else:
        print("ERROR: Could not get axis for calculation")
        m = 0
    if m == 0:
        axis = "x"
        lScale = (0, source_details.y.distance, source_details.z.distance)
        numSlices = math.ceil(source_details.x.distance/(dimensions["width"] + dimensions["gap"]))
        CS_slices = slices(source, numSlices, (dimensions["width"] + dimensions["gap"]), axis=axis, drawSlices=False) # get list of horizontal bmesh slices
    if m == 1:
        axis = "y"
        lScale = (source_details.x.distance, 0, source_details.z.distance)
        numSlices = math.ceil(source_details.y.distance/(dimensions["width"] + dimensions["gap"]))
        CS_slices = slices(source, numSlices, (dimensions["width"] + dimensions["gap"]), axis=axis, drawSlices=False) # get list of horizontal bmesh slices
    if m == 2:
        axis = "z"
        lScale = (source_details.x.distance, source_details.y.distance, 0)
        numSlices = math.ceil(source_details.z.distance/(dimensions["height"] + dimensions["gap"]))
        CS_slices = slices(source, numSlices, (dimensions["height"] + dimensions["gap"]), axis=axis, drawSlices=False) # get list of horizontal bmesh slices

    return axis, lScale, CS_slices

def merge(bricks):
    return

def makeBricks(slicesList, refBrick, source, source_details, preHollow=False):
    """ Make bricks """
    scn = bpy.context.scene
    # initialize temporary object
    tempMesh = bpy.data.meshes.new('tempM')
    tempObj = bpy.data.objects.new('temp', tempMesh)

    # # assemble coordinates for each layer into coList
    # coList = []
    # for bm in slices:
    #     drawBMesh(bm)
    #     bm.verts.ensure_lookup_table()
    #     if len(bm.verts) > 2:
    #         z = bm.verts[0].co.z
    #         matrix = getMatrix(z, source, dimensions)
    #         face = bm.faces.new(bm.verts)
    #         for i in range(len(matrix)):
    #             for co in matrix[i]:
    #                 if is_inside(face, co):
    #                     coList.append(co)
    #     else:
    #         # TODO: If the layer has less than three verts, figure out a way to still do the calculations without creating a face
    #         pass
    #
    # bpy.data.objects.remove(tempObj)
    coList = []
    moreCOs = []
    for sl in slicesList:
        slices = sl["slices"]
        lScale = sl["lScale"]
        R = sl["R"]
        axis = sl["axis"]

        # for each slice
        for bm in slices:
            # drawBMesh(bm) # draw the slice (for testing purposes)
            # create lattice bmesh
            # TODO: lattice BM can be created outside of for loop and transformed each time, if that's more efficient
            bm.verts.ensure_lookup_table()
            if axis == "z":
                offset = (source_details.x.mid, source_details.y.mid, bm.verts[0].co.z)
            elif axis == "y":
                offset = (source_details.x.mid, bm.verts[0].co.y, source_details.z.mid)
            else:
                offset = ( bm.verts[0].co.x, source_details.y.mid, source_details.z.mid)
            latticeBM = makeLattice(R, lScale, offset)
            # drawBMesh(latticeBM) # draw the lattice (for testing purposes)
            coListNew = getIntersectedEdgeVerts(bm, latticeBM, axis)
            insideVerts = getInsideVerts(bm, latticeBM, coListNew, source)
            try:
                if lastcoList and lastInsideVerts:
                    pass
            except:
                lastcoList = coListNew
                lastInsideVerts = insideVerts
            if preHollow and len(lastcoList) != 0:
                print(len(insideVerts))
                # bmJunk = bmesh.new()
                # for co in insideVerts:
                #     v2 = bmJunk.verts.new((co))
                #     if axis == "z":
                #         v2.co.z = lastcoList[0][2]
                #     if axis == "y":
                #         v2.co.y = lastcoList[0][1]
                #     else:
                #         v2.co.x = lastcoList[0][0]
                #
                #     if v2.co.to_tuple() not in lastcoList and v2.co.to_tuple() not in lastInsideVerts:
                #         print("yes!")
                #         coListNew.append(co)
            else:
                coList += insideVerts
            print("len(coListNew): " + str(len(coListNew)))
            coList += coListNew
            lastcoList = coListNew
            lastInsideVerts = insideVerts
        coList += insideVerts

    # uniquify coList
    coList = uniquify(coList, lambda x: (round(x[0], 2), round(x[1], 2), round(x[2], 2)))

    # make bricks at determined locations
    bricks = []
    if len(coList) == 0:
        coList.append((source_details.x.mid, source_details.y.mid, source_details.z.mid))
    for i,co in enumerate(coList):
        brickMesh = bpy.data.meshes.new('LEGOizer_brickMesh_' + str(i+1))
        brick = bpy.data.objects.new('LEGOizer_brick_' + str(i+1), brickMesh)
        brick.location = Vector(co)
        brick.data = refBrick.data
        bpy.context.scene.objects.link(brick)
        bricks.append(brick)
    bpy.context.scene.update()
    # add bricks to LEGOizer_bricks group
    select(bricks, active=bricks[0])
    n = scn.cmlist[scn.cmlist_index].source_name
    LEGOizer_bricks = 'LEGOizer_%(n)s_bricks' % locals()
    if not groupExists(LEGOizer_bricks):
        bpy.ops.group.create(name=LEGOizer_bricks)
    else:
        bpy.data.groups.remove(group=bpy.data.groups[LEGOizer_bricks], do_unlink=True)
        bpy.ops.group.create(name=LEGOizer_bricks)
    # return list of created objects
    return bricks
