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


def addStuds(dimensions, height, brickSize, brickType, circleVerts, bme, hollow=False, zStep=1, inset=0):
    r = dimensions["bar_radius" if hollow else "stud_radius"]
    h = dimensions["stud_height"]
    t = dimensions["stud_radius"] - dimensions["bar_radius"]
    z = height / 2 + dimensions["stud_height"] / 2 - inset / 2
    for xNum in range(brickSize[0]):
        for yNum in range(brickSize[1]):
            x = dimensions["width"] * xNum
            y = dimensions["width"] * yNum
            if hollow:
                _, studVerts = makeTube(r, h, t, circleVerts, co=Vector((0, 0, z)), bme=bme)
                selectVerts(studVerts["outer"]["bottom"] + studVerts["inner"]["bottom"])
            else:
                _, studVerts = makeCylinder(r, h + inset, circleVerts, co=Vector((x, y, z)), botFace=False, bme=bme)
                selectVerts(studVerts["bottom"])
    return studVerts


def addSupports(cm, dimensions, height, brickSize, circleVerts, type, detail, d, scalar, thick, bme, hollow=None, add_beams=None):
    # initialize vars
    if hollow is None:
        add_beams = brickSize[2] == 3 and (sum(brickSize[:2]) > 4 or min(brickSize[:2]) == 1 and max(brickSize[:2]) == 3) and detail in ["MEDIUM", "HIGH"]
    if hollow is None:
        hollow = brickSize[2] == 1 or min(brickSize[:2]) != 1
    bAndPBrick = "PLATES" in cm.brickType and brickSize[2] == 3
    sides = [0, 1] + ([0, 0, 1, 1] if brickSize[0] < brickSize[1] else [1, 1, 0, 0])
    z1 = -d.z if not hollow else d.z - thick.z - dimensions["support_height_triple" if bAndPBrick else "support_height"]
    z2 = d.z - thick.z
    r = dimensions["stud_radius"] if min(brickSize[:2]) != 1 else dimensions["bar_radius"] - (dimensions["tube_thickness"] if hollow else 0)
    h = height - thick.z
    t = dimensions["tube_thickness"]
    tubeZ = -(thick.z / 2)
    allTopVerts = []
    startX = -1 if brickSize[0] == 1 else 0
    startY = -1 if brickSize[1] == 1 else 0
    startX = 1 if type == "SLOPE" and brickSize[:2] in [[3, 1], [4, 1]] else startX
    startY = 1 if type == "SLOPE" and brickSize[:2] in [[1, 3], [1, 4]] else startY
    # add supports for each appropriate underside location
    for xNum in range(startX, brickSize[0] - 1):
        for yNum in range(startY, brickSize[1] - 1):
            # add support tubes
            tubeX = (xNum * d.x * 2) + d.x * (2 if brickSize[0] == 1 else 1)
            tubeY = (yNum * d.y * 2) + d.y * (2 if brickSize[1] == 1 else 1)
            if hollow:
                bme, tubeVerts = makeTube(r, h, t, circleVerts, co=Vector((tubeX, tubeY, tubeZ)), botFace=True, topFace=False, bme=bme)
                selectVerts(tubeVerts["outer"]["top"] + tubeVerts["inner"]["top"])
                allTopVerts += tubeVerts["outer"]["top"] + tubeVerts["inner"]["top"]
            else:
                bme, tubeVerts = makeCylinder(r, h, circleVerts, co=Vector((tubeX, tubeY, tubeZ)), botFace=True, topFace=False, bme=bme)
                selectVerts(tubeVerts["top"])
                allTopVerts += tubeVerts["top"]
            # add support beams next to odd tubes
            if not add_beams:
                continue
            if brickSize[0] > brickSize[1]:
                if brickSize[0] == 3 or xNum % 2 == brickSize[1] - min(brickSize[:2]) + 1 or (brickSize == [8, 1, 3] and xNum in [0, brickSize[0] - 2]):
                    # initialize x, y
                    x1 = tubeX - (dimensions["support_width"] / 2)
                    x2 = tubeX + (dimensions["support_width"] / 2)
                    y1 = tubeY + r
                    y2 = tubeY + d.y * min(brickSize[:2]) - thick.x
                    y3 = tubeY - d.y * min(brickSize[:2]) + thick.y
                    y4 = tubeY - r
                    # CREATING SUPPORT BEAM
                    cubeVerts1 = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=sides, bme=bme)
                    cubeVerts2 = makeCube(Vector((x1, y3, z1)), Vector((x2, y4, z2)), sides=sides, bme=bme)
                    allTopVerts += cubeVerts1[4:] + cubeVerts2[4:]
            if brickSize[1] > brickSize[0]:
                if brickSize[1] == 3 or yNum % 2 == brickSize[0] - min(brickSize[:2]) + 1 or (brickSize == [1, 8, 3] and yNum in [0, brickSize[1] - 2]):
                    # initialize x, y
                    x1 = tubeX + r
                    x2 = tubeX + d.x * min(brickSize[:2]) - thick.x
                    x3 = tubeX - d.x * min(brickSize[:2]) + thick.y
                    x4 = tubeX - r
                    y1 = tubeY - (dimensions["support_width"] / 2)
                    y2 = tubeY + (dimensions["support_width"] / 2)
                    # CREATING SUPPORT BEAM
                    cubeVerts1 = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=sides, bme=bme)
                    cubeVerts2 = makeCube(Vector((x3, y1, z1)), Vector((x4, y2, z2)), sides=sides, bme=bme)
                    allTopVerts += cubeVerts1[4:] + cubeVerts2[4:]
    if type == "SLOPE":
        cutVerts(dimensions, height, brickSize, allTopVerts, d, scalar, thick, bme)


def cutVerts(dimensions, height, brickSize, verts, d, scalar, thick, bme):
    minZ = -(height / 2) + thick.z
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
    joinVerts = {"X+":[], "Y+":[], "X-":[], "Y-":[]}
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
                joinVerts["X-"] += [v1, v2]
            elif xNum == brickSize[0]-1:
                # initialize x, y
                x1 = xNum * d.x * 2 + d.x - thick.x - dimensions["tick_depth"]
                x2 = xNum * d.x * 2 + d.x - thick.x
                y1 = yNum * d.y * 2 - dimensions["tick_width"] / 2
                y2 = yNum * d.y * 2 + dimensions["tick_width"] / 2
                # CREATING SUPPORT BEAM
                _, _, v3, v4, v5, _, _, v8 = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=[0, 1, 0, 1, 1, 1], bme=bme)
                selectVerts([v3, v4, v5, v8])
                joinVerts["X+"] += [v4, v3]
            if yNum == 0:
                # initialize x, y
                y1 = -d.y + thick.y
                y2 = -d.y + thick.y + dimensions["tick_depth"]
                x1 = xNum * d.x * 2 - dimensions["tick_width"] / 2
                x2 = xNum * d.x * 2 + dimensions["tick_width"] / 2
                # CREATING SUPPORT BEAM
                v1, _, _, v4, _, _, v7, v8 = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=[0, 1, 1, 1, 1, 0], bme=bme)
                selectVerts([v1, v4, v7, v8])
                joinVerts["Y-"] += [v1, v4]
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
                joinVerts["Y+"] += [v2, v3]

    bme.faces.new([nni, nno, npo, npi] + joinVerts["X-"][::-1])
    bme.faces.new([ppi, ppo, pno, pni] + joinVerts["X+"])
    bme.faces.new([pni, pno, nno, nni] + joinVerts["Y-"])
    bme.faces.new([npi, npo, ppo, ppi] + joinVerts["Y+"][::-1])


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
