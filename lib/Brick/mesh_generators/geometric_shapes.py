import bpy
import bmesh
import math
from mathutils import Vector
from ....functions.common import *


def makeSquare(coord1:Vector, coord2:Vector, face:bool=True, flipNormal:bool=False, bme:bmesh=None):
    """
    create a square with bmesh

    Keyword Arguments:
        coord1     -- back/left/bottom corner of the square (furthest negative in all three axes)
        coord2     -- front/right/top  corner of the square (furthest positive in all three axes)
        face       -- draw face connecting cube verts
        flipNormal -- flip the normals of the cube
        bme        -- bmesh object in which to create verts
    NOTE: if coord1 and coord2 are different on all three axes, z axis will stay consistent at coord1.z

    Returns:
        vList      -- list of vertices with normal facing in positive direction (right hand rule)

    """
    # create new bmesh object
    if bme is None:
        bme = bmesh.new()

    # create square with normal facing +x direction
    if coord1.x == coord2.x:
        v1, v2, v3, v4 = [bme.verts.new((coord1.x, y, z)) for y in [coord1.y, coord2.y] for z in [coord1.z, coord2.z]]
    # create square with normal facing +y direction
    elif coord1.y == coord2.y:
        v1, v2, v3, v4 = [bme.verts.new((x, coord1.y, z)) for x in [coord1.x, coord2.x] for z in [coord1.z, coord2.z]]
    # create square with normal facing +z direction
    else:
        v1, v2, v3, v4 = [bme.verts.new((x, y, coord1.z)) for x in [coord1.x, coord2.x] for y in [coord1.y, coord2.y]]
    vList = [v1, v3, v4, v2]

    # create face
    if face:
        bme.faces.new(vList[::-1] if flipNormal else vList)

    return vList


def makeCube(coord1:Vector, coord2:Vector, sides:list=[False]*6, flipNormals:bool=False, bme:bmesh=None):
    """
    create a cube with bmesh

    Keyword Arguments:
        coord1      -- back/left/bottom corner of the cube (furthest negative in all three axes)
        coord2      -- front/right/top  corner of the cube (furthest positive in all three axes)
        sides       -- draw sides [+z, -z, +x, -x, +y, -y]
        flipNormals -- flip the normals of the cube
        bme         -- bmesh object in which to create verts

    Returns:
        vList       -- list of vertices in the following x,y,z order: [---, -+-, ++-, +--, --+, +-+, +++, -++]

    """

    # ensure coord1 is less than coord2 in all dimensions
    assert coord1.x < coord2.x
    assert coord1.y < coord2.y
    assert coord1.z < coord2.z

    # create new bmesh object
    if bme is None:
        bme = bmesh.new()

    # create vertices
    vList = [bme.verts.new((x, y, z)) for x in [coord1.x, coord2.x] for y in [coord1.y, coord2.y] for z in [coord1.z, coord2.z]]

    # create faces
    v1, v2, v3, v4, v5, v6, v7, v8 = vList
    newFaces = []
    if sides[0]:
        newFaces.append([v6, v8, v4, v2])
    if sides[1]:
        newFaces.append([v3, v7, v5, v1])
    if sides[4]:
        newFaces.append([v4, v8, v7, v3])
    if sides[3]:
        newFaces.append([v2, v4, v3, v1])
    if sides[2]:
        newFaces.append([v8, v6, v5, v7])
    if sides[5]:
        newFaces.append([v6, v2, v1, v5])

    for f in newFaces:
        if flipNormals:
            f.reverse()
        bme.faces.new(f)

    return [v1, v3, v7, v5, v2, v6, v8, v4]


def makeCircle(r:float, N:int, co:Vector=Vector((0,0,0)), face:bool=True, flipNormals:bool=False, bme:bmesh=None):
    """
    create a circle with bmesh

    Keyword Arguments:
        r           -- radius of circle
        N           -- number of verts on circumference
        co          -- coordinate of cylinder's center
        face        -- create face between circle verts
        flipNormals -- flip normals of cylinder
        bme         -- bmesh object in which to create verts

    """
    # create new bmesh object
    if bme is None:
        bme = bmesh.new()

    verts = []

    # create verts around circumference of circle
    for i in range(N):
        x = r * math.cos(((2 * math.pi) / N) * i)
        y = r * math.sin(((2 * math.pi) / N) * i)
        coord = co + Vector((x, y, 0))
        verts.append(bme.verts.new(coord))
    # create face
    if face:
        bme.faces.new(verts if not flipNormals else verts[::-1])

    return verts


def makeCylinder(r:float, h:float, N:int, co:Vector=Vector((0,0,0)), botFace:bool=True, topFace:bool=True, flipNormals:bool=False, bme:bmesh=None):
    """
    create a cylinder with bmesh

    Keyword Arguments:
        r           -- radius of cylinder
        h           -- height of cylinder
        N           -- number of verts per circle
        co          -- coordinate of cylinder's center
        botFace     -- create face on bottom of cylinder
        topFace     -- create face on top of cylinder
        flipNormals -- flip normals of cylinder
        bme         -- bmesh object in which to create verts

    """
    # create new bmesh object
    if bme is None:
        bme = bmesh.new()

    # initialize lists
    topVerts = []
    botVerts = []
    sideFaces = []

    # create upper and lower circles
    for i in range(N):
        x = r * math.cos(((2 * math.pi) / N) * i)
        y = r * math.sin(((2 * math.pi) / N) * i)
        z = h / 2
        coordT = co + Vector((x, y, z))
        coordB = co + Vector((x, y, -z))
        topVerts.append(bme.verts.new(coordT))
        botVerts.append(bme.verts.new(coordB))

    # create faces on the sides
    _, sideFaces = connectCircles(topVerts if flipNormals else botVerts, botVerts if flipNormals else topVerts, bme)
    smoothFaces(sideFaces)

    # create top and bottom faces
    if topFace:
        bme.faces.new(topVerts if not flipNormals else topVerts[::-1])
    if botFace:
        bme.faces.new(botVerts[::-1] if not flipNormals else botVerts)

    # return bme & dictionary with lists of top and bottom vertices
    return bme, {"bottom":botVerts[::-1], "top":topVerts}


def makeTube(r:float, h:float, t:float, N:int, co:Vector=Vector((0,0,0)), topFace:bool=True, botFace:bool=True, bme:bmesh=None):
    """
    create a tube with bmesh

    Keyword Arguments:
        r       -- radius of inner cylinder
        h       -- height of cylinder
        t       -- thickness of tube
        N       -- number of verts per circle
        co      -- coordinate of cylinder's center
        botFace -- create face on bottom of cylinder
        topFace -- create face on top of cylinder
        bme     -- bmesh object in which to create verts

    """
    # create new bmesh object
    if bme == None:
        bme = bmesh.new()

    # create upper and lower circles
    bme, innerVerts = makeCylinder(r, h, N, co=co, botFace=False, topFace=False, flipNormals=True, bme=bme)
    bme, outerVerts = makeCylinder(r + t, h, N, co=co, botFace=False, topFace=False, bme=bme)
    if topFace:
        connectCircles(outerVerts["top"], innerVerts["top"], bme)
    if botFace:
        connectCircles(outerVerts["bottom"], innerVerts["bottom"], bme)
    # return bmesh
    return bme, {"outer":outerVerts, "inner":innerVerts}


def connectCircles(circle1, circle2, bme, offset=0):
    assert offset < len(circle1) - 1 and offset >= 0
    faces = []
    for v in range(len(circle1)):
        v1 = circle1[v - offset]
        v2 = circle2[v]
        v3 = circle2[(v-1)]
        v4 = circle1[(v-1) - offset]
        f = bme.faces.new((v1, v2, v3, v4))
        faces.append(f)
    return bme, faces
