import bpy
import bmesh
import math
from mathutils import Matrix
from .brick_mesh_generate import makeCylinder, makeTube


def makeBrickRound1x1(dimensions, brickSize, cylinderVerts=None, detail="Low Detail", stud=True, bme=None):
    """
    create round 1x1 brick with bmesh

    Keyword Arguments:
        dimensions   -- dictionary containing brick dimensions
        brickSize    -- size of brick (e.g. standard 2x4 -> [2, 4, 3])
        cylinderVerts -- number of vertices per circle of cylinders
        detail       -- level of brick detail (options: ["Flat", "Low Detail", "Medium Detail", "High Detail"])
        stud         -- create stud on top of brick
        bme          -- bmesh object in which to create verts

    """
    # create new bmesh object
    if not bme:
        bme = bmesh.new()
    scn, cm, _ = getActiveContextInfo()

    # set scale and thickness variables
    dX = dimensions["width"]
    dY = dimensions["width"]
    dZ = dimensions["height"]
    if cm.brickType != "Bricks":
        dZ = dZ*brickSize[2]
    thickZ = dimensions["thickness"]
    if detail == "High Detail" and not (brickSize[0] == 1 or brickSize[1] == 1) and brickSize[2] != 1:
        thickXY = dimensions["thickness"] - dimensions["tick_depth"]
    else:
        thickXY = dimensions["thickness"]
    sX = (brickSize[0] * 2) - 1
    sY = (brickSize[1] * 2) - 1

    # half scale inputs
    dX = dX/2
    dY = dY/2
    dZ = dZ/2



    return
def makeBrickRound2x2():
    return
