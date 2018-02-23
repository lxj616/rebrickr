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
import bmesh
import math

# Blender imports
from mathutils import Vector, Matrix
from bpy.types import Object

# Rebrickr imports
from .geometric_shapes import *
from ....functions.common import *
from ....functions.general import *


def makeStandardBrick(dimensions:dict, brickSize:list, brickType:str, circleVerts:int=16, detail:str="LOW", logo:Object=None, stud:bool=True, bme:bmesh=None):
    """
    create brick with bmesh

    Keyword Arguments:
        dimensions  -- dictionary containing brick dimensions
        brickSize   -- size of brick (e.g. standard 2x4 -> [2, 4, 3])
        brickType   -- type of brick (e.g. Bricks, Plates)
        circleVerts -- number of vertices per circle of cylinders
        detail      -- level of brick detail (options: ["FLAT", "LOW", "MEDIUM", "HIGH"])
        logo        -- logo object to create on top of studs
        stud        -- create stud on top of brick
        bme         -- bmesh object in which to create verts

    """
    assert detail in ["FLAT", "LOW", "MEDIUM", "HIGH"]
    # create new bmesh object
    if not bme:
        bme = bmesh.new()
    _, cm, _ = getActiveContextInfo()

    # get halfScale
    d = Vector((dimensions["width"] / 2, dimensions["width"] / 2, dimensions["height"] / 2))
    if brickType != "Bricks":
        d.z = d.z * brickSize[2]
    # get scalar for d in both positive directions
    sX = (brickSize[0] * 2) - 1
    sY = (brickSize[1] * 2) - 1
    # get thickness of brick from inside to outside
    thickZ = dimensions["thickness"]
    thickXY = dimensions["thickness"] - (dimensions["tick_depth"] if "High" in detail and min(brickSize) != 1 else 0)

    # create cube
    vector_mult = lambda v1, v2: Vector(e1 * e2 for e1, e2 in zip(v1, v2))
    coord1 = -d
    coord2 = vector_mult(d, Vector((sX, sY, 1)))
    v1, v2, v3, v4, v5, v6, v7, v8 = makeCube(coord1, coord2, [1, 1 if detail == "FLAT" else 0, 1, 1, 1, 1], bme=bme)

    # add studs
    if stud: addStuds(dimensions, brickSize, brickType, circleVerts, bme, zStep=getZStep(cm), inset=dimensions["thickness"] * 0.9)

    # add details
    if detail != "FLAT":
        # creating cylinder
        # making verts for hollow portion
        x1 = v1.co.x + thickXY
        x2 = v4.co.x - thickXY
        y1 = v4.co.y + thickXY
        y2 = v3.co.y - thickXY
        z1 = v1.co.z
        z2 = d.z - thickZ
        v9, v10, v11, v12, v13, v14, v15, v16 = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), [1 if detail == "LOW" else 0, 0, 1, 1, 1, 1], flipNormals=True, bme=bme)
        # make tick marks inside 2 by x bricks
        if detail == "HIGH" and ((brickSize[0] == 2 and brickSize[1] > 1) or (brickSize[1] == 2 and brickSize[0] > 1)) and brickSize[2] != 1:
            addTickMarks(dimensions, brickSize, circleVerts, detail, d, thickXY, v1, v2, v3, v4, v9, v10, v11, v12, bme)
        else:
            # make faces on bottom edges of brick
            bme.faces.new((v1,  v9,  v12, v4))
            bme.faces.new((v1,  v2,  v10, v9))
            bme.faces.new((v11, v3,  v4,  v12))
            bme.faces.new((v11, v10, v2,  v3))


        # make tubes
        addTubeSupports(dimensions, brickSize, circleVerts, brickType, detail, d, sX, thickXY, bme)
        # Adding bar inside 1 by x bricks
        addBars(dimensions, brickSize, circleVerts, brickType, detail, d, sX, thickXY, bme)
        # add small inner cylinders inside brick
        if detail in ["MEDIUM", "HIGH"]:
            addInnerCylinders(dimensions, brickSize, circleVerts, d, v13, v14, v15, v16, bme)


    # bmesh.ops.transform(bme, matrix=Matrix.Translation(((dimensions["width"]/2)*(addedX),(dimensions["width"]/2)*(addedY),0)), verts=bme.verts)
    nx = (dimensions["width"] + dimensions["gap"]) * brickSize[0] - dimensions["gap"]
    ny = (dimensions["width"] + dimensions["gap"]) * brickSize[1] - dimensions["gap"]
    dx = dimensions["width"] * brickSize[0]
    dy = dimensions["width"] * brickSize[1]
    if brickSize[0] != 1 or brickSize[1] != 1:
        bmesh.ops.scale(bme, verts=bme.verts, vec=(nx/dx, ny/dy, 1.0))

    # return bmesh
    return bme


def createVertListBDict(verts):
    idx4 = len(verts["bottom"]) - 1
    idx1 = int(round(len(verts["bottom"]) * 1 / 4)) - 1
    idx2 = int(round(len(verts["bottom"]) * 2 / 4)) - 1
    idx3 = int(round(len(verts["bottom"]) * 3 / 4)) - 1

    vertListBDict = {"++":[verts["bottom"][idx] for idx in range(idx1 + 1, idx2)],
                     "+-":[verts["bottom"][idx] for idx in range(idx2 + 1, idx3)],
                     "--":[verts["bottom"][idx] for idx in range(idx3 + 1, idx4)],
                     "-+":[verts["bottom"][idx] for idx in range(0,        idx1)],
                     "y+":[verts["bottom"][idx1]],
                     "x+":[verts["bottom"][idx2]],
                     "y-":[verts["bottom"][idx3]],
                     "x-":[verts["bottom"][idx4]]}

    return vertListBDict


def addTickMarks(dimensions, brickSize, circleVerts, detail, d, thickXY, v1, v2, v3, v4, v9, v10, v11, v12, bme):
    thickZ = dimensions["thickness"]
    # set edge vert refs (n=negative, p=positive, o=outer, i=inner)
    nno = v1
    npo = v2
    ppo = v3
    pno = v4
    nni = v9
    npi = v10
    ppi = v11
    pni = v12
    # make tick marks
    for xNum in range(brickSize[0]):
        for yNum in range(brickSize[1]):
            # initialize z
            z1 = -d.z
            z2 = d.z - thickZ
            if xNum == 0:
                # initialize x, y
                x1 = -d.x + thickXY
                x2 = -d.x + thickXY + dimensions["tick_depth"]
                y1 = yNum * d.y * 2 - dimensions["tick_width"] / 2
                y2 = yNum * d.y * 2 + dimensions["tick_width"] / 2
                # CREATING SUPPORT BEAM
                v1, v2, _, _, _, v6, v7, _ = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=[0, 1, 1, 0, 1, 1], bme=bme)
                selectVerts([v1, v2, v6, v7])
                if yNum == 0:
                    bme.faces.new((v1, nni, nno))
                else:
                    bme.faces.new((v1, xN0v, nno))
                if yNum == brickSize[1]-1:
                    bme.faces.new((v2, npo, npi))
                    bme.faces.new((v2, v1, nno, npo))
                else:
                    bme.faces.new((v2, v1, nno))
                xN0v = v2
            elif xNum == brickSize[0]-1:
                # initialize x, y
                x1 = xNum * d.x * 2 + d.x - thickXY - dimensions["tick_depth"]
                x2 = xNum * d.x * 2 + d.x - thickXY
                y1 = yNum * d.y * 2 - dimensions["tick_width"] / 2
                y2 = yNum * d.y * 2 + dimensions["tick_width"] / 2
                # CREATING SUPPORT BEAM
                _, _, v3, v4, v5, _, _, v8 = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=[0, 1, 0, 1, 1, 1], bme=bme)
                selectVerts([v3, v4, v5, v8])
                if yNum == 0:
                    bme.faces.new((pni, v4, pno))
                else:
                    bme.faces.new((v4, pno, xN1v))
                if yNum == brickSize[1]-1:
                    bme.faces.new((ppo, v3, ppi))
                    bme.faces.new((v4, v3, ppo, pno))
                else:
                    bme.faces.new((v4, v3, pno))
                xN1v = v3
            if yNum == 0:
                # initialize x, y
                y1 = -d.y + thickXY
                y2 = -d.y + thickXY + dimensions["tick_depth"]
                x1 = xNum * d.x * 2 - dimensions["tick_width"] / 2
                x2 = xNum * d.x * 2 + dimensions["tick_width"] / 2
                # CREATING SUPPORT BEAM
                v1, _, _, v4, _, _, v7, v8 = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=[0, 1, 1, 1, 1, 0], bme=bme)
                selectVerts([v1, v4, v7, v8])
                if xNum == 0:
                    bme.faces.new((nni, v1, nno))
                else:
                    bme.faces.new((v4, nno, yN0v))
                if xNum == brickSize[0]-1:
                    bme.faces.new((pno, v4, pni))
                    bme.faces.new((nno, v1, v4, pno))
                else:
                    bme.faces.new((v1, v4, nno))
                yN0v = v4
            elif yNum == brickSize[1]-1:
                # initialize x, y
                x1 = xNum * d.x * 2 - dimensions["tick_width"] / 2
                x2 = xNum * d.x * 2 + dimensions["tick_width"] / 2
                y1 = yNum * d.y * 2 + d.y - thickXY - dimensions["tick_depth"]
                y2 = yNum * d.y * 2 + d.y - thickXY
                # CREATING SUPPORT BEAM
                _, v2, v3, _, v5, v6, _, _ = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=[0, 1, 1, 1, 0, 1], bme=bme)
                # select bottom connecting verts for exclusion from vertex group
                selectVerts([v2, v3, v5, v6])
                if xNum == 0:
                    bme.faces.new((v2, npi, npo))
                else:
                    bme.faces.new((npo, v2, yN1v))
                if xNum == brickSize[0]-1:
                    bme.faces.new((v3, ppo, ppi))
                    bme.faces.new((v3, v2, npo, ppo))
                else:
                    bme.faces.new((v3, v2, npo))
                yN1v = v3


def addTubeSupports(dimensions, brickSize, circleVerts, type, detail, d, sX, thickXY, bme):
    thickZ = dimensions["thickness"]
    addSupports = (brickSize[0] > 2 and brickSize[1] == 2) or (brickSize[1] > 2 and brickSize[0] == 2)
    # set z1 value
    z1 = d.z - thickZ - dimensions["support_height"] * (brickSize[2] if type == "Bricks and Plates" else 1)
    z2 = d.z - thickZ
    allTopVerts = []
    for xNum in range(brickSize[0]-1):
        for yNum in range(brickSize[1]-1):
            tubeX = (xNum * d.x * 2) + d.x
            tubeY = (yNum * d.y * 2) + d.y
            tubeZ = (-thickZ / 2)
            r = dimensions["stud_radius"]
            h = (dimensions["height"]) - thickZ
            bme, tubeVerts = makeTube(r, h, dimensions["tube_thickness"], circleVerts, co=Vector((tubeX, tubeY, tubeZ)), botFace=True, topFace=False, bme=bme)
            # select verts for exclusion from vert group
            selectVerts(tubeVerts["outer"]["top"] + tubeVerts["inner"]["top"])
            allTopVerts += tubeVerts["outer"]["top"] + tubeVerts["inner"]["top"]

            # add support next to odd tubes
            if detail not in ["MEDIUM", "HIGH"] or not addSupports or brickSize[2] == 1:
                continue
            if brickSize[0] > brickSize[1]:
                if brickSize[0] == 3 or xNum % 2 == 1:
                    # initialize x, y
                    x1 = tubeX - (dimensions["support_width"] / 2)
                    x2 = tubeX + (dimensions["support_width"] / 2)
                    y1 = tubeY + r
                    y2 = tubeY - thickXY + d.y * 2
                    y3 = tubeY + thickXY - d.y * 2
                    y4 = tubeY - r
                    # CREATING SUPPORT BEAM
                    cubeVerts1 = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=[0, 1, 1, 1, 0, 0], bme=bme)
                    cubeVerts2 = makeCube(Vector((x1, y3, z1)), Vector((x2, y4, z2)), sides=[0, 1, 1, 1, 0, 0], bme=bme)
                    allTopVerts += cubeVerts1[4:] + cubeVerts2[4:]
            elif brickSize[1] > brickSize[0]:
                if brickSize[1] == 3 or yNum % 2 == 1:
                    # initialize x, y
                    x1 = tubeX + r
                    x2 = tubeX - thickXY + d.x * 2
                    x3 = tubeX + thickXY - d.x * 2
                    x4 = tubeX - r
                    y1 = tubeY - (dimensions["support_width"] / 2)
                    y2 = tubeY + (dimensions["support_width"] / 2)
                    # CREATING SUPPORT BEAM
                    cubeVerts1 = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=[0, 1, 0, 0, 1, 1], bme=bme)
                    cubeVerts2 = makeCube(Vector((x3, y1, z1)), Vector((x4, y2, z2)), sides=[0, 1, 0, 0, 1, 1], bme=bme)
                    allTopVerts += cubeVerts1[4:] + cubeVerts2[4:]
    if type == "SLOPE":
        cutVerts(dimensions, brickSize, allTopVerts, d, sX, thickZ, bme)


def addBars(dimensions, brickSize, circleVerts, type, detail, d, sX, thickXY, bme):
    thickZ = dimensions["thickness"]
    z1 = -d.z
    z2 = d.z - thickZ
    r = dimensions["bar_radius"]
    barZ = -(thickZ / 2)
    sides = [0, 1] + ([0, 0, 1, 1] if brickSize[0] == 1 else [1, 1, 0, 0])
    allTopVerts = []
    if brickSize[0] == 1:
        for y in range(1, brickSize[1]):
            barY = (y * dimensions["width"]) - d.y
            _,verts = makeCylinder(r=r, h=dimensions["height"] - thickZ, N=circleVerts, co=Vector((0, barY, barZ)), botFace=True, topFace=False, bme=bme)
            selectVerts(verts["top"])
            allTopVerts += verts["top"]
            if detail in ["FLAT", "LOW"] or brickSize[2] == 1:
                continue
            if brickSize[1] == 3 or brickSize[1] == 2 or y % 2 == 0 or ((y == 1 or y == brickSize[1] - 1) and brickSize[1] == 8):
                # initialize x, y, z
                x1 = -d.x + thickXY
                x2 =  d.x - thickXY
                y1 = barY - (dimensions["support_width"] / 2)
                y2 = barY + (dimensions["support_width"] / 2)
                # CREATING SUPPORT BEAM
                cubeVerts = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=sides, bme=bme)
                allTopVerts += cubeVerts[4:]
    elif brickSize[1] == 1:
        for x in range(1, brickSize[0]):
            barX = (x * dimensions["width"]) - d.x
            _,verts = makeCylinder(r=r, h=dimensions["height"]-thickZ, N=circleVerts, co=Vector((barX, 0, barZ)), botFace=True, topFace=False, bme=bme)
            selectVerts(verts["top"])
            allTopVerts += verts["top"]
            # add supports next to odd bars
            if detail in ["FLAT", "LOW"] or brickSize[2] == 1:
                continue
            if brickSize[0] == 3 or brickSize[0] == 2 or x % 2 == 0 or ((x == 1 or x == brickSize[0] - 1) and brickSize[0] == 8):
                # initialize x, y, z
                x1 = barX - (dimensions["support_width"] / 2)
                x2 = barX + (dimensions["support_width"] / 2)
                y1 = -d.y + thickXY
                y2 =  d.y - thickXY
                # CREATING SUPPORT BEAM
                cubeVerts = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=sides, bme=bme)
                allTopVerts += cubeVerts[4:]
    if type == "SLOPE":
        cutVerts(dimensions, brickSize, allTopVerts, d, sX, thickZ, bme)


def cutVerts(dimensions, brickSize, verts, d, sX, thickZ, bme):
    minZ = -(dimensions["height"] / 2) + thickZ
    for v in verts:
        numer = v.co.x - d.x
        denom = d.x * (sX - 1) - (dimensions["tube_thickness"] + dimensions["stud_radius"]) * (brickSize[0] - 2) + (dimensions["thickness"] * (brickSize[0] - 3))
        fac = numer / denom
        if fac < 0:
            continue
        v.co.z = fac * minZ + (1-fac) * v.co.z


def addInnerCylinders(dimensions, brickSize, circleVerts, d, v5, v6, v7, v8, bme):
    thickZ = dimensions["thickness"]
    # make small cylinders
    botVertsDofDs = {}
    for xNum in range(brickSize[0]):
        for yNum in range(brickSize[1]):
            r = dimensions["stud_radius"]-(2 * thickZ)
            N = circleVerts
            h = thickZ * 0.99
            bme, innerCylinderVerts = makeCylinder(r, h, N, co=Vector((xNum*d.x*2,yNum*d.y*2,d.z - thickZ + h/2)), botFace=False, flipNormals=True, bme=bme)
            botVertsD = createVertListBDict(innerCylinderVerts)
            botVertsDofDs["%(xNum)s,%(yNum)s" % locals()] = botVertsD

    # Make corner faces
    vList = botVertsDofDs["0,0"]["y-"] + botVertsDofDs["0,0"]["--"] + botVertsDofDs["0,0"]["x-"]
    for i in range(1, len(vList)):
        bme.faces.new((vList[i], vList[i-1], v5))
    vList = botVertsDofDs[str(xNum) + "," + str(0)]["x+"] + botVertsDofDs[str(xNum) + "," + str(0)]["+-"] + botVertsDofDs[str(xNum) + "," + str(0)]["y-"]
    for i in range(1, len(vList)):
        bme.faces.new((vList[i], vList[i-1], v6))
    vList = botVertsDofDs[str(xNum) + "," + str(yNum)]["y+"] + botVertsDofDs[str(xNum) + "," + str(yNum)]["++"] + botVertsDofDs[str(xNum) + "," + str(yNum)]["x+"]
    for i in range(1, len(vList)):
        bme.faces.new((vList[i], vList[i-1], v7))
    vList = botVertsDofDs[str(0) + "," + str(yNum)]["x-"] + botVertsDofDs[str(0) + "," + str(yNum)]["-+"] + botVertsDofDs[str(0) + "," + str(yNum)]["y+"]
    for i in range(1, len(vList)):
        bme.faces.new((vList[i], vList[i-1], v8))

    # Make edge faces
    v = botVertsDofDs[str(xNum) + "," + str(yNum)]["y+"][0]
    bme.faces.new((v8, v7, v))
    v = botVertsDofDs[str(0) + "," + str(yNum)]["x-"][0]
    bme.faces.new((v5, v8, v))
    v = botVertsDofDs[str(0) + "," + str(0)]["y-"][0]
    bme.faces.new((v6, v5, v))
    v = botVertsDofDs[str(xNum) + "," + str(0)]["x+"][0]
    bme.faces.new((v7, v6, v))
    for xNum in range(1, brickSize[0]):
        try:
            v1 = botVertsDofDs[str(xNum) + "," + str(yNum)]["y+"][0]
            v2 = botVertsDofDs[str(xNum-1) + "," + str(yNum)]["y+"][0]
            bme.faces.new((v1, v2, v8))
        except:
            pass
        try:
            v1 = botVertsDofDs[str(xNum) + "," + str(0)]["y-"][0]
            v2 = botVertsDofDs[str(xNum-1) + "," + str(0)]["y-"][0]
            bme.faces.new((v6, v2, v1))
        except:
            pass
    for yNum in range(1, brickSize[1]):
        try:
            v1 = botVertsDofDs[str(xNum) + "," + str(yNum)]["x+"][0]
            v2 = botVertsDofDs[str(xNum) + "," + str(yNum-1)]["x+"][0]
            bme.faces.new((v7, v2, v1))
        except:
            pass
        try:
            v1 = botVertsDofDs[str(0) + "," + str(yNum)]["x-"][0]
            v2 = botVertsDofDs[str(0) + "," + str(yNum-1)]["x-"][0]
            bme.faces.new((v1, v2, v5))
        except:
            pass

    # Make in-between-insets faces along x axis
    for xNum in range(1, brickSize[0]):
        for yNum in range(brickSize[1]):
            vList1 = botVertsDofDs[str(xNum-1) + "," + str(yNum)]["y+"] + botVertsDofDs[str(xNum-1) + "," + str(yNum)]["++"] + botVertsDofDs[str(xNum-1) + "," + str(yNum)]["x+"] + botVertsDofDs[str(xNum-1) + "," + str(yNum)]["+-"] + botVertsDofDs[str(xNum-1) + "," + str(yNum)]["y-"]
            vList2 = botVertsDofDs[str(xNum) + "," + str(yNum)]["y+"] + botVertsDofDs[str(xNum) + "," + str(yNum)]["-+"][::-1] + botVertsDofDs[str(xNum) + "," + str(yNum)]["x-"] + botVertsDofDs[str(xNum) + "," + str(yNum)]["--"][::-1] + botVertsDofDs[str(xNum) + "," + str(yNum)]["y-"]
            if len(vList1) > len(vList2):
                v1 = vList1[-1]
                v2 = vList1[-2]
                v3 = vList2[-1]
                bme.faces.new((v1, v2, v3))
                numIters = len(vList2)
            elif len(vList1) < len(vList2):
                v1 = vList1[-1]
                v2 = vList2[-2]
                v3 = vList2[-1]
                bme.faces.new((v1, v2, v3))
                numIters = len(vList1)
            else:
                numIters = len(vList1)
            for i in range(1, numIters):
                v1 = vList1[i]
                v2 = vList1[i-1]
                v3 = vList2[i-1]
                v4 = vList2[i]
                bme.faces.new((v1, v2, v3, v4))

    # Make in-between-inset quads
    for yNum in range(1, brickSize[1]):
        for xNum in range(1, brickSize[0]):
            try:
                v1 = botVertsDofDs[str(xNum-1) + "," + str(yNum)]["y-"][0]
                v2 = botVertsDofDs[str(xNum) + "," + str(yNum)]["y-"][0]
                v3 = botVertsDofDs[str(xNum) + "," + str(yNum-1)]["y+"][0]
                v4 = botVertsDofDs[str(xNum-1) + "," + str(yNum-1)]["y+"][0]
                bme.faces.new((v1, v2, v3, v4))
            except:
                pass

    # Make final in-between-insets faces on extremes of x axis along y axis
    for yNum in range(1, brickSize[1]):
        vList1 = botVertsDofDs[str(0) + "," + str(yNum-1)]["x-"] + botVertsDofDs[str(0) + "," + str(yNum-1)]["-+"] + botVertsDofDs[str(0) + "," + str(yNum-1)]["y+"]
        vList2 = botVertsDofDs[str(0) + "," + str(yNum)]["x-"] + botVertsDofDs[str(0) + "," + str(yNum)]["--"][::-1] + botVertsDofDs[str(0) + "," + str(yNum)]["y-"]
        if len(vList1) > len(vList2):
            v1 = vList1[-1]
            v2 = vList1[-2]
            v3 = vList2[-1]
            bme.faces.new((v1, v2, v3))
            numIters = len(vList2)
        elif len(vList1) < len(vList2):
            v1 = vList1[-1]
            v2 = vList2[-2]
            v3 = vList2[-1]
            bme.faces.new((v1, v2, v3))
            numIters = len(vList1)
        else:
            numIters = len(vList1)
        for i in range(1, numIters):
            v1 = vList1[i]
            v2 = vList1[i-1]
            v3 = vList2[i-1]
            v4 = vList2[i]
            bme.faces.new((v1, v2, v3, v4))
    for yNum in range(1, brickSize[1]):
        vList1 = botVertsDofDs[str(xNum) + "," + str(yNum-1)]["x+"] + botVertsDofDs[str(xNum) + "," + str(yNum-1)]["++"][::-1] + botVertsDofDs[str(xNum) + "," + str(yNum-1)]["y+"]
        vList2 = botVertsDofDs[str(xNum) + "," + str(yNum)]["x+"] + botVertsDofDs[str(xNum) + "," + str(yNum)]["+-"] + botVertsDofDs[str(xNum) + "," + str(yNum)]["y-"]
        if len(vList1) > len(vList2):
            v1 = vList1[-1]
            v2 = vList2[-1]
            v3 = vList1[-2]
            bme.faces.new((v1, v2, v3))
            numIters = len(vList2)
        elif len(vList1) < len(vList2):
            v1 = vList1[-1]
            v2 = vList2[-2]
            v3 = vList2[-1]
            bme.faces.new((v1, v2, v3))
        else:
            numIters = len(vList1)
        for i in range(1, numIters):
            v1 = vList2[i]
            v2 = vList2[i-1]
            v3 = vList1[i-1]
            v4 = vList1[i]
            bme.faces.new((v1, v2, v3, v4))


def addStuds(dimensions, brickSize, brickType, circleVerts, bme, hollow=False, zStep=1, inset=0):
    r = dimensions["bar_radius" if hollow else "stud_radius"]
    h = dimensions["stud_height"]
    t = dimensions["stud_radius"] - dimensions["bar_radius"]
    if brickType == "Bricks and Plates":
        mult = brickSize[2]
    elif "STUD" in brickType:
        mult = 1 / 3
    else:
        mult = 1
    z = ((dimensions["height"] * mult) / 2) + dimensions["stud_height"] / 2 - inset / 2
    for xNum in range(brickSize[0]):
        for yNum in range(brickSize[1]):
            x = dimensions["width"] * xNum
            y = dimensions["width"] * yNum
            if hollow:
                _, studVerts = makeTube(r, h, t, circleVerts, co=Vector((0, 0, z)), bme=bme)
                selectVerts(studVerts["outer"]["bottom"] + studVerts["inner"]["bottom"])
            else:
                _, studVerts = makeCylinder(r=r, h=h + inset, N=circleVerts, co=Vector((x, y, z)), botFace=False, bme=bme)
                selectVerts(studVerts["bottom"])
    return studVerts
