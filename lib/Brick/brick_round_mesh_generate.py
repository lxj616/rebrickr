import bpy
import bmesh
import math
from mathutils import Matrix
from .brick_mesh_generate import makeCylinder, makeTube


def makeBrickRound1x1(dimensions, brickSize, circleVerts=None, detail="Low Detail", stud=True, bme=None):
    """
    create round 1x1 brick with bmesh

    Keyword Arguments:
        dimensions   -- dictionary containing brick dimensions
        brickSize    -- size of brick (e.g. standard 2x4 -> [2, 4, 3])
        circleVerts -- number of vertices per circle of cylinders
        detail       -- level of brick detail (options: ["Flat", "Low Detail", "Medium Detail", "High Detail"])
        stud         -- create stud on top of brick
        bme          -- bmesh object in which to create verts

    """
    # create new bmesh object
    if not bme:
        bme = bmesh.new()
    scn, cm, _ = getActiveContextInfo()

    # set scale and thickness variables
    thickZ = dimensions["thickness"]
    if detail == "High Detail" and not (brickSize[0] == 1 or brickSize[1] == 1) and brickSize[2] != 1:
        thickXY = dimensions["thickness"] - dimensions["tick_depth"]
    else:
        thickXY = dimensions["thickness"]
    sX = (brickSize[0] * 2) - 1
    sY = (brickSize[1] * 2) - 1

    # create outer cylinder
    r = dimensions["width"] / 2
    h = dimensions["height"] - dimensions["stud_height"]
    bme, botVerts, topVerts = makeCylinder(r, h, circleVerts, co=Vector((0, 0, dimensions["stud_height"] / 2)), botFace=False, bme=bme)

    # create lower cylinder
    r = dimensions["stud_radius"]
    h = dimensions["stud_height"]
    # TODO: get official thickness of bottom cylinder in round 1x1 LEGO brick
    t = (dimensions["width"] - r) * 0.25
    bme = makeTube(r, h, t, circleVerts, co=Vector((0, 0, - dimensions["height"] + (dimensions["stud_height"] / 2))), topFace=False, bme=bme)

    # create stud


    return
