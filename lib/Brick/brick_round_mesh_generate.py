import bpy
import bmesh
import math
from mathutils import Matrix

# r = radius, N = numVerts, h = height, co = target cylinder position, botFace = Bool for creating face on bottom, bme = bmesh to insert mesh data into
def makeCylinder(r, N, h, co=(0,0,0), botFace=True, topFace=True, bme=None):
    # create new bmesh object
    if bme == None:
        bme = bmesh.new()

    # create upper and lower circles
    vertListT = []
    vertListB = []
    sideFaces = []
    for i in range(N):
        x = r * math.cos(((2 * math.pi) / N) * i)
        y = r * math.sin(((2 * math.pi) / N) * i)
        z = h / 2
        coordT = (x + co[0], y + co[1], z + co[2])
        coordB = (x + co[0], y + co[1], -z + co[2])
        vertListT.append(bme.verts.new(coordT))
        vertListB.append(bme.verts.new(coordB))

    # create top and bottom faces
    topVerts = vertListT[:]
    botVerts = vertListB[::-1]
    if topFace:
        bme.faces.new(topVerts)
    if botFace:
        bme.faces.new(botVerts)

    # create faces on the sides
    sideFaces.append(bme.faces.new((vertListT[-1], vertListB[-1], vertListB[0], vertListT[0])))
    for v in range(N-1):
        sideFaces.append(bme.faces.new((vertListT.pop(0), vertListB.pop(0), vertListB[0], vertListT[0])))

    for f in sideFaces:
        f.smooth = True

    # return bmesh
    return bme, botVerts, topVerts

def makeBrickRound1x1(dimensions, brickSize, numStudVerts=None, detail="Low Detail", stud=True, bme=None):
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
