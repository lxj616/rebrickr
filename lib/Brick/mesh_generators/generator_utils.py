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

# Addon imports
from .geometric_shapes import *
from .generator_utils import *
from ....functions import *


def addSupports(cm, dimensions, height, brickSize, circleVerts, type, detail, d, scalar, thick, bme, hollow=None, add_beams=None):
    # initialize vars
    if hollow is None:
        add_beams = brickSize[2] == 3 and (sum(brickSize[:2]) > 4 or min(brickSize[:2]) == 1 and max(brickSize[:2]) == 3) and detail in ["MEDIUM", "HIGH"]
    if hollow is None:
        hollow = brickSize[2] == 1 or min(brickSize[:2]) != 1
    bAndPBrick = flatBrickType(cm) and brickSize[2] == 3
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
    r = dimensions["stud_radius"]-(2 * thickZ)
    N = circleVerts
    h = thickZ * 0.99
    for xNum in range(brickSize[0]):
        for yNum in range(brickSize[1]):
            bme, innerCylinderVerts = makeCylinder(r, h, N, co=Vector((xNum*d.x*2,yNum*d.y*2,d.z - thickZ + h/2)), botFace=False, flipNormals=True, bme=bme)
            botVertsD = createVertListDict(innerCylinderVerts["bottom"])
            botVertsDofDs["%(xNum)s,%(yNum)s" % locals()] = botVertsD
    connectCirclesToSquare(dimensions, brickSize, circleVerts, v5, v6, v7, v8, botVertsDofDs, xNum, yNum, bme, step=1)


def addStuds(dimensions, height, brickSize, brickType, circleVerts, bme, v5=None, v6=None, v7=None, v8=None, hollow=False, botFace=True, loopCut=False):
    r = dimensions["bar_radius" if hollow else "stud_radius"]
    h = dimensions["stud_height"]
    t = dimensions["stud_radius"] - dimensions["bar_radius"]
    z = height / 2 + dimensions["stud_height"] / 2
    # make studs
    topVertsDofDs = {}
    for xNum in range(brickSize[0]):
        for yNum in range(brickSize[1]):
            x = dimensions["width"] * xNum
            y = dimensions["width"] * yNum
            if hollow:
                _, studVerts = makeTube(r, h, t, circleVerts, co=Vector((0, 0, z)), loopCut=loopCut, botFace=botFace, bme=bme)
                if v5 is not None: bme.faces.new(studVerts["inner"]["bottom"])
                select(studVerts["inner"]["mid" if loopCut else "bottom"] + studVerts["outer"]["mid" if loopCut else "bottom"])
            else:
                # split stud at center by creating cylinder and circle and joining them (allows Bevel to work correctly)
                _, studVerts = makeCylinder(r, h, circleVerts, co=Vector((x, y, z)), botFace=False, loopCut=loopCut, bme=bme)
                select(studVerts["mid" if loopCut else "bottom"])
            if v5 is not None:
                topVertsD = createVertListDict2(studVerts["outer"]["bottom"] if hollow else studVerts["bottom"])
                topVertsDofDs["%(xNum)s,%(yNum)s" % locals()] = topVertsD
    if v5 is not None:
        connectCirclesToSquare(dimensions, brickSize, circleVerts, v5, v6, v7, v8, topVertsDofDs, xNum, yNum, bme, step=-1)
    return studVerts


def connectCirclesToSquare(dimensions, brickSize, circleVerts, v5, v6, v7, v8, vertsDofDs, xNum, yNum, bme, step=1):
    thickZ = dimensions["thickness"]
    # Make corner faces
    vList = vertsDofDs["0,0"]["y-"] + vertsDofDs["0,0"]["--"] + vertsDofDs["0,0"]["x-"]
    for i in range(1, len(vList)):
        bme.faces.new([vList[i], vList[i-1], v5][::step])
    vList = vertsDofDs[str(xNum) + "," + str(0)]["x+"] + vertsDofDs[str(xNum) + "," + str(0)]["+-"] + vertsDofDs[str(xNum) + "," + str(0)]["y-"]
    for i in range(1, len(vList)):
        bme.faces.new([vList[i], vList[i-1], v6][::step])
    vList = vertsDofDs[str(xNum) + "," + str(yNum)]["y+"] + vertsDofDs[str(xNum) + "," + str(yNum)]["++"] + vertsDofDs[str(xNum) + "," + str(yNum)]["x+"]
    for i in range(1, len(vList)):
        bme.faces.new([vList[i], vList[i-1], v7][::step])
    vList = vertsDofDs[str(0) + "," + str(yNum)]["x-"] + vertsDofDs[str(0) + "," + str(yNum)]["-+"] + vertsDofDs[str(0) + "," + str(yNum)]["y+"]
    for i in range(1, len(vList)):
        bme.faces.new([vList[i], vList[i-1], v8][::step])

    # Make edge faces
    joinVerts = {"Y+":[v7, v8], "Y-":[v6, v5], "X+":[v7, v6], "X-":[v8, v5]}
    for xNum in range(brickSize[0]):
        vertD = vertsDofDs[str(xNum) + "," + str(yNum)]
        joinVerts["Y+"].append(vertD["y+"][0])
        vertD = vertsDofDs[str(xNum) + "," + str(0)]
        joinVerts["Y-"].append(vertD["y-"][0])
    for yNum in range(brickSize[1]):
        vertD = vertsDofDs[str(xNum) + "," + str(yNum)]
        joinVerts["X+"].append(vertD["x+"][0])
        vertD = vertsDofDs[str(0) + "," + str(yNum)]
        joinVerts["X-"].append(vertD["x-"][0])
    for item in joinVerts:
        step0 = -step if item in ["Y+", "X-"] else step
        bme.faces.new(joinVerts[item][::step0])

    # Make in-between-insets faces along x axis
    for xNum in range(1, brickSize[0]):
        for yNum in range(brickSize[1]):
            vList1 = vertsDofDs[str(xNum-1) + "," + str(yNum)]["y+"] + vertsDofDs[str(xNum-1) + "," + str(yNum)]["++"] + vertsDofDs[str(xNum-1) + "," + str(yNum)]["x+"] + vertsDofDs[str(xNum-1) + "," + str(yNum)]["+-"] + vertsDofDs[str(xNum-1) + "," + str(yNum)]["y-"]
            vList2 = vertsDofDs[str(xNum) + "," + str(yNum)]["y+"] + vertsDofDs[str(xNum) + "," + str(yNum)]["-+"][::-1] + vertsDofDs[str(xNum) + "," + str(yNum)]["x-"] + vertsDofDs[str(xNum) + "," + str(yNum)]["--"][::-1] + vertsDofDs[str(xNum) + "," + str(yNum)]["y-"]
            if len(vList1) > len(vList2):
                v1 = vList1[-1]
                v2 = vList1[-2]
                v3 = vList2[-1]
                bme.faces.new([v1, v2, v3][::step])
                numIters = len(vList2)
            elif len(vList1) < len(vList2):
                v1 = vList1[-1]
                v2 = vList2[-2]
                v3 = vList2[-1]
                bme.faces.new([v1, v2, v3][::step])
                numIters = len(vList1)
            else:
                numIters = len(vList1)
            for i in range(1, numIters):
                v1 = vList1[i]
                v2 = vList1[i-1]
                v3 = vList2[i-1]
                v4 = vList2[i]
                bme.faces.new([v1, v2, v3, v4][::step])

    # Make in-between-inset quads
    for yNum in range(1, brickSize[1]):
        for xNum in range(1, brickSize[0]):
            # try:
            v1 = vertsDofDs[str(xNum-1) + "," + str(yNum)]["y-"][0]
            v2 = vertsDofDs[str(xNum) + "," + str(yNum)]["y-"][0]
            v3 = vertsDofDs[str(xNum) + "," + str(yNum-1)]["y+"][0]
            v4 = vertsDofDs[str(xNum-1) + "," + str(yNum-1)]["y+"][0]
            bme.faces.new([v1, v2, v3, v4][::step])
            # except ???Error:
            #     pass

    # Make final in-between-insets faces on extremes of x axis along y axis
    for yNum in range(1, brickSize[1]):
        vList1 = vertsDofDs[str(0) + "," + str(yNum-1)]["x-"] + vertsDofDs[str(0) + "," + str(yNum-1)]["-+"] + vertsDofDs[str(0) + "," + str(yNum-1)]["y+"]
        vList2 = vertsDofDs[str(0) + "," + str(yNum)]["x-"] + vertsDofDs[str(0) + "," + str(yNum)]["--"][::-1] + vertsDofDs[str(0) + "," + str(yNum)]["y-"]
        if len(vList1) > len(vList2):
            v1 = vList1[-1]
            v2 = vList1[-2]
            v3 = vList2[-1]
            bme.faces.new([v1, v2, v3][::step])
            numIters = len(vList2)
        elif len(vList1) < len(vList2):
            v1 = vList1[-1]
            v2 = vList2[-2]
            v3 = vList2[-1]
            bme.faces.new([v1, v2, v3][::step])
            numIters = len(vList1)
        else:
            numIters = len(vList1)
        for i in range(1, numIters):
            v1 = vList1[i]
            v2 = vList1[i-1]
            v3 = vList2[i-1]
            v4 = vList2[i]
            bme.faces.new([v1, v2, v3, v4][::step])
    for yNum in range(1, brickSize[1]):
        vList1 = vertsDofDs[str(xNum) + "," + str(yNum-1)]["x+"] + vertsDofDs[str(xNum) + "," + str(yNum-1)]["++"][::-1] + vertsDofDs[str(xNum) + "," + str(yNum-1)]["y+"]
        vList2 = vertsDofDs[str(xNum) + "," + str(yNum)]["x+"] + vertsDofDs[str(xNum) + "," + str(yNum)]["+-"] + vertsDofDs[str(xNum) + "," + str(yNum)]["y-"]
        if len(vList1) > len(vList2):
            v1 = vList1[-1]
            v2 = vList2[-1]
            v3 = vList1[-2]
            bme.faces.new([v1, v2, v3][::step])
            numIters = len(vList2)
        elif len(vList1) < len(vList2):
            v1 = vList2[-1]
            v2 = vList2[-2]
            v3 = vList1[-1]
            bme.faces.new([v1, v2, v3][::step])
            numIters = len(vList1)
        else:
            numIters = len(vList1)
        for i in range(1, numIters):
            v1 = vList2[i]
            v2 = vList2[i-1]
            v3 = vList1[i-1]
            v4 = vList1[i]
            bme.faces.new([v1, v2, v3, v4][::step])


def addTickMarks(dimensions, brickSize, circleVerts, detail, d, thick, nno, npo, ppo, pno, nni, npi, ppi, pni, nnt, npt, ppt, pnt, bme):
    # for edge vert refs, n=negative, p=positive, o=outer, i=inner, t=top
    joinVerts = {"X-":[npi, npo, nno, nni], "X+":[ppi, ppo, pno, pni], "Y-":[pni, pno, nno, nni], "Y+":[ppi, ppo, npo, npi]}
    lastSideVerts = {"X-":[nnt, nni], "X+":[pni, pnt], "Y-":[nni, nnt], "Y+":[npt, npi]}
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
                v1, v2, _, _, v5, v6, v7, v8 = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=[0, 1, 1, 0, 1, 1], bme=bme)
                selectVerts([v6, v7])
                joinVerts["X-"] += [v1, v2]
                bme.faces.new([v1, v5] + lastSideVerts["X-"])
                lastSideVerts["X-"] = [v8, v2]
            elif xNum == brickSize[0]-1:
                # initialize x, y
                x1 = xNum * d.x * 2 + d.x - thick.x - dimensions["tick_depth"]
                x2 = xNum * d.x * 2 + d.x - thick.x
                y1 = yNum * d.y * 2 - dimensions["tick_width"] / 2
                y2 = yNum * d.y * 2 + dimensions["tick_width"] / 2
                # CREATING SUPPORT BEAM
                _, _, v3, v4, v5, v6, v7, v8 = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=[0, 1, 0, 1, 1, 1], bme=bme)
                selectVerts([v5, v8])
                joinVerts["X+"] += [v4, v3]
                bme.faces.new([v6, v4] + lastSideVerts["X+"])
                lastSideVerts["X+"] = [v3, v7]
            if yNum == 0:
                # initialize x, y
                y1 = -d.y + thick.y
                y2 = -d.y + thick.y + dimensions["tick_depth"]
                x1 = xNum * d.x * 2 - dimensions["tick_width"] / 2
                x2 = xNum * d.x * 2 + dimensions["tick_width"] / 2
                # CREATING SUPPORT BEAM
                v1, _, _, v4, v5, v6, v7, v8 = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=[0, 1, 1, 1, 1, 0], bme=bme)
                selectVerts([v7, v8])
                joinVerts["Y-"] += [v1, v4]
                bme.faces.new([v5, v1] + lastSideVerts["Y-"])
                lastSideVerts["Y-"] = [v4, v6]
            elif yNum == brickSize[1]-1:
                # initialize x, y
                x1 = xNum * d.x * 2 - dimensions["tick_width"] / 2
                x2 = xNum * d.x * 2 + dimensions["tick_width"] / 2
                y1 = yNum * d.y * 2 + d.y - thick.y - dimensions["tick_depth"]
                y2 = yNum * d.y * 2 + d.y - thick.y
                # CREATING SUPPORT BEAM
                _, v2, v3, _, v5, v6, v7, v8 = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), sides=[0, 1, 1, 1, 0, 1], bme=bme)
                # select bottom connecting verts for exclusion from vertex group
                selectVerts([v5, v6])
                joinVerts["Y+"] += [v2, v3]
                bme.faces.new([v2, v8] + lastSideVerts["Y+"])
                lastSideVerts["Y+"] = [v7, v3]

    # draw faces between ticks and base
    bme.faces.new(joinVerts["X-"][::-1])
    bme.faces.new(joinVerts["X+"])
    bme.faces.new(joinVerts["Y-"])
    bme.faces.new(joinVerts["Y+"][::-1])
    bme.faces.new([npi, npt] + lastSideVerts["X-"])
    bme.faces.new([ppt, ppi] + lastSideVerts["X+"])
    bme.faces.new([pnt, pni] + lastSideVerts["Y-"])
    bme.faces.new([ppi, ppt] + lastSideVerts["Y+"])


def createVertListDict(verts):
    idx1 = int(round(len(verts) * 1 / 4)) - 1
    idx2 = int(round(len(verts) * 2 / 4)) - 1
    idx3 = int(round(len(verts) * 3 / 4)) - 1
    idx4 = int(round(len(verts) * 4 / 4)) - 1

    vertListBDict = {"++":[verts[idx] for idx in range(idx1 + 1, idx2)],
                     "+-":[verts[idx] for idx in range(idx2 + 1, idx3)],
                     "--":[verts[idx] for idx in range(idx3 + 1, idx4)],
                     "-+":[verts[idx] for idx in range(0,        idx1)],
                     "y+":[verts[idx1]],
                     "x+":[verts[idx2]],
                     "y-":[verts[idx3]],
                     "x-":[verts[idx4]]}

    return vertListBDict


def createVertListDict2(verts):
    idx1 = int(round(len(verts) * 1 / 4)) - 1
    idx2 = int(round(len(verts) * 2 / 4)) - 1
    idx3 = int(round(len(verts) * 3 / 4)) - 1
    idx4 = int(round(len(verts) * 4 / 4)) - 1

    vertListBDict = {"--":[verts[idx] for idx in range(idx1 + 1, idx2)],
                     "-+":[verts[idx] for idx in range(idx2 + 1, idx3)],
                     "++":[verts[idx] for idx in range(idx3 + 1, idx4)],
                     "+-":[verts[idx] for idx in range(0,        idx1)],
                     "y-":[verts[idx1]],
                     "x-":[verts[idx2]],
                     "y+":[verts[idx3]],
                     "x+":[verts[idx4]]}

    return vertListBDict


def addGrillDetails(dimensions, brickSize, thick, scalar, d, v1, v2, v3, v4, v9, v10, v11, v12, bme):
    # NOTE: n=negative, p=positive, m=middle
    # inner support in middle
    x1 = dimensions["stud_radius"]
    x2 = dimensions["stud_radius"] + (d.x - dimensions["stud_radius"]) * 2
    y1 = -dimensions["thickness"] / 2
    y2 =  dimensions["thickness"] / 2
    z1 = -d.z
    z2 = d.z - dimensions["thickness"]
    mms = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), [0, 1, 1, 1, 1, 1], bme=bme)

    z1 = d.z - dimensions["thickness"]
    z2 = d.z
    # upper middle x- grill
    x1 = -d.x
    x2 = -d.x + dimensions["thickness"]
    nmg = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), [1, 0, 0, 1, 1, 1], bme=bme)
    # upper y- x- grill
    y3 = y1 - dimensions["thickness"] * 2
    y4 = y2 - dimensions["thickness"] * 2
    nng = makeCube(Vector((x1, y3, z1)), Vector((x2, y4, z2)), [1, 0, 0, 1, 1, 1], bme=bme)
    bme.verts.remove(nng[3])
    nng[3] = None
    # upper y+ x- grill
    y3 = y1 + dimensions["thickness"] * 2
    y4 = y2 + dimensions["thickness"] * 2
    npg = makeCube(Vector((x1, y3, z1)), Vector((x2, y4, z2)), [1, 0, 0, 1, 1, 1], bme=bme)
    bme.verts.remove(npg[2])
    npg[2] = None

    # upper middle x+ grill
    x1 = d.x * 3 - dimensions["thickness"]
    x2 = d.x * 3
    pmg = makeCube(Vector((x1, y1, z1)), Vector((x2, y2, z2)), [1, 0, 1, 0, 1, 1], bme=bme)
    # upper y- x+ grill
    y3 = y1 - dimensions["thickness"] * 2
    y4 = y2 - dimensions["thickness"] * 2
    png = makeCube(Vector((x1, y3, z1)), Vector((x2, y4, z2)), [1, 0, 1, 0, 1, 1], bme=bme)
    bme.verts.remove(png[0])
    png[0] = None
    # upper y+ x+ grill
    y3 = y1 + dimensions["thickness"] * 2
    y4 = y2 + dimensions["thickness"] * 2
    ppg = makeCube(Vector((x1, y3, z1)), Vector((x2, y4, z2)), [1, 0, 1, 0, 1, 1], bme=bme)
    bme.verts.remove(ppg[1])
    ppg[1] = None

    # connect grill tops
    bme.faces.new((pmg[4], pmg[7], nmg[6], nmg[5]))
    bme.faces.new((png[4], png[7], nng[6], nng[5]))
    bme.faces.new((ppg[4], ppg[7], npg[6], npg[5]))
    # connect outer sides
    bme.faces.new((v4, png[3], png[5], nng[4], nng[0], v1))
    bme.faces.new((v2, npg[1], npg[7], ppg[6], ppg[2], v3))
    bme.faces.new((v3, ppg[2], ppg[3], pmg[2], pmg[3], png[2], png[3], v4))
    bme.faces.new((v1, nng[0], nng[1], nmg[0], nmg[1], npg[0], npg[1], v2))
    # connect grills together
    bme.faces.new((nng[1], nng[2], nmg[3], nmg[0]))
    bme.faces.new((nmg[1], nmg[2], npg[3], npg[0]))
    bme.faces.new((png[1], png[2], pmg[3], pmg[0]))
    bme.faces.new((pmg[1], pmg[2], ppg[3], ppg[0]))
    bme.faces.new((nmg[5], nmg[3], mms[4], mms[5], pmg[0], pmg[4]))
    bme.faces.new((pmg[7], pmg[1], mms[6], mms[7], nmg[2], nmg[6]))
    # connect grill to base
    bme.faces.new((nmg[2], mms[7], mms[4], nmg[3]))
    bme.faces.new((pmg[0], mms[5], mms[6], pmg[1]))
    # create square at inner base
    coord1 = -d + Vector((thick.x, thick.y, 0))
    coord2 = vec_mult(d, scalar) - thick
    coord2.z = -d.z
    v17, v18, v19, v20 = makeSquare(coord1, coord2, face=False, bme=bme)
    # connect inner base to outer base
    bme.faces.new((v17, v9, v10, v20))
    bme.faces.new((v20, v10, v11, v19))
    bme.faces.new((v19, v11, v12, v18))
    bme.faces.new((v18, v12, v9, v17))
    # create inner faces
    if brickSize[0] < brickSize[1]:
        bme.faces.new((v17, v20, ppg[0], ppg[4], npg[5], npg[4]))
        bme.faces.new((v19, v18, nng[2], nng[6], png[7], png[1]))
        bme.faces.new((v20, v19, png[1], pmg[0], pmg[1], ppg[0]))
        bme.faces.new((v18, v17, npg[3], nmg[2], nmg[3], nng[2]))
    else:
        bme.faces.new((v20, v19, ppg[0], ppg[4], npg[5], npg[4]))
        bme.faces.new((v18, v17, nng[2], nng[6], png[7], png[1]))
        bme.faces.new((v19, v18, png[1], pmg[0], pmg[1], ppg[0]))
        bme.faces.new((v17, v20, npg[3], nmg[2], nmg[3], nng[2]))

    # rotate created vertices in to place if necessary
    if brickSize[0] < brickSize[1]:
        vertsCreated = nng + nmg + npg + png + pmg + ppg + mms
        vertsCreated = [v for v in vertsCreated if v is not None]
        bmesh.ops.rotate(bme, verts=vertsCreated, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, 'Z'))
