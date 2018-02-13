import bpy
import bmesh
import math
from mathutils import Matrix, Vector
from ...functions.common import *


def makeCube(coord1, coord2, sides=[False]*6, flipNormals=False, bme=None):
    """
    Keyword Arguments:
        coord1 -- back/left/bottom corner of the cube (furthest negative in all three axes)
        coord2 -- front/right/top  corner of the cube (furthest positive in all three axes)
        sides  -- draw sides [+z, -z, +x, -x, +y, -y]
        bme    -- bmesh object in which to create verts

    """

    assert coord1[0] < coord2[0]
    assert coord1[1] < coord2[1]
    assert coord1[2] < coord2[2]

    # create new bmesh object
    if bme is None:
        bme = bmesh.new()

    # create vertices
    vList = []
    for x in [coord1[0], coord2[0]]:
        for y in [coord1[1], coord2[1]]:
            for z in [coord1[2], coord2[2]]:
                vList.append(bme.verts.new((x, y, z)))

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

    return vList

# r = radius, N = numVerts, h = height, co = target cylinder position, botFace = Bool for creating face on bottom, bme = bmesh to insert mesh data into
def makeCylinder(r, N, h, co:Vector=Vector((0,0,0)), botFace=True, topFace=True, flipNormals=False, bme=None):
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
    for v in range(N):
        idx1 = v if flipNormals else (v-1)
        idx2 = (v-1) if flipNormals else v
        sideFaces.append(bme.faces.new((topVerts[idx1], botVerts[idx1], botVerts[idx2], topVerts[idx2])))
    # set side faces to smooth
    for f in sideFaces:
        f.smooth = True

    # create top and bottom faces
    if topFace:
        bme.faces.new(topVerts if not flipNormals else topVerts[::-1])
    if botFace:
        bme.faces.new(botVerts[::-1] if not flipNormals else botVerts)

    # return bmesh
    return bme, botVerts[::-1], topVerts

# r = radius, N = numVerts, h = height, t = thickness, co = target cylinder position
def makeTube(r, N, h, t, co:Vector=Vector((0,0,0)), wings=False, bme=None):
    # create new bmesh object
    if bme == None:
        bme = bmesh.new()

    # create upper and lower circles
    for i in range(N):
        bme, vertListBInner, vertListTInner = makeCylinder(r, N, h, co=co, botFace=False, topFace=False, flipNormals=True, bme=bme)
        bme, vertListBOuter, vertListTOuter = makeCylinder(r + t, N, h, co=co, botFace=False, topFace=False, bme=bme)
    for i in range(len(vertListBInner)):
        bme.faces.new((vertListBOuter[i], vertListBInner[i], vertListBInner[i-1], vertListBOuter[i-1]))
    # select top verts for exclusion from vert group
    for lst in [vertListTOuter, vertListTInner]:
        for v in lst:
            v.select = True

    # return bmesh
    return bme

# r = radius, N = numVerts, h = height, o = z offset, co = target cylinder position, bme = bmesh to insert mesh data into
def makeInnerCylinder(r, N, h, co:Vector=Vector((0,0,0)), bme=None):
    """ Make a brick inner cylinder """

    # create new bmesh object
    if bme == None:
        bme = bmesh.new()

    # shift co down by half the hight
    co.z = co.z + h/2

    # create cylinder
    bme, vertListB, vertListT = makeCylinder(r, N, h, co=co, botFace=False, flipNormals=True, bme=bme)

    idx4 = len(vertListB) - 1
    idx1 = int(round(len(vertListB) * 1 / 4)) - 1
    idx2 = int(round(len(vertListB) * 2 / 4)) - 1
    idx3 = int(round(len(vertListB) * 3 / 4)) - 1

    vertListBDict = {"++":[vertListB[idx] for idx in range(idx1 + 1, idx2)],
                     "+-":[vertListB[idx] for idx in range(idx2 + 1, idx3)],
                     "--":[vertListB[idx] for idx in range(idx3 + 1, idx4)],
                     "-+":[vertListB[idx] for idx in range(0,        idx1)],
                     "y+":[vertListB[idx1]],
                     "x+":[vertListB[idx2]],
                     "y-":[vertListB[idx3]],
                     "x-":[vertListB[idx4]]}

    return vertListBDict

def makeBrick(dimensions, brickSize, numStudVerts=None, detail="Low Detail", logo=None, stud=True, bme=None):
    # create new bmesh object
    if not bme:
        bme = bmesh.new()
    scn, cm, _ = getActiveContextInfo()

    # set scale and thickness variables
    d = Vector((dimensions["width"] / 2, dimensions["width"] / 2, dimensions["height"] / 2))
    if cm.brickType != "Bricks":
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
    if cm.brickType in ["Bricks and Plates"] and brickSize[2] == 3:
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
    v1, v2, v3, v4, v5, v6, v7, v8 = makeCube((x1, y1, z1), (x2, y2, z2), [1, 1 if detail == "Flat" else 0, 1, 1, 1, 1], bme=bme)

    # CREATING STUD(S)
    if stud:
        studInset = thickZ * 0.9
        for xNum in range(brickSize[0]):
            for yNum in range(brickSize[1]):
                if cm.brickType == "Bricks and Plates" and brickSize[2] == 3:
                    zCO = dimensions["stud_offset_triple"]-(studInset/2)
                else:
                    zCO = dimensions["stud_offset"]-(studInset/2)
                _,botVerts,_ = makeCylinder(r=dimensions["stud_radius"], N=numStudVerts, h=dimensions["stud_height"]+studInset, co=Vector((xNum*d.x*2,yNum*d.y*2,zCO)), botFace=False, bme=bme)
                for v in botVerts:
                    v.select = True

    if detail != "Flat":
        # creating cylinder
        # making verts for hollow portion
        x1 = v2.co.x + thickXY
        x2 = v6.co.x - thickXY
        y1 = v2.co.y + thickXY
        y2 = v4.co.y - thickXY
        z1 = v1.co.z
        z2 = d.z - thickZ
        v9, v10, v11, v12, v13, v14, v15, v16 = makeCube((x1, y1, z1), (x2, y2, z2), [1 if detail == "Low Detail" else 0, 0, 1, 1, 1, 1], flipNormals=True, bme=bme)
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
                        v1, v2, v3, v4, _, _, _, _ = makeCube((x1, y1, z1), (x2, y2, z2), sides=[0, 1, 1, 0, 1, 1], bme=bme)
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
                        _, _, _, _, v5, v6, v7, v8 = makeCube((x1, y1, z1), (x2, y2, z2), sides=[0, 1, 0, 1, 1, 1], bme=bme)
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
                        v1, v2, _, _, v5, v6, _, _ = makeCube((x1, y1, z1), (x2, y2, z2), sides=[0, 1, 1, 1, 1, 0], bme=bme)
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
                        _, _, v3, v4, _, _, v7, v8 = makeCube((x1, y1, z1), (x2, y2, z2), sides=[0, 1, 1, 1, 0, 1], bme=bme)
                        # select bottom connecting verts for exclusion from vertex group
                        to_select += [v3, v4, v7, v8]
                        if xNum == 0:
                            bme.faces.new((v3, npi, npo))
                            pass
                        else:
                            bme.faces.new((npo, v3, yN1v))
                        if xNum == brickSize[0]-1:
                            bme.faces.new((v7, ppo, ppi))
                            bme.faces.new((v7, v3, npo, ppo))
                            pass
                        else:
                            bme.faces.new((v7, v3, npo))
                            pass
                        yN1v = v7
                    # select verts for exclusion from vertex group
                    for v in to_select:
                        v.select = True
        else:
            # make faces on bottom edges of brick
            bme.faces.new((v1,  v9,  v13, v5))
            bme.faces.new((v1,  v3,  v11, v9))
            bme.faces.new((v15, v7,  v5,  v13))
            bme.faces.new((v15, v11, v3,  v7))
            pass


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
                t = (d.z*2)-thickZ
                makeTube(r, numStudVerts, t, dimensions["tube_thickness"], co=Vector((tubeX, tubeY, tubeZ)), wings=True, bme=bme)
                # add support next to odd tubes
                if not (detail == "Medium Detail" or detail == "High Detail") or not addSupports or brickSize[2] == 1:
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
                        makeCube((x1, y1, z1), (x2, y2, z2), sides=[0, 1, 1, 1, 0, 0], bme=bme)
                        makeCube((x1, y3, z1), (x2, y4, z2), sides=[0, 1, 1, 1, 0, 0], bme=bme)
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
                        makeCube((x1, y1, z1), (x2, y2, z2), sides=[0, 1, 0, 0, 1, 1], bme=bme)
                        makeCube((x3, y1, z1), (x4, y2, z2), sides=[0, 1, 0, 0, 1, 1], bme=bme)
        # Adding bar inside 1 by x bricks
        if brickSize[0] == 1:
            for y in range(1, brickSize[1]):
                barX = 0
                barY = (y * d.y * 2) - d.y
                barZ = -thickZ/2
                r = dimensions["bar_radius"]
                _,_,topVerts = makeCylinder(r=r, N=numStudVerts, h=(d.z*2)-thickZ, co=Vector((barX, barY, barZ)), botFace=True, topFace=False, bme=bme)
                # select top verts for exclusion from vert group
                for v in topVerts:
                    v.select = True
                if (detail == "Medium Detail" or detail == "High Detail") and brickSize[2] != 1:
                    if brickSize[1] == 3 or brickSize[1] == 2 or y % 2 == 0 or ((y == 1 or y == brickSize[1]-1) and brickSize[1] == 8):
                        # initialize x, y, z
                        x1 = barX - d.x+thickXY
                        x2 = barX + d.x-thickXY
                        y1 = barY - (dimensions["support_width"]/2)
                        y2 = barY + (dimensions["support_width"]/2)
                        # CREATING SUPPORT BEAM
                        makeCube((x1, y1, z1), (x2, y2, z2), sides=[0, 1, 0, 0, 1, 1], bme=bme)
        if brickSize[1] == 1:
            for x in range(1, brickSize[0]):
                barX = (x * d.x * 2) - d.x
                barY = 0
                barZ = -thickZ/2
                r = dimensions["bar_radius"]
                _,_,topVerts = makeCylinder(r=r, N=numStudVerts, h=(d.z*2)-thickZ, co=Vector((barX, barY, barZ)), botFace=True, topFace=False, bme=bme)
                # select top verts for exclusion from vert group
                for v in topVerts:
                    v.select = True
                # add supports next to odd bars
                if not (detail == "Medium Detail" or detail == "High Detail") or brickSize[2] == 1:
                    continue
                if brickSize[0] == 3 or brickSize[0] == 2 or x % 2 == 0 or ((x == 1 or x == brickSize[0]-1) and brickSize[0] == 8):
                    # initialize x, y, z
                    x1 = barX - (dimensions["support_width"]/2)
                    x2 = barX + (dimensions["support_width"]/2)
                    y1 = barY - d.y+thickXY
                    y2 = barY + d.y-thickXY
                    # CREATING SUPPORT BEAM
                    makeCube((x1, y1, z1), (x2, y2, z2), sides=[0, 1, 1, 1, 0, 0], bme=bme)
        # make face at top
        if detail in ["Medium Detail", "High Detail"]:
            # make small inner cylinder at top
            botVertsDofDs = {}
            for xNum in range(brickSize[0]):
                for yNum in range(brickSize[1]):
                    r = dimensions["stud_radius"]-(2 * thickZ)
                    N = numStudVerts
                    h = thickZ * 0.99
                    botVertsD = makeInnerCylinder(r, N, h, co=Vector((xNum*d.x*2,yNum*d.y*2,d.z-thickZ)), bme=bme)
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

def newObjFromBmesh(layer, bme, meshName, objName=False):

    # if only one name given, use it for both names
    if not objName:
        objName = meshName

    # create mesh and object
    me = bpy.data.meshes.new(meshName)
    ob = bpy.data.objects.new(objName, me)

    scn = bpy.context.scene # grab a reference to the scene
    scn.objects.link(ob)    # link new object to scene
    scn.objects.active = ob # make new object active
    ob.select = True        # make new object selected (does not deselect
                             # other objects)

    obj = bme.to_mesh(me)         # push bmesh data into me

    # move to appropriate layer
    layerList = []
    for i in range(20):
        layerList.append(i == layer-1)
    bpy.ops.object.move_to_layer(layers=layerList)
    setLayers(layerList)
    bpy.ops.object.select_all(action='TOGGLE')
    return ob

def deleteExisting():
    scn = bpy.context.scene
    # delete existing objects
    tmpList = [True]*20
    scn.layers = tmpList
    for i in range(2):
        bpy.ops.object.select_all(action='TOGGLE')
        bpy.ops.object.delete()
    scn.layers = ([False]*19) + [True]

def get_dimensions(height=1, zScale=1, gap_percentage=0.01):
    scale = height/9.6
    brick_dimensions = {}
    brick_dimensions["height"] = scale*9.6*zScale
    brick_dimensions["width"] = scale*8
    brick_dimensions["gap"] = scale*9.6*gap_percentage
    brick_dimensions["stud_height"] = scale*1.8
    brick_dimensions["stud_diameter"] = scale*4.8
    brick_dimensions["stud_radius"] = scale*2.4
    brick_dimensions["stud_offset"] = (brick_dimensions["height"] / 2) + (brick_dimensions["stud_height"] / 2)
    brick_dimensions["thickness"] = scale*1.6
    brick_dimensions["tube_thickness"] = scale*0.855
    brick_dimensions["bar_radius"] = scale*1.6
    brick_dimensions["logo_width"] = scale*3.74
    brick_dimensions["support_width"] = scale*0.8
    brick_dimensions["tick_width"] = scale*0.6
    brick_dimensions["tick_depth"] = scale*0.3
    brick_dimensions["support_height"] = brick_dimensions["height"]*0.65

    brick_dimensions["logo_offset"] = (brick_dimensions["height"] / 2) + (brick_dimensions["stud_height"])
    return brick_dimensions

def main():
    try:
        bpy.ops.object.select_all(action='TOGGLE')
    except RuntimeError:
        print("Not in object mode!")
        return
    deleteExisting()

    # create objects
    dimensions = get_dimensions(.1, 1, .01)
    newObjFromBmesh(1, makeBrick(dimensions=dimensions, brickSize=[1,1,3], numStudVerts=16, detail="Flat"), "1x1 flat").location = (-.2,0,0)
    newObjFromBmesh(1, makeBrick(dimensions=dimensions, brickSize=[1,1,3], numStudVerts=16, detail="Low Detail"), "1x1 low").location = (0,0,0)
    newObjFromBmesh(1, makeBrick(dimensions=dimensions, brickSize=[1,1,3], numStudVerts=16, detail="Medium Detail"), "1x1 medium").location = (.2,0,0)
    newObjFromBmesh(1, makeBrick(dimensions=dimensions, brickSize=[1,1,3], numStudVerts=16, detail="High Detail"), "1x1 high").location = (.4,0,0)
    newObjFromBmesh(2, makeBrick(dimensions=dimensions, brickSize=[1,2,3], numStudVerts=16, detail="Flat"), "1x2 flat").location = (-.4,0,0)
    newObjFromBmesh(2, makeBrick(dimensions=dimensions, brickSize=[1,2,3], numStudVerts=16, detail="Low Detail"), "1x2 low").location = (-.2,0,0)
    newObjFromBmesh(2, makeBrick(dimensions=dimensions, brickSize=[1,2,3], numStudVerts=16, detail="Medium Detail"), "1x2 meidium").location = (0,0,0)
    newObjFromBmesh(2, makeBrick(dimensions=dimensions, brickSize=[1,2,3], numStudVerts=16, detail="High Detail"), "1x2 high").location = (.2,0,0)
    newObjFromBmesh(2, makeBrick(dimensions=dimensions, brickSize=[1,2,3], numStudVerts=16, detail="Full Detail"), "1x2 full").location = (.4,0,0)
    newObjFromBmesh(3, makeBrick(dimensions=dimensions, brickSize=[3,1,3], numStudVerts=16, detail="Flat"), "3x1 flat").location = (0,-.4,0)
    newObjFromBmesh(3, makeBrick(dimensions=dimensions, brickSize=[3,1,3], numStudVerts=16, detail="Low Detail"), "3x1 low").location = (0,-.2,0)
    newObjFromBmesh(3, makeBrick(dimensions=dimensions, brickSize=[3,1,3], numStudVerts=16, detail="Medium Detail"), "3x1 meidium").location = (0,0,0)
    newObjFromBmesh(3, makeBrick(dimensions=dimensions, brickSize=[3,1,3], numStudVerts=16, detail="High Detail"), "3x1 high").location = (0,.2,0)
    newObjFromBmesh(3, makeBrick(dimensions=dimensions, brickSize=[3,1,3], numStudVerts=16, detail="Full Detail"), "3x1 full").location = (0,.4,0)
    newObjFromBmesh(4, makeBrick(dimensions=dimensions, brickSize=[1,8,3], numStudVerts=16, detail="Flat"), "1x8 flat").location = (-.4,0,0)
    newObjFromBmesh(4, makeBrick(dimensions=dimensions, brickSize=[1,8,3], numStudVerts=16, detail="Low Detail"), "1x8 low").location = (-.2,0,0)
    newObjFromBmesh(4, makeBrick(dimensions=dimensions, brickSize=[1,8,3], numStudVerts=16, detail="Medium Detail"), "1x8 meidium").location = (0,0,0)
    newObjFromBmesh(4, makeBrick(dimensions=dimensions, brickSize=[1,8,3], numStudVerts=16, detail="High Detail"), "1x8 high").location = (.2,0,0)
    newObjFromBmesh(4, makeBrick(dimensions=dimensions, brickSize=[1,8,3], numStudVerts=16, detail="Full Detail"), "1x8 full").location = (.4,0,0)
    newObjFromBmesh(5, makeBrick(dimensions=dimensions, brickSize=[2,2,3], numStudVerts=16, detail="Flat"), "2x2 flat").location = (-.6,0,0)
    newObjFromBmesh(5, makeBrick(dimensions=dimensions, brickSize=[2,2,3], numStudVerts=16, detail="Low Detail"), "2x2 low").location = (-.3,0,0)
    newObjFromBmesh(5, makeBrick(dimensions=dimensions, brickSize=[2,2,3], numStudVerts=16, detail="Medium Detail"), "2x2 medium").location = (0,0,0)
    newObjFromBmesh(5, makeBrick(dimensions=dimensions, brickSize=[2,2,3], numStudVerts=16, detail="High Detail"), "2x2 high").location = (.3,0,0)
    newObjFromBmesh(5, makeBrick(dimensions=dimensions, brickSize=[2,2,3], numStudVerts=16, detail="Full Detail"), "2x2 full").location = (.6,0,0)
    newObjFromBmesh(6, makeBrick(dimensions=dimensions, brickSize=[2,6,3], numStudVerts=16, detail="Flat"), "2x6 flat").location = (-.6,0,0)
    newObjFromBmesh(6, makeBrick(dimensions=dimensions, brickSize=[2,6,3], numStudVerts=16, detail="Low Detail"), "2x6 low").location = (-.3,0,0)
    newObjFromBmesh(6, makeBrick(dimensions=dimensions, brickSize=[2,6,3], numStudVerts=16, detail="Medium Detail"), "2x6 medium").location = (0,0,0)
    newObjFromBmesh(6, makeBrick(dimensions=dimensions, brickSize=[2,6,3], numStudVerts=16, detail="High Detail"), "2x6 high").location = (.3,0,0)
    newObjFromBmesh(6, makeBrick(dimensions=dimensions, brickSize=[2,6,3], numStudVerts=16, detail="Full Detail"), "2x6 full").location = (.6,0,0)
    newObjFromBmesh(7, makeBrick(dimensions=dimensions, brickSize=[6,2,3], numStudVerts=15, detail="Flat"), "6x2 flat").location = (0,-.6,0)
    newObjFromBmesh(7, makeBrick(dimensions=dimensions, brickSize=[6,2,3], numStudVerts=15, detail="Low Detail"), "6x2 low").location = (0,-.3,0)
    newObjFromBmesh(7, makeBrick(dimensions=dimensions, brickSize=[6,2,3], numStudVerts=15, detail="Medium Detail"), "6x2 medium").location = (0,0,0)
    newObjFromBmesh(7, makeBrick(dimensions=dimensions, brickSize=[6,2,3], numStudVerts=15, detail="High Detail"), "6x2 high").location = (0,.3,0)
    newObjFromBmesh(7, makeBrick(dimensions=dimensions, brickSize=[6,2,3], numStudVerts=15, detail="Full Detail"), "6x2 full").location = (0,.6,0)

    layerToOpen = 7

    layerList = []
    for i in range(20):
        layerList.append(i == layerToOpen-1)
    scn = bpy.context.scene
    scn.layers = layerList

# main()
