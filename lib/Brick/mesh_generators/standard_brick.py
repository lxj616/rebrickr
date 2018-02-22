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


def makeStandardBrick(dimensions:dict, brickSize:list, brickType:str, circleVerts:int=16, detail:str="Low Detail", logo:Object=None, stud:bool=True, bme:bmesh=None):
    """
    create brick with bmesh

    Keyword Arguments:
        dimensions  -- dictionary containing brick dimensions
        brickSize   -- size of brick (e.g. standard 2x4 -> [2, 4, 3])
        brickType   -- type of brick (e.g. Bricks, Plates)
        circleVerts -- number of vertices per circle of cylinders
        detail      -- level of brick detail (options: ["Flat", "Low Detail", "Medium Detail", "High Detail"])
        logo        -- logo object to create on top of studs
        stud        -- create stud on top of brick
        bme         -- bmesh object in which to create verts

    """
    assert detail in ["Flat", "Low Detail", "Medium Detail", "High Detail"]
    # create new bmesh object
    if not bme:
        bme = bmesh.new()

    # set scale and thickness variables
    d = Vector((dimensions["width"] / 2, dimensions["width"] / 2, dimensions["height"] / 2))
    if brickType != "Bricks":
        d.z = d.z * brickSize[2]
    thickZ = dimensions["thickness"]
    if detail == "High Detail" and not (brickSize[0] == 1 or brickSize[1] == 1) and brickSize[2] != 1:
        thickXY = dimensions["thickness"] - dimensions["tick_depth"]
    else:
        thickXY = dimensions["thickness"]
    sX = (brickSize[0] * 2) - 1
    sY = (brickSize[1] * 2) - 1

    # set z2b value for use later
    z2 = -d.z
    if brickType in ["Bricks and Plates"] and brickSize[2] == 3:
        z2b = d.z-thickZ-dimensions["support_height_triple"]
    else:
        z2b = d.z-thickZ-dimensions["support_height"]

    # CREATING CUBE
    x1 = -d.x
    x2 = d.x * sX
    y1 = -d.y
    y2 = d.y * sY
    z1 = -d.z
    z2 = d.z
    v1, v2, v3, v4, v5, v6, v7, v8 = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), [1, 1 if detail == "Flat" else 0, 1, 1, 1, 1], bme=bme)

    # CREATING STUD(S)
    if stud:
        studInset = thickZ * 0.9
        for xNum in range(brickSize[0]):
            for yNum in range(brickSize[1]):
                if brickType == "Bricks and Plates" and brickSize[2] == 3:
                    zCO = dimensions["stud_offset_triple"]-(studInset/2)
                else:
                    zCO = dimensions["stud_offset"]-(studInset/2)
                _,verts = makeCylinder(r=dimensions["stud_radius"], h=dimensions["stud_height"]+studInset, N=circleVerts, co=Vector((xNum*d.x*2,yNum*d.y*2,zCO)), botFace=False, bme=bme)
                selectVerts(verts["bottom"])

    if detail != "Flat":
        # creating cylinder
        # making verts for hollow portion
        x1 = v2.co.x + thickXY
        x2 = v6.co.x - thickXY
        y1 = v2.co.y + thickXY
        y2 = v4.co.y - thickXY
        z1 = v1.co.z
        z2 = d.z - thickZ
        v9, v10, v11, v12, v13, v14, v15, v16 = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), [1 if detail == "Low Detail" else 0, 0, 1, 1, 1, 1], flipNormals=True, bme=bme)
        # set edge vert refs (n=negative, p=positive, o=outer, i=inner)
        nno = v1
        npo = v3
        pno = v5
        ppo = v7
        nni = v9
        npi = v11
        pni = v13
        ppi = v15
        # make tick marks inside 2 by x bricks
        if detail == "High Detail" and ((brickSize[0] == 2 and brickSize[1] > 1) or (brickSize[1] == 2 and brickSize[0] > 1)) and brickSize[2] != 1:
            for xNum in range(brickSize[0]):
                for yNum in range(brickSize[1]):
                    to_select = []
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
                        v1, v2, v3, v4, _, _, _, _ = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=[0, 1, 1, 0, 1, 1], bme=bme)
                        to_select += [v1, v3, v2, v4]
                        if yNum == 0:
                            bme.faces.new((v1, nni, nno))
                        else:
                            bme.faces.new((v1, xN0v, nno))
                        if yNum == brickSize[1]-1:
                            bme.faces.new((v3, npo, npi))
                            bme.faces.new((v3, v1, nno, npo))
                        else:
                            bme.faces.new((v3, v1, nno))
                        xN0v = v3
                    elif xNum == brickSize[0]-1:
                        # initialize x, y
                        x1 = xNum * d.x * 2 + d.x - thickXY - dimensions["tick_depth"]
                        x2 = xNum * d.x * 2 + d.x - thickXY
                        y1 = yNum * d.y * 2 - dimensions["tick_width"] / 2
                        y2 = yNum * d.y * 2 + dimensions["tick_width"] / 2
                        # CREATING SUPPORT BEAM
                        _, _, _, _, v5, v6, v7, v8 = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=[0, 1, 0, 1, 1, 1], bme=bme)
                        to_select += [v5, v6, v7, v8]
                        if yNum == 0:
                            bme.faces.new((pni, v5, pno))
                        else:
                            bme.faces.new((v5, pno, xN1v))
                        if yNum == brickSize[1]-1:
                            bme.faces.new((ppo, v7, ppi))
                            bme.faces.new((v5, v7, ppo, pno))
                        else:
                            bme.faces.new((v5, v7, pno))
                        xN1v = v7
                    if yNum == 0:
                        # initialize x, y
                        y1 = -d.y + thickXY
                        y2 = -d.y + thickXY + dimensions["tick_depth"]
                        x1 = xNum * d.x * 2 - dimensions["tick_width"] / 2
                        x2 = xNum * d.x * 2 + dimensions["tick_width"] / 2
                        # CREATING SUPPORT BEAM
                        v1, v2, _, _, v5, v6, _, _ = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=[0, 1, 1, 1, 1, 0], bme=bme)
                        to_select += [v1, v2, v5, v6]
                        if xNum == 0:
                            bme.faces.new((nni, v1, nno))
                        else:
                            bme.faces.new((v5, nno, yN0v))
                        if xNum == brickSize[0]-1:
                            bme.faces.new((pno, v5, pni))
                            bme.faces.new((nno, v1, v5, pno))
                        else:
                            bme.faces.new((v1, v5, nno))
                        yN0v = v5
                    elif yNum == brickSize[1]-1:
                        # initialize x, y
                        x1 = xNum * d.x * 2 - dimensions["tick_width"] / 2
                        x2 = xNum * d.x * 2 + dimensions["tick_width"] / 2
                        y1 = yNum * d.y * 2 + d.y - thickXY - dimensions["tick_depth"]
                        y2 = yNum * d.y * 2 + d.y - thickXY
                        # CREATING SUPPORT BEAM
                        _, _, v3, v4, _, _, v7, v8 = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=[0, 1, 1, 1, 0, 1], bme=bme)
                        # select bottom connecting verts for exclusion from vertex group
                        to_select += [v3, v4, v7, v8]
                        if xNum == 0:
                            bme.faces.new((v3, npi, npo))
                        else:
                            bme.faces.new((npo, v3, yN1v))
                        if xNum == brickSize[0]-1:
                            bme.faces.new((v7, ppo, ppi))
                            bme.faces.new((v7, v3, npo, ppo))
                        else:
                            bme.faces.new((v7, v3, npo))
                        yN1v = v7
                    # select verts for exclusion from vertex group
                    selectVerts(to_select)
        else:
            # make faces on bottom edges of brick
            bme.faces.new((v1,  v9,  v13, v5))
            bme.faces.new((v1,  v3,  v11, v9))
            bme.faces.new((v15, v7,  v5,  v13))
            bme.faces.new((v15, v11, v3,  v7))


        # make tubes
        addSupports = (brickSize[0] > 2 and brickSize[1] == 2) or (brickSize[1] > 2 and brickSize[0] == 2)
        z1 = z2b
        z2 = d.z-thickZ
        for xNum in range(brickSize[0]-1):
            for yNum in range(brickSize[1]-1):
                tubeX = (xNum * d.x * 2) + d.x
                tubeY = (yNum * d.y * 2) + d.y
                tubeZ = (-thickZ/2)
                r = dimensions["stud_radius"]
                h = (d.z*2)-thickZ
                bme, tubeVerts = makeTube(r, h, dimensions["tube_thickness"], circleVerts, co=Vector((tubeX, tubeY, tubeZ)), botFace=True, topFace=False, bme=bme)
                # select top verts for exclusion from vert group
                for lst in [tubeVerts["outer"]["top"], tubeVerts["inner"]["top"]]:
                    selectVerts(lst)

                # add support next to odd tubes
                if detail not in ["Medium Detail", "High Detail"] or not addSupports or brickSize[2] == 1:
                    continue
                if brickSize[0] > brickSize[1]:
                    if brickSize[0] == 3 or xNum % 2 == 1:
                        # initialize x, y
                        x1 = tubeX - (dimensions["support_width"]/2)
                        x2 = tubeX + (dimensions["support_width"]/2)
                        y1 = tubeY + r
                        y2 = tubeY + d.y*2-thickXY
                        y3 = tubeY - d.y*2+thickXY
                        y4 = tubeY - r
                        # CREATING SUPPORT BEAM
                        makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=[0, 1, 1, 1, 0, 0], bme=bme)
                        makeCube(Vector((x1, y3, z1)), Vector((x2, y4, z2)), sides=[0, 1, 1, 1, 0, 0], bme=bme)
                elif brickSize[1] > brickSize[0]:
                    if brickSize[1] == 3 or yNum % 2 == 1:
                        # initialize x, y
                        x1 = tubeX + r
                        x2 = tubeX + d.x*2-thickXY
                        x3 = tubeX - d.x*2+thickXY
                        x4 = tubeX - r
                        y1 = tubeY - (dimensions["support_width"] / 2)
                        y2 = tubeY + (dimensions["support_width"] / 2)
                        # CREATING SUPPORT BEAM
                        makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=[0, 1, 0, 0, 1, 1], bme=bme)
                        makeCube(Vector((x3, y1, z1)), Vector((x4, y2, z2)), sides=[0, 1, 0, 0, 1, 1], bme=bme)
        # Adding bar inside 1 by x bricks
        if brickSize[0] == 1:
            for y in range(1, brickSize[1]):
                barX = 0
                barY = (y * d.y * 2) - d.y
                barZ = -thickZ/2
                r = dimensions["bar_radius"]
                _,verts = makeCylinder(r=r, h=(d.z*2)-thickZ, N=circleVerts, co=Vector((barX, barY, barZ)), botFace=True, topFace=False, bme=bme)
                # select top verts for exclusion from vert group
                selectVerts(verts["top"])
                if detail in ["Medium Detail", "High Detail"] and brickSize[2] != 1:
                    if brickSize[1] == 3 or brickSize[1] == 2 or y % 2 == 0 or ((y == 1 or y == brickSize[1]-1) and brickSize[1] == 8):
                        # initialize x, y, z
                        x1 = barX - d.x+thickXY
                        x2 = barX + d.x-thickXY
                        y1 = barY - (dimensions["support_width"]/2)
                        y2 = barY + (dimensions["support_width"]/2)
                        # CREATING SUPPORT BEAM
                        makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=[0, 1, 0, 0, 1, 1], bme=bme)
        if brickSize[1] == 1:
            for x in range(1, brickSize[0]):
                barX = (x * d.x * 2) - d.x
                barY = 0
                barZ = -thickZ/2
                r = dimensions["bar_radius"]
                _,verts = makeCylinder(r=r, h=(d.z*2)-thickZ, N=circleVerts, co=Vector((barX, barY, barZ)), botFace=True, topFace=False, bme=bme)
                # select top verts for exclusion from vert group
                selectVerts(verts["top"])
                # add supports next to odd bars
                if detail in ["Flat", "Low Detail"] or brickSize[2] == 1:
                    continue
                if brickSize[0] == 3 or brickSize[0] == 2 or x % 2 == 0 or ((x == 1 or x == brickSize[0]-1) and brickSize[0] == 8):
                    # initialize x, y, z
                    x1 = barX - (dimensions["support_width"]/2)
                    x2 = barX + (dimensions["support_width"]/2)
                    y1 = barY - d.y+thickXY
                    y2 = barY + d.y-thickXY
                    # CREATING SUPPORT BEAM
                    makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=[0, 1, 1, 1, 0, 0], bme=bme)
        # add small inner cylinders inside brick
        if detail in ["Medium Detail", "High Detail"]:
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
                bme.faces.new((vList[i], vList[i-1], v10))
            vList = botVertsDofDs[str(xNum) + "," + str(0)]["x+"] + botVertsDofDs[str(xNum) + "," + str(0)]["+-"] + botVertsDofDs[str(xNum) + "," + str(0)]["y-"]
            for i in range(1, len(vList)):
                bme.faces.new((vList[i], vList[i-1], v14))
            vList = botVertsDofDs[str(xNum) + "," + str(yNum)]["y+"] + botVertsDofDs[str(xNum) + "," + str(yNum)]["++"] + botVertsDofDs[str(xNum) + "," + str(yNum)]["x+"]
            for i in range(1, len(vList)):
                bme.faces.new((vList[i], vList[i-1], v16))
            vList = botVertsDofDs[str(0) + "," + str(yNum)]["x-"] + botVertsDofDs[str(0) + "," + str(yNum)]["-+"] + botVertsDofDs[str(0) + "," + str(yNum)]["y+"]
            for i in range(1, len(vList)):
                bme.faces.new((vList[i], vList[i-1], v12))

            # Make edge faces
            v = botVertsDofDs[str(xNum) + "," + str(yNum)]["y+"][0]
            bme.faces.new((v12, v16, v))
            v = botVertsDofDs[str(0) + "," + str(yNum)]["x-"][0]
            bme.faces.new((v10, v12, v))
            v = botVertsDofDs[str(0) + "," + str(0)]["y-"][0]
            bme.faces.new((v14, v10, v))
            v = botVertsDofDs[str(xNum) + "," + str(0)]["x+"][0]
            bme.faces.new((v16, v14, v))
            for xNum in range(1, brickSize[0]):
                try:
                    v1 = botVertsDofDs[str(xNum) + "," + str(yNum)]["y+"][0]
                    v2 = botVertsDofDs[str(xNum-1) + "," + str(yNum)]["y+"][0]
                    bme.faces.new((v1, v2, v12))
                except:
                    pass
                try:
                    v1 = botVertsDofDs[str(xNum) + "," + str(0)]["y-"][0]
                    v2 = botVertsDofDs[str(xNum-1) + "," + str(0)]["y-"][0]
                    bme.faces.new((v14, v2, v1))
                except:
                    pass
            for yNum in range(1, brickSize[1]):
                try:
                    v1 = botVertsDofDs[str(xNum) + "," + str(yNum)]["x+"][0]
                    v2 = botVertsDofDs[str(xNum) + "," + str(yNum-1)]["x+"][0]
                    bme.faces.new((v16, v2, v1))
                except:
                    pass
                try:
                    v1 = botVertsDofDs[str(0) + "," + str(yNum)]["x-"][0]
                    v2 = botVertsDofDs[str(0) + "," + str(yNum-1)]["x-"][0]
                    bme.faces.new((v1, v2, v10))
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
