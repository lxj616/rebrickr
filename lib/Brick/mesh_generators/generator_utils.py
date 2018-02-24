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
from .generator_utils import *
from ....functions.common import *
from ....functions.general import *


def addStuds(dimensions, brickSize, brickType, circleVerts, bme, hollow=False, zStep=1, inset=0):
    r = dimensions["bar_radius" if hollow else "stud_radius"]
    h = dimensions["stud_height"]
    t = dimensions["stud_radius"] - dimensions["bar_radius"]
    if brickType == "BRICKS AND PLATES":
        mult = brickSize[2]
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


def addBars(dimensions, brickSize, circleVerts, type, detail, d, scalar, thick, bme):
    z1 = -d.z
    z2 = d.z - thick.z
    r = dimensions["bar_radius"]
    _, cm, _ = getActiveContextInfo()
    bAndPBrick = cm.brickType == "BRICKS AND PLATES" and brickSize[2] == 3
    height = dimensions["height"] * (3 if bAndPBrick else 1)
    barZ = -(thick.z / 2)
    sides = [0, 1] + ([0, 0, 1, 1] if brickSize[0] == 1 else [1, 1, 0, 0])
    allTopVerts = []
    if brickSize[0] == 1:
        for y in range(1, brickSize[1]):
            barY = (y * dimensions["width"]) - d.y
            _,verts = makeCylinder(r=r, h=height - thick.z, N=circleVerts, co=Vector((0, barY, barZ)), botFace=True, topFace=False, bme=bme)
            selectVerts(verts["top"])
            allTopVerts += verts["top"]
            if detail in ["FLAT", "LOW"] or brickSize[2] == 1:
                continue
            if brickSize[1] == 3 or brickSize[1] == 2 or y % 2 == 0 or ((y == 1 or y == brickSize[1] - 1) and brickSize[1] == 8):
                # initialize x, y, z
                x1 = -d.x + thick.x
                x2 =  d.x - thick.x
                y1 = barY - (dimensions["support_width"] / 2)
                y2 = barY + (dimensions["support_width"] / 2)
                # CREATING SUPPORT BEAM
                cubeVerts = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=sides, bme=bme)
                allTopVerts += cubeVerts[4:]
    elif brickSize[1] == 1:
        for x in range(1, brickSize[0]):
            barX = (x * dimensions["width"]) - d.x
            _,verts = makeCylinder(r=r, h=height-thick.z, N=circleVerts, co=Vector((barX, 0, barZ)), botFace=True, topFace=False, bme=bme)
            selectVerts(verts["top"])
            allTopVerts += verts["top"]
            # add supports next to odd bars
            if detail in ["FLAT", "LOW"] or brickSize[2] == 1:
                continue
            if brickSize[0] == 3 or brickSize[0] == 2 or x % 2 == 0 or ((x == 1 or x == brickSize[0] - 1) and brickSize[0] == 8):
                # initialize x, y, z
                x1 = barX - (dimensions["support_width"] / 2)
                x2 = barX + (dimensions["support_width"] / 2)
                y1 = -d.y + thick.y
                y2 =  d.y - thick.y
                # CREATING SUPPORT BEAM
                cubeVerts = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=sides, bme=bme)
                allTopVerts += cubeVerts[4:]
    if type == "SLOPE":
        cutVerts(dimensions, brickSize, allTopVerts, d, scalar, thick, bme)


def addTubeSupports(dimensions, brickSize, circleVerts, type, detail, d, scalar, thick, bme):
    _, cm, _ = getActiveContextInfo()
    addSupports = (brickSize[0] > 2 and brickSize[1] == 2) or (brickSize[1] > 2 and brickSize[0] == 2)
    bAndPBrick = cm.brickType == "BRICKS AND PLATES" and brickSize[2] == 3
    height = dimensions["height"] * (3 if bAndPBrick else 1)
    # set z1/z2 values
    z1 = d.z - thick.z - dimensions["support_height_triple" if bAndPBrick else "support_height"]
    z2 = d.z - thick.z
    allTopVerts = []
    for xNum in range(brickSize[0]-1):
        for yNum in range(brickSize[1]-1):
            tubeX = (xNum * d.x * 2) + d.x
            tubeY = (yNum * d.y * 2) + d.y
            tubeZ = (-thick.z / 2)
            r = dimensions["stud_radius"]
            h = height - thick.z
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
                    y2 = tubeY - thick.y + d.y * 2
                    y3 = tubeY + thick.y - d.y * 2
                    y4 = tubeY - r
                    # CREATING SUPPORT BEAM
                    cubeVerts1 = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=[0, 1, 1, 1, 0, 0], bme=bme)
                    cubeVerts2 = makeCube(Vector((x1, y3, z1)), Vector((x2, y4, z2)), sides=[0, 1, 1, 1, 0, 0], bme=bme)
                    allTopVerts += cubeVerts1[4:] + cubeVerts2[4:]
            elif brickSize[1] > brickSize[0]:
                if brickSize[1] == 3 or yNum % 2 == 1:
                    # initialize x, y
                    x1 = tubeX + r
                    x2 = tubeX - thick.x + d.x * 2
                    x3 = tubeX + thick.x - d.x * 2
                    x4 = tubeX - r
                    y1 = tubeY - (dimensions["support_width"] / 2)
                    y2 = tubeY + (dimensions["support_width"] / 2)
                    # CREATING SUPPORT BEAM
                    cubeVerts1 = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=[0, 1, 0, 0, 1, 1], bme=bme)
                    cubeVerts2 = makeCube(Vector((x3, y1, z1)), Vector((x4, y2, z2)), sides=[0, 1, 0, 0, 1, 1], bme=bme)
                    allTopVerts += cubeVerts1[4:] + cubeVerts2[4:]
    if type == "SLOPE":
        cutVerts(dimensions, brickSize, allTopVerts, d, scalar, thick, bme)


def cutVerts(dimensions, brickSize, verts, d, scalar, thick, bme):
    minZ = -(dimensions["height"] / 2) + thick.z
    for v in verts:
        numer = v.co.x - d.x
        denom = d.x * (scalar.x - 1) - (dimensions["tube_thickness"] + dimensions["stud_radius"]) * (brickSize[0] - 2) + (thick.z * (brickSize[0] - 3))
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
        # try:
        v1 = botVertsDofDs[str(xNum) + "," + str(yNum)]["y+"][0]
        v2 = botVertsDofDs[str(xNum-1) + "," + str(yNum)]["y+"][0]
        bme.faces.new((v1, v2, v8))
        # except ???Error:
        #     pass
        # try:
        v1 = botVertsDofDs[str(xNum) + "," + str(0)]["y-"][0]
        v2 = botVertsDofDs[str(xNum-1) + "," + str(0)]["y-"][0]
        bme.faces.new((v6, v2, v1))
        # except ???Error:
        #     pass
    for yNum in range(1, brickSize[1]):
        # try:
        v1 = botVertsDofDs[str(xNum) + "," + str(yNum)]["x+"][0]
        v2 = botVertsDofDs[str(xNum) + "," + str(yNum-1)]["x+"][0]
        bme.faces.new((v7, v2, v1))
        # except ???Error:
        #     pass
        # try:
        v1 = botVertsDofDs[str(0) + "," + str(yNum)]["x-"][0]
        v2 = botVertsDofDs[str(0) + "," + str(yNum-1)]["x-"][0]
        bme.faces.new((v1, v2, v5))
        # except ???Error:
        #     pass

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
            # try:
            v1 = botVertsDofDs[str(xNum-1) + "," + str(yNum)]["y-"][0]
            v2 = botVertsDofDs[str(xNum) + "," + str(yNum)]["y-"][0]
            v3 = botVertsDofDs[str(xNum) + "," + str(yNum-1)]["y+"][0]
            v4 = botVertsDofDs[str(xNum-1) + "," + str(yNum-1)]["y+"][0]
            bme.faces.new((v1, v2, v3, v4))
            # except ???Error:
            #     pass

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


def addTickMarks(dimensions, brickSize, circleVerts, detail, d, thick, v1, v2, v3, v4, v9, v10, v11, v12, bme):
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
            z2 = d.z - thick.z
            if xNum == 0:
                # initialize x, y
                x1 = -d.x + thick.x
                x2 = -d.x + thick.x + dimensions["tick_depth"]
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
                x1 = xNum * d.x * 2 + d.x - thick.x - dimensions["tick_depth"]
                x2 = xNum * d.x * 2 + d.x - thick.x
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
                y1 = -d.y + thick.y
                y2 = -d.y + thick.y + dimensions["tick_depth"]
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
                y1 = yNum * d.y * 2 + d.y - thick.y - dimensions["tick_depth"]
                y2 = yNum * d.y * 2 + d.y - thick.y
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
