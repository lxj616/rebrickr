import bpy
import bmesh
import math
from mathutils import Matrix
# from ...functions.common_mesh_generate import makeCylinder

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

# r = radius, N = numVerts, h = height, t = thickness, co = target cylinder position
def makeTube(r, N, h, t, co=(0,0,0), wings=False, bme=None):
    # create new bmesh object
    if bme == None:
        bme = bmesh.new()

    # create upper and lower circles
    vertListTInner = []
    vertListBInner = []
    vertListTOuter = []
    vertListBOuter = []
    for i in range(N):
        # set coord x,y,z locations
        xInner = r * math.cos(((2 * math.pi) / N) * i)
        xOuter = (r + t) * math.cos(((2 * math.pi) / N) * i)
        yInner = r * math.sin(((2 * math.pi) / N) * i)
        yOuter = (r + t) * math.sin(((2 * math.pi) / N) * i)
        z = h / 2
        # inner cylinder verts
        coordT = (xInner + co[0], yInner + co[1], z + co[2])
        coordB = (xInner + co[0], yInner + co[1], -z + co[2])
        vertListTInner.append(bme.verts.new(coordT))
        vertListBInner.append(bme.verts.new(coordB))
        # outer cylinder verts
        coordT = (xOuter + co[0], yOuter + co[1], z + co[2])
        coordB = (xOuter + co[0], yOuter + co[1], -z + co[2])
        vertListTOuter.append(bme.verts.new(coordT))
        vertListBOuter.append(bme.verts.new(coordB))
        # create faces between them
        if i > 0:
            bme.faces.new((vertListBOuter[-2], vertListBInner[-2], vertListBInner[-1], vertListBOuter[-1]))
    # select top verts for exclusion from vert group
    for lst in [vertListTOuter, vertListTInner]:
        for v in lst:
            v.select = True

    bme.faces.new((vertListBOuter[-1], vertListBInner[-1], vertListBInner[0], vertListBOuter[0]))

    # create faces on the outer and inner sides
    sideFaces = []
    sideFaces.append(bme.faces.new((vertListTOuter[-1], vertListBOuter[-1], vertListBOuter[0], vertListTOuter[0])))
    sideFaces.append(bme.faces.new((vertListTInner[0], vertListBInner[0], vertListBInner[-1], vertListTInner[-1])))
    for v in range(N-1):
        sideFaces.append(bme.faces.new((vertListTOuter.pop(0), vertListBOuter.pop(0), vertListBOuter[0], vertListTOuter[0])))
        sideFaces.append(bme.faces.new((vertListTInner[1], vertListBInner[1], vertListBInner.pop(0), vertListTInner.pop(0))))

    for f in sideFaces:
        f.smooth = True

    # return bmesh
    return bme

# r = radius, N = numVerts, h = height, o = z offset, co = target cylinder position, bme = bmesh to insert mesh data into
def makeInnerCylinder(r, N, h, co=(0,0,0), bme=None):
    """ Make a brick inner cylinder """
    # create upper circle
    vertListT = []
    vertListB = []
    vertListBDict = {"++":[], "-+":[], "--":[], "+-":[], "x+":[], "x-":[], "y+":[], "y-":[]}
    for i in range(N):
        # set coord x,y,z locations
        x = r * math.cos(((2 * math.pi) / N) * i)
        y = r * math.sin(((2 * math.pi) / N) * i)
        z = co[2]
        # create top verts
        vertListT.append(bme.verts.new((x + co[0], y + co[1], z + h)))

        # create bottom verts and add to dict
        v = bme.verts.new((x + co[0], y + co[1], z))
        yP = v.co.y > co[1] # true if 'y' is positive
        xP = v.co.x > co[0] # true if 'x' is positive
        if abs(v.co.x - co[0]) < 0.00001:
            if yP:
                l = "y+"
            else:
                l = "y-"
        elif abs(v.co.y - co[1]) < 0.00001:
            if xP:
                l = "x+"
            else:
                l = "x-"
        else:
            if xP and yP:
                l = "++"
            elif not xP and yP:
                l = "-+"
            elif not xP and not yP:
                l = "--"
            else:
                l = "+-"
        vertListBDict[l].insert(0,v)
        vertListB.append(v)
    bme.faces.new(vertListT[::-1])
    if len(vertListBDict["y+"]) == 0:
        v0 = vertListBDict["++"][0]
        v1 = vertListBDict["-+"][0]
        if v0.co.y > v1.co.y:
            vertListBDict["y+"] = [vertListBDict["++"].pop(0)]
        else:
            vertListBDict["y+"] = [vertListBDict["-+"].pop(-1)]
    if len(vertListBDict["x+"]) == 0:
        v0 = vertListBDict["+-"][0]
        v1 = vertListBDict["++"][0]
        if v0.co.x > v1.co.x:
            vertListBDict["x+"] = [vertListBDict["+-"].pop(0)]
        else:
            vertListBDict["x+"] = [vertListBDict["++"].pop(-1)]
    if len(vertListBDict["y-"]) == 0:
        v0 = vertListBDict["--"][0]
        v1 = vertListBDict["+-"][0]
        if v0.co.y > v1.co.y:
            vertListBDict["y-"] = [vertListBDict["--"].pop(0)]
        else:
            vertListBDict["y-"] = [vertListBDict["+-"].pop(-1)]
    if len(vertListBDict["x-"]) == 0:
        v0 = vertListBDict["-+"][0]
        v1 = vertListBDict["--"][0]
        if v0.co.x > v1.co.x:
            vertListBDict["x-"] = [vertListBDict["-+"].pop(0)]
        else:
            vertListBDict["x-"] = [vertListBDict["--"].pop(-1)]

    # select bottom verts for vertex group
    for v in vertListB:
        v.select = True

#    # create lower circle faces with square
#    lastKey = "x-y"
#    for key in ["xy", "-xy", "-x-y", "x-y"]:
#        bme.faces.new((vertListBDict[lastKey][1][-1], vertListBDict[key][1][0], vertListBDict[key][0], vertListBDict[lastKey][0]))
#        for i in range(1, len(vertListBDict[key][1])):
#            bme.faces.new((vertListBDict[key][1][i-1], vertListBDict[key][1][i], vertListBDict[key][0]))
#        lastKey = key

    # create faces around edge
    sideFaces = []
    sideFaces.append(bme.faces.new((vertListT[0], vertListB[0], vertListB[-1], vertListT[-1])))
    for v in range(N-1):
        sideFaces.append(bme.faces.new((vertListT[1], vertListB[1], vertListB.pop(0), vertListT.pop(0))))

    for f in sideFaces:
        f.smooth = True

    return vertListBDict

def makeBrick(dimensions, brickSize, numStudVerts=None, detail="Low Detail", logo=None, stud=True, bme=None):
    # create new bmesh object
    if not bme:
        bme = bmesh.new()
    scn = bpy.context.scene
    cm = scn.cmlist[scn.cmlist_index]

    # set scale and thickness variables
    dX = dimensions["width"]
    dY = dimensions["width"]
    dZ = dimensions["height"]
    if cm.brickType != "Bricks":
        dZ = dZ*brickSize[2]
    thickZ = dimensions["thickness"]
    if detail == "Full Detail" and not (brickSize[0] == 1 or brickSize[1] == 1) and brickSize[2] != 1:
        thickXY = dimensions["thickness"] - dimensions["tick_depth"]
    else:
        thickXY = dimensions["thickness"]
    sX = (brickSize[0] * 2) - 1
    sY = (brickSize[1] * 2) - 1

    # half scale inputs
    dX = dX/2
    dY = dY/2
    dZ = dZ/2

    # CREATING CUBE
    v1 = bme.verts.new(( dX * sX, dY * sY, dZ))
    v2 = bme.verts.new((-dX, dY * sY, dZ))
    v3 = bme.verts.new((-dX,-dY, dZ))
    v4 = bme.verts.new(( dX * sX,-dY, dZ))
    bme.faces.new((v1, v2, v3, v4))
    v5 = bme.verts.new(( dX * sX, dY * sY,-dZ))
    v6 = bme.verts.new((-dX, dY * sY,-dZ))
    bme.faces.new((v2, v1, v5, v6))
    v7 = bme.verts.new((-dX,-dY,-dZ))
    bme.faces.new((v3, v2, v6, v7))
    v8 = bme.verts.new(( dX * sX,-dY,-dZ))
    bme.faces.new((v1, v4, v8, v5))
    bme.faces.new((v4, v3, v7, v8))

    # CREATING STUD(S)
    if stud:
        studInset = thickZ * 0.9
        for xNum in range(brickSize[0]):
            for yNum in range(brickSize[1]):
                _,botVerts,_ = makeCylinder(r=dimensions["stud_radius"], N=numStudVerts, h=dimensions["stud_height"]+studInset, co=(xNum*dX*2,yNum*dY*2,dimensions["stud_offset"]-(studInset/2)), botFace=False, bme=bme)
                for v in botVerts:
                    v.select = True

    if detail == "Flat":
        bme.faces.new((v8, v7, v6, v5))
    else:
        # creating cylinder
        # making verts for hollow portion at bottom
        v9 = bme.verts.new((v5.co.x-thickXY, v5.co.y-thickXY, v5.co.z))
        v10 = bme.verts.new((v6.co.x+thickXY, v6.co.y-thickXY, v6.co.z))
        v11 = bme.verts.new((v7.co.x+thickXY, v7.co.y+thickXY, v7.co.z))
        v12 = bme.verts.new((v8.co.x-thickXY, v8.co.y+thickXY, v8.co.z))
        # making verts for hollow portion at top
        v13 = bme.verts.new((v9.co.x, v9.co.y, dZ-thickZ))
        v14 = bme.verts.new((v10.co.x, v10.co.y, dZ-thickZ))
        bme.faces.new((v9, v13, v14, v10))
        v15 = bme.verts.new((v11.co.x, v11.co.y, dZ-thickZ))
        bme.faces.new((v10, v14, v15, v11))
        v16 = bme.verts.new((v12.co.x, v12.co.y, dZ-thickZ))
        bme.faces.new((v11, v15, v16, v12))
        bme.faces.new((v12,v16, v13, v9))
        # set edge vert refs (n=negative, p=positive, o=outer, i=inner)
        nno = v5
        pno = v6
        ppo = v7
        npo = v8
        nni = v9
        pni = v10
        ppi = v11
        npi = v12
        # make tick marks inside 2 by x bricks
        if detail == "Full Detail" and ((brickSize[0] == 2 and brickSize[1] > 1) or (brickSize[1] == 2 and brickSize[0] > 1)) and brickSize[2] != 1:
            for xNum in range(brickSize[0]):
                for yNum in range(brickSize[1]):
                    to_select = []
                    if xNum == 0:
                        # initialize x, y, z
                        x1 = -dX+thickXY
                        x2 = x1+dimensions["tick_depth"]
                        y1 = yNum*dY*2+dimensions["tick_width"]/2
                        y2 = yNum*dY*2-dimensions["tick_width"]/2
                        z1 = dZ-thickZ
                        z2 = -dZ
                        # CREATING SUPPORT BEAM
                        v1 = bme.verts.new((x1, y1, z1))
                        v2 = bme.verts.new((x1, y2, z1))
                        v3 = bme.verts.new((x1, y1, z2))
                        v4 = bme.verts.new((x1, y2, z2))
                        v5 = bme.verts.new((x2, y1, z1))
                        v6 = bme.verts.new((x2, y2, z1))
                        v7 = bme.verts.new((x2, y1, z2))
                        v8 = bme.verts.new((x2, y2, z2))
                        bme.faces.new((v8, v6, v2, v4))
                        bme.faces.new((v4, v3, v7, v8))
                        bme.faces.new((v5, v7, v3, v1))
                        bme.faces.new((v6, v8, v7, v5))
                        to_select += [v1, v2, v3, v4]
                        if yNum == 0:
                            bme.faces.new((v4, ppi, ppo))
                            pass
                        else:
                            bme.faces.new((v4, xN0v, ppo))
                        if yNum == brickSize[1]-1:
                            bme.faces.new((v3, pno, pni))
                            bme.faces.new((v3, v4, ppo, pno))
                            pass
                        else:
                            bme.faces.new((v3, v4, ppo))
                            pass
                        xN0v = v3
                    elif xNum == brickSize[0]-1:
                        # initialize x, y, z
                        x1 = xNum*dX*2+dX-thickXY
                        x2 = x1-dimensions["tick_depth"]
                        y1 = yNum*dY*2+dimensions["tick_width"]/2
                        y2 = yNum*dY*2-dimensions["tick_width"]/2
                        z1 = dZ-thickZ
                        z2 = -dZ
                        # CREATING SUPPORT BEAM
                        v1 = bme.verts.new((x1, y1, z1))
                        v2 = bme.verts.new((x1, y2, z1))
                        v3 = bme.verts.new((x1, y1, z2))
                        v4 = bme.verts.new((x1, y2, z2))
                        v5 = bme.verts.new((x2, y1, z1))
                        v6 = bme.verts.new((x2, y2, z1))
                        v7 = bme.verts.new((x2, y1, z2))
                        v8 = bme.verts.new((x2, y2, z2))
                        bme.faces.new((v4, v2, v6, v8))
                        bme.faces.new((v8, v7, v3, v4))
                        bme.faces.new((v1, v3, v7, v5))
                        bme.faces.new((v5, v7, v8, v6))
                        to_select += [v1, v2, v3, v4]
                        if yNum == 0:
                            bme.faces.new((npi, v4, npo))
                            pass
                        else:
                            bme.faces.new((v4, npo, xN1v))
                        if yNum == brickSize[1]-1:
                            bme.faces.new((nno, v3, nni))
                            bme.faces.new((v4, v3, nno, npo))
                            pass
                        else:
                            bme.faces.new((v4, v3, npo))
                            pass
                        xN1v = v3
                    if yNum == 0:
                        # initialize x, y, z
                        y1 = -dY+thickXY
                        y2 = y1+dimensions["tick_depth"]
                        x1 = xNum*dX*2+dimensions["tick_width"]/2
                        x2 = xNum*dX*2-dimensions["tick_width"]/2
                        z1 = dZ-thickZ
                        z2 = -dZ
                        # CREATING SUPPORT BEAM
                        v1 = bme.verts.new((x1, y1, z1))
                        v2 = bme.verts.new((x2, y1, z1))
                        v3 = bme.verts.new((x1, y1, z2))
                        v4 = bme.verts.new((x2, y1, z2))
                        v5 = bme.verts.new((x1, y2, z1))
                        v6 = bme.verts.new((x2, y2, z1))
                        v7 = bme.verts.new((x1, y2, z2))
                        v8 = bme.verts.new((x2, y2, z2))
                        bme.faces.new((v4, v2, v6, v8))
                        bme.faces.new((v8, v7, v3, v4))
                        bme.faces.new((v1, v3, v7, v5))
                        bme.faces.new((v5, v7, v8, v6))
                        to_select += [v1, v2, v3, v4]
                        if xNum == 0:
                            bme.faces.new((ppi, v4, ppo))
                            pass
                        else:
                            bme.faces.new((v3, ppo, yN0v))
                            pass
                        if xNum == brickSize[0]-1:
                            bme.faces.new((npo, v3, npi))
                            bme.faces.new((ppo, v4, v3, npo))
                            pass
                        else:
                            bme.faces.new((v4, v3, ppo))
                            pass
                        yN0v = v3
                    elif yNum == brickSize[1]-1:
                        # initialize x, y, z
                        y1 = yNum*dY*2+dY-thickXY
                        y2 = y1-dimensions["tick_depth"]
                        x1 = xNum*dX*2+dimensions["tick_width"]/2
                        x2 = xNum*dX*2-dimensions["tick_width"]/2
                        z1 = dZ-thickZ
                        z2 = -dZ
                        # CREATING SUPPORT BEAM
                        v1 = bme.verts.new((x1, y1, z1))
                        v2 = bme.verts.new((x1, y2, z1))
                        v3 = bme.verts.new((x1, y1, z2))
                        v4 = bme.verts.new((x1, y2, z2))
                        v5 = bme.verts.new((x2, y1, z1))
                        v6 = bme.verts.new((x2, y2, z1))
                        v7 = bme.verts.new((x2, y1, z2))
                        v8 = bme.verts.new((x2, y2, z2))
                        bme.faces.new((v4, v2, v6, v8))
                        bme.faces.new((v8, v7, v3, v4))
                        bme.faces.new((v8, v6, v5, v7))
                        bme.faces.new((v2, v4, v3, v1))
                        # select bottom connecting verts for exclusion from vertex group
                        to_select += [v1, v2, v3, v7]
                        if xNum == 0:
                            bme.faces.new((v7, pni, pno))
                            pass
                        else:
                            bme.faces.new((pno, v7, yN1v))
                        if xNum == brickSize[0]-1:
                            bme.faces.new((v3, nno, nni))
                            bme.faces.new((v3, v7, pno, nno))
                            pass
                        else:
                            bme.faces.new((v3, v7, pno))
                            pass
                        yN1v = v3
                    # select verts for exclusion from vertex group
                    for v in to_select:
                        v.select = True
        else:
            # make faces on bottom edges of brick
            bme.faces.new((v5, v9, v10, v6))
            bme.faces.new((v6, v10, v11, v7))
            bme.faces.new((v7, v11, v12, v8))
            bme.faces.new((v8, v12, v9, v5))


        # make tubes
        addSupports = (brickSize[0] > 2 and brickSize[1] == 2) or (brickSize[1] > 2 and brickSize[0] == 2)
        for xNum in range(brickSize[0]-1):
            for yNum in range(brickSize[1]-1):
                tubeX = (xNum * dX * 2) + dX
                tubeY = (yNum * dY * 2) + dY
                tubeZ = (-thickZ/2)
                r = dimensions["stud_radius"]
                t = (dZ*2)-thickZ
                makeTube(r, numStudVerts, t, dimensions["tube_thickness"], co=(tubeX, tubeY, tubeZ), wings=True, bme=bme)
                # add support next to odd tubes
                if (detail == "High Detail" or detail == "Full Detail") and addSupports and brickSize[2] != 1:
                    if brickSize[0] > brickSize[1]:
                        if brickSize[0] == 3 or xNum % 2 == 1:
                            # initialize x, y, z
                            x1 = tubeX + (dimensions["support_width"]/2)
                            x2 = tubeX - (dimensions["support_width"]/2)
                            y1 = tubeY + r
                            y2 = tubeY + dY*2-thickXY
                            y3 = tubeY - r
                            y4 = tubeY - dY*2+thickXY
                            z1 = dZ-thickZ
                            z2 = dZ-thickZ-dimensions["support_height"]
                            # CREATING SUPPORT BEAM
                            v1a = bme.verts.new((x1, y1, z1))
                            v2a = bme.verts.new((x2, y1, z1))
                            v3a = bme.verts.new((x1, y1, z2))
                            v4a = bme.verts.new((x2, y1, z2))
                            v5a = bme.verts.new((x1, y2, z1))
                            v6a = bme.verts.new((x2, y2, z1))
                            v7a = bme.verts.new((x1, y2, z2))
                            v8a = bme.verts.new((x2, y2, z2))
                            bme.faces.new((v1a, v3a, v7a, v5a))
                            bme.faces.new((v3a, v4a, v8a, v7a))
                            bme.faces.new((v6a, v8a, v4a, v2a))
                            v1b = bme.verts.new((x1, y3, z1))
                            v2b = bme.verts.new((x2, y3, z1))
                            v3b = bme.verts.new((x1, y3, z2))
                            v4b = bme.verts.new((x2, y3, z2))
                            v5b = bme.verts.new((x1, y4, z1))
                            v6b = bme.verts.new((x2, y4, z1))
                            v7b = bme.verts.new((x1, y4, z2))
                            v8b = bme.verts.new((x2, y4, z2))
                            bme.faces.new((v5b, v7b, v3b, v1b))
                            bme.faces.new((v7b, v8b, v4b, v3b))
                            bme.faces.new((v2b, v4b, v8b, v6b))
                    elif brickSize[1] > brickSize[0]:
                        if brickSize[1] == 3 or yNum % 2 == 1:
                            # initialize x, y, z
                            x1 = tubeX + r
                            x2 = tubeX + dX*2-thickXY
                            x3 = tubeX - r
                            x4 = tubeX - dX*2+thickXY
                            y1 = tubeY + (dimensions["support_width"]/2)
                            y2 = tubeY - (dimensions["support_width"]/2)
                            z1 = dZ-thickZ
                            z2 = dZ-thickZ-dimensions["support_height"]
                            # CREATING SUPPORT BEAM
                            v1a = bme.verts.new((x1, y1, z1))
                            v2a = bme.verts.new((x1, y2, z1))
                            v3a = bme.verts.new((x1, y1, z2))
                            v4a = bme.verts.new((x1, y2, z2))
                            v5a = bme.verts.new((x2, y1, z1))
                            v6a = bme.verts.new((x2, y2, z1))
                            v7a = bme.verts.new((x2, y1, z2))
                            v8a = bme.verts.new((x2, y2, z2))
                            bme.faces.new((v5a, v7a, v3a, v1a))
                            bme.faces.new((v7a, v8a, v4a, v3a))
                            bme.faces.new((v2a, v4a, v8a, v6a))
                            v1b = bme.verts.new((x3, y1, z1))
                            v2b = bme.verts.new((x3, y2, z1))
                            v3b = bme.verts.new((x3, y1, z2))
                            v4b = bme.verts.new((x3, y2, z2))
                            v5b = bme.verts.new((x4, y1, z1))
                            v6b = bme.verts.new((x4, y2, z1))
                            v7b = bme.verts.new((x4, y1, z2))
                            v8b = bme.verts.new((x4, y2, z2))
                            bme.faces.new((v1b, v3b, v7b, v5b))
                            bme.faces.new((v3b, v4b, v8b, v7b))
                            bme.faces.new((v6b, v8b, v4b, v2b))
        # Adding bar inside 1 by x bricks
        if brickSize[0] == 1:
            for y in range(1, brickSize[1]):
                barX = 0
                barY = (y * dY * 2) - dY
                barZ = -thickZ/2
                r = dimensions["bar_radius"]
                _,_,topVerts = makeCylinder(r=r, N=numStudVerts, h=(dZ*2)-thickZ, co=(barX, barY, barZ), botFace=True, topFace=False, bme=bme)
                # select top verts for exclusion from vert group
                for v in topVerts:
                    v.select = True
                if (detail == "High Detail" or detail == "Full Detail") and brickSize[2] != 1:
                    if brickSize[1] == 3 or brickSize[1] == 2 or y % 2 == 0 or ((y == 1 or y == brickSize[1]-1) and brickSize[1] == 8):
                        # initialize x, y, z
                        x2 = barX + dX-thickXY
                        x4 = barX - dX+thickXY
                        y1 = barY + (dimensions["support_width"]/2)
                        y2 = barY - (dimensions["support_width"]/2)
                        z1 = dZ-thickZ
                        z2 = dZ-thickZ-dimensions["support_height"]
                        # CREATING SUPPORT BEAM
                        v1 = bme.verts.new((x2, y1, z1))
                        v2 = bme.verts.new((x2, y2, z1))
                        v3 = bme.verts.new((x2, y1, z2))
                        v4 = bme.verts.new((x2, y2, z2))
                        v5 = bme.verts.new((x4, y1, z1))
                        v6 = bme.verts.new((x4, y2, z1))
                        v7 = bme.verts.new((x4, y1, z2))
                        v8 = bme.verts.new((x4, y2, z2))
                        bme.faces.new((v4, v2, v6, v8))
                        bme.faces.new((v8, v7, v3, v4))
                        bme.faces.new((v1, v3, v7, v5))
        if brickSize[1] == 1:
            for x in range(1, brickSize[0]):
                barX = (x * dX * 2) - dX
                barY = 0
                barZ = -thickZ/2
                r = dimensions["bar_radius"]
                _,_,topVerts = makeCylinder(r=r, N=numStudVerts, h=(dZ*2)-thickZ, co=(barX, barY, barZ), botFace=True, topFace=False, bme=bme)
                # select top verts for exclusion from vert group
                for v in topVerts:
                    v.select = True
                # add supports next to odd bars
                if (detail == "High Detail" or detail == "Full Detail") and brickSize[2] != 1:
                    if brickSize[0] == 3 or brickSize[0] == 2 or x % 2 == 0 or ((x == 1 or x == brickSize[0]-1) and brickSize[0] == 8):
                        # initialize x, y, z
                        x1 = barX + (dimensions["support_width"]/2)
                        x2 = barX - (dimensions["support_width"]/2)
                        y2 = barY + dY-thickXY
                        y4 = barY - dY+thickXY
                        z1 = dZ-thickZ
                        z2 = dZ-thickZ-dimensions["support_height"]
                        # CREATING SUPPORT BEAM
                        v1 = bme.verts.new((x1, y2, z1))
                        v2 = bme.verts.new((x2, y2, z1))
                        v3 = bme.verts.new((x1, y2, z2))
                        v4 = bme.verts.new((x2, y2, z2))
                        v5 = bme.verts.new((x1, y4, z1))
                        v6 = bme.verts.new((x2, y4, z1))
                        v7 = bme.verts.new((x1, y4, z2))
                        v8 = bme.verts.new((x2, y4, z2))
                        bme.faces.new((v8, v6, v2, v4))
                        bme.faces.new((v4, v3, v7, v8))
                        bme.faces.new((v5, v7, v3, v1))
        # make face at top
        if detail == "Low Detail":
            bme.faces.new((v16, v15, v14, v13))
        else:
        # make small inner cylinder at top
            botVertsDofDs = {}
            for xNum in range(brickSize[0]):
                for yNum in range(brickSize[1]):
                    r = dimensions["stud_radius"]-(2 * thickZ)
                    N = numStudVerts
                    h = thickZ * 0.99
                    botVertsD = makeInnerCylinder(r, N, h, co=(xNum*dX*2,yNum*dY*2,dZ-thickZ), bme=bme)
                    botVertsDofDs["%(xNum)s,%(yNum)s" % locals()] = botVertsD

            # Make corner faces
            vList = botVertsDofDs["0,0"]["y-"] + botVertsDofDs["0,0"]["--"] + botVertsDofDs["0,0"]["x-"]
            for i in range(1, len(vList)):
                bme.faces.new((vList[i], vList[i-1], v15))
            vList = botVertsDofDs[str(xNum) + "," + str(0)]["x+"] + botVertsDofDs[str(xNum) + "," + str(0)]["+-"] + botVertsDofDs[str(xNum) + "," + str(0)]["y-"]
            for i in range(1, len(vList)):
                bme.faces.new((vList[i], vList[i-1], v16))
            vList = botVertsDofDs[str(xNum) + "," + str(yNum)]["y+"] + botVertsDofDs[str(xNum) + "," + str(yNum)]["++"] + botVertsDofDs[str(xNum) + "," + str(yNum)]["x+"]
            for i in range(1, len(vList)):
                bme.faces.new((vList[i], vList[i-1], v13))
            vList = botVertsDofDs[str(0) + "," + str(yNum)]["x-"] + botVertsDofDs[str(0) + "," + str(yNum)]["-+"] + botVertsDofDs[str(0) + "," + str(yNum)]["y+"]
            for i in range(1, len(vList)):
                bme.faces.new((vList[i], vList[i-1], v14))

            # Make edge faces
            v = botVertsDofDs[str(xNum) + "," + str(yNum)]["y+"][0]
            bme.faces.new((v14, v13, v))
            # except:
            #     v = botVertsDofDs[str(xNum) + "," + str(yNum)]["++"][0]
            # bme.faces.new((v14, v13, v))
            v = botVertsDofDs[str(0) + "," + str(yNum)]["x-"][0]
            bme.faces.new((v15, v14, v))
            # except:
            #     v = botVertsDofDs[str(0) + "," + str(yNum)]["--"][0]
            # bme.faces.new((v15, v14, v))
            v = botVertsDofDs[str(0) + "," + str(0)]["y-"][0]
            bme.faces.new((v16, v15, v))
            # except:
            #     v = botVertsDofDs[str(0) + "," + str(0)]["--"][0]
            # bme.faces.new((v16, v15, v))
            v = botVertsDofDs[str(xNum) + "," + str(0)]["x+"][0]
            bme.faces.new((v13, v16, v))
            # except:
            #     v = botVertsDofDs[str(xNum) + "," + str(0)]["++"][0]
            # bme.faces.new((v13, v16, v))
            for xNum in range(1, brickSize[0]):
                try:
                    v1 = botVertsDofDs[str(xNum) + "," + str(yNum)]["y+"][0]
                    v2 = botVertsDofDs[str(xNum-1) + "," + str(yNum)]["y+"][0]
                    bme.faces.new((v1, v2, v14))
                except:
                    v1 = botVertsDofDs[str(xNum) + "," + str(yNum)]["y+"][0]
                    v2 = botVertsDofDs[str(xNum-1) + "," + str(yNum)]["y+"][0]
                    bme.faces.new((v1, v2, v14))
                    pass
                try:
                    v1 = botVertsDofDs[str(xNum) + "," + str(0)]["y-"][0]
                    v2 = botVertsDofDs[str(xNum-1) + "," + str(0)]["y-"][0]
                    bme.faces.new((v16, v2, v1))
                except:
                    pass
            for yNum in range(1, brickSize[1]):
                try:
                    v1 = botVertsDofDs[str(xNum) + "," + str(yNum)]["x+"][0]
                    v2 = botVertsDofDs[str(xNum) + "," + str(yNum-1)]["x+"][0]
                    bme.faces.new((v13, v2, v1))
                except:
                    pass
                try:
                    v1 = botVertsDofDs[str(0) + "," + str(yNum)]["x-"][0]
                    v2 = botVertsDofDs[str(0) + "," + str(yNum-1)]["x-"][0]
                    bme.faces.new((v1, v2, v15))
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
        if i == layer-1:
            layerList.append(True)
        else:
            layerList.append(False)
    bpy.ops.object.move_to_layer(layers=layerList)
    scn.layers = layerList
    bpy.ops.object.select_all(action='TOGGLE')
    return ob

def deleteExisting():
    # delete existing objects
    tmpList = [True]*20
    bpy.context.scene.layers = tmpList
    for i in range(2):
        bpy.ops.object.select_all(action='TOGGLE')
        bpy.ops.object.delete()
    bpy.context.scene.layers = [False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True]

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
    except:
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
        if i == layerToOpen-1: layerList.append(True)
        else: layerList.append(False)
    bpy.context.scene.layers = layerList

main()
