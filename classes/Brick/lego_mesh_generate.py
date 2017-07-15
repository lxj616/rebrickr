import bpy
import bmesh
import math
from mathutils import Matrix
from ...functions.common_mesh_generate import makeCylinder

# r = radius, N = numVerts, h = height, t = thickness, co = target cylinder position
def makeTube(r, N, h, t, co=(0,0,0), bme=None):
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
    bme.faces.new((vertListBOuter[-1], vertListBInner[-1], vertListBInner[0], vertListBOuter[0]))

    # create faces on the outer and inner sides
    bme.faces.new((vertListTOuter[-1], vertListBOuter[-1], vertListBOuter[0], vertListTOuter[0]))
    bme.faces.new((vertListTInner[0], vertListBInner[0], vertListBInner[-1], vertListTInner[-1]))
    for v in range(N-1):
        bme.faces.new((vertListTOuter.pop(0), vertListBOuter.pop(0), vertListBOuter[0], vertListTOuter[0]))
        bme.faces.new((vertListTInner[1], vertListBInner[1], vertListBInner.pop(0), vertListTInner.pop(0)))

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
        vertListBDict["y+"] = [vertListBDict["++"].pop(0)]
    if len(vertListBDict["x+"]) == 0:
        vertListBDict["x+"] = [vertListBDict["+-"].pop(0)]
    if len(vertListBDict["y-"]) == 0:
        vertListBDict["y-"] = [vertListBDict["--"].pop(0)]
    if len(vertListBDict["x-"]) == 0:
        vertListBDict["x-"] = [vertListBDict["-+"].pop(0)]

#    # create lower circle faces with square
#    lastKey = "x-y"
#    for key in ["xy", "-xy", "-x-y", "x-y"]:
#        bme.faces.new((vertListBDict[lastKey][1][-1], vertListBDict[key][1][0], vertListBDict[key][0], vertListBDict[lastKey][0]))
#        for i in range(1, len(vertListBDict[key][1])):
#            bme.faces.new((vertListBDict[key][1][i-1], vertListBDict[key][1][i], vertListBDict[key][0]))
#        lastKey = key

    bme.faces.new((vertListT[0], vertListB[0], vertListB[-1], vertListT[-1]))
    for v in range(N-1):
        bme.faces.new((vertListT[1], vertListB[1], vertListB.pop(0), vertListT.pop(0)))

    return vertListBDict

def makeBrick(dimensions, brickSize, numStudVerts=None, detail="Low Detail", stud=True):
    # create new bmesh object
    bme = bmesh.new()

    # set scale and thickness variables
    addedX = round(((dimensions["gap"] * brickSize[0]) - dimensions["gap"]),5)
    addedY = round(((dimensions["gap"] * brickSize[1]) - dimensions["gap"]),5)
    dX = dimensions["width"]
    dY = dimensions["width"]
    dZ = dimensions["height"]
    thick = dimensions["thickness"]
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
        studInset = thick * 0.9
        for xNum in range(brickSize[0]):
            for yNum in range(brickSize[1]):
                makeCylinder(r=dimensions["stud_radius"], N=numStudVerts, h=dimensions["stud_height"]+studInset, co=(xNum*dX*2,yNum*dY*2,dimensions["stud_offset"]-(studInset/2)), botFace=False, bme=bme)

    if detail == "Flat":
        bme.faces.new((v8, v7, v6, v5))
    else:
        # creating cylinder
        # making verts for hollow portion at bottom
        v9 = bme.verts.new((v5.co.x-thick, v5.co.y-thick, v5.co.z))
        v10 = bme.verts.new((v6.co.x+thick, v6.co.y-thick, v6.co.z))
        bme.faces.new((v5, v9, v10, v6))
        v11 = bme.verts.new((v7.co.x+thick, v7.co.y+thick, v7.co.z))
        bme.faces.new((v6, v10, v11, v7))
        v12 = bme.verts.new((v8.co.x-thick, v8.co.y+thick, v8.co.z))
        bme.faces.new((v7, v11, v12, v8))
        bme.faces.new((v8, v12, v9, v5))
        # making verts for hollow portion at top
        v13 = bme.verts.new((v9.co.x, v9.co.y, v1.co.z-thick))
        v14 = bme.verts.new((v10.co.x, v10.co.y, v2.co.z-thick))
        bme.faces.new((v9, v13, v14, v10))
        v15 = bme.verts.new((v11.co.x, v11.co.y, v3.co.z-thick))
        bme.faces.new((v10, v14, v15, v11))
        v16 = bme.verts.new((v12.co.x, v12.co.y, v4.co.z-thick))
        bme.faces.new((v11, v15, v16, v12))
        bme.faces.new((v12,v16, v13, v9))
        # make tubes
        for xNum in range(brickSize[0]-1):
            for yNum in range(brickSize[1]-1):
                makeTube(dimensions["stud_radius"], numStudVerts, (dZ*2)-thick, dimensions["tube_thickness"], co=((xNum * dX * 2) + dX, (yNum * dY * 2) + dY, -thick/2), bme=bme)
        # make face at top
        if detail == "Low Detail":
            bme.faces.new((v16, v15, v14, v13))
        # make small inner cylinder at top
        elif detail == "High Detail":
            botVertsDofDs = {}
            for xNum in range(brickSize[0]):
                for yNum in range(brickSize[1]):
                    r = dimensions["stud_radius"]-(2 * thick)
                    N = numStudVerts
                    h = thick * 0.99
                    botVertsD = makeInnerCylinder(r, N, h, co=(xNum*dX*2,yNum*dY*2,v16.co.z), bme=bme)
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
                    for i in range(1, len(vList1)):
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
                for i in range(1, len(vList1)):
                    v1 = vList1[i]
                    v2 = vList1[i-1]
                    v3 = vList2[i-1]
                    v4 = vList2[i]
                    bme.faces.new((v1, v2, v3, v4))
            for yNum in range(1, brickSize[1]):
                vList1 = botVertsDofDs[str(xNum) + "," + str(yNum-1)]["x+"] + botVertsDofDs[str(xNum) + "," + str(yNum-1)]["++"][::-1] + botVertsDofDs[str(xNum) + "," + str(yNum-1)]["y+"]
                vList2 = botVertsDofDs[str(xNum) + "," + str(yNum)]["x+"] + botVertsDofDs[str(xNum) + "," + str(yNum)]["+-"] + botVertsDofDs[str(xNum) + "," + str(yNum)]["y-"]
                for i in range(1, len(vList1)):
                    v1 = vList2[i]
                    v2 = vList2[i-1]
                    v3 = vList1[i-1]
                    v4 = vList1[i]
                    bme.faces.new((v1, v2, v3, v4))


    # bmesh.ops.transform(bme, matrix=Matrix.Translation(((dimensions["width"]/2)*(addedX),(dimensions["width"]/2)*(addedY),0)), verts=bme.verts)
    bmesh.ops.scale(bme, verts=bme.verts, vec=((dimensions["width"] + addedX/4)/dimensions["width"], (dimensions["width"] + addedY/4)/dimensions["width"], 1.0))

    # return bmesh
    return bme

## r = radius, N = numVerts, h = height, co = target cylinder position, botFace = Bool for creating face on bottom, bme = bmesh to insert mesh data into
#def makeCylinder(r, N, h, co=(0,0,0), botFace=True, bme=None):
#    # create new bmesh object
#    if bme == None:
#        bme = bmesh.new()

#    # create upper and lower circles
#    vertListT = []
#    vertListB = []
#    for i in range(N):
#        x = r * math.cos(((2 * math.pi) / N) * i)
#        y = r * math.sin(((2 * math.pi) / N) * i)
#        z = h / 2
#        coordT = (x + co[0], y + co[1], z + co[2])
#        coordB = (x + co[0], y + co[1], -z + co[2])
#        vertListT.append(bme.verts.new(coordT))
#        vertListB.append(bme.verts.new(coordB))

#    # create top and bottom faces
#    bme.faces.new(vertListT)
#    if botFace:
#        bme.faces.new(vertListB)

#    # create faces on the sides
#    bme.faces.new((vertListT[-1], vertListB[-1], vertListB[0], vertListT[0]))
#    for v in range(N-1):
#        bme.faces.new((vertListT.pop(0), vertListB.pop(0), vertListB[0], vertListT[0]))

#    # return bmesh
#    return bme

#def newObjFromBmesh(layer, bme, meshName, objName=False):

#    # if only one name given, use it for both names
#    if not objName:
#        objName = meshName

#    # create mesh and object
#    me = bpy.data.meshes.new(meshName)
#    ob = bpy.data.objects.new(objName, me)

#    scn = bpy.context.scene # grab a reference to the scene
#    scn.objects.link(ob)    # link new object to scene
#    scn.objects.active = ob # make new object active
#    ob.select = True        # make new object selected (does not deselect
#                             # other objects)
#
#    obj = bme.to_mesh(me)         # push bmesh data into me

#    # move to appropriate layer
#    layerList = []
#    for i in range(20):
#        if i == layer-1:
#            layerList.append(True)
#        else:
#            layerList.append(False)
#    bpy.ops.object.move_to_layer(layers=layerList)
#    bpy.context.scene.layers = layerList
#    bpy.ops.object.select_all(action='TOGGLE')
#    return ob

#def deleteExisting():
#    # delete existing objects
#    tmpList = [True]*20
#    bpy.context.scene.layers = tmpList
#    for i in range(2):
#        bpy.ops.object.select_all(action='TOGGLE')
#        bpy.ops.object.delete(use_global=False)
#    bpy.context.scene.layers = [False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True]

#def main():
#    deleteExisting()

#    # create objects
#    dimensions = {'gap': 0.0015000000260770308, 'width': 0.12500000496705374, 'stud_diameter': 0.07500000298023224, 'height': 0.15000000596046448, 'stud_offset': 0.08906250353902578, 'thickness': 0.02500000099341075, 'tube_thickness': 0.013359375530853868, 'logo_width': 0.05843750232209763, 'stud_radius': 0.03750000149011612, 'stud_height': 0.028125001117587093, 'logo_offset': 0.10312500409781933}
#    newObjFromBmesh(1, makeBrick(dimensions=dimensions, brickSize=[1,1], numStudVerts=16, detail="Flat"), "1x1 flat").location = (-.2,0,0)
#    newObjFromBmesh(1, makeBrick(dimensions=dimensions, brickSize=[1,1], numStudVerts=16, detail="Low Detail"), "1x1 low").location = (0,0,0)
#    newObjFromBmesh(1, makeBrick(dimensions=dimensions, brickSize=[1,1], numStudVerts=16, detail="High Detail"), "1x1 high").location = (.2,0,0)
#    newObjFromBmesh(2, makeBrick(dimensions=dimensions, brickSize=[1,2], numStudVerts=16, detail="Flat"), "1x2 flat").location = (-.2,0,0)
#    newObjFromBmesh(2, makeBrick(dimensions=dimensions, brickSize=[1,2], numStudVerts=16, detail="Low Detail"), "1x2 low").location = (0,0,0)
#    newObjFromBmesh(2, makeBrick(dimensions=dimensions, brickSize=[1,2], numStudVerts=16, detail="High Detail"), "1x2 high").location = (.2,0,0)
#    newObjFromBmesh(3, makeBrick(dimensions=dimensions, brickSize=[2,2], numStudVerts=16, detail="Flat"), "2x2 flat").location = (-.3,0,0)
#    newObjFromBmesh(3, makeBrick(dimensions=dimensions, brickSize=[2,2], numStudVerts=16, detail="Low Detail"), "2x2 low").location = (0,0,0)
#    newObjFromBmesh(3, makeBrick(dimensions=dimensions, brickSize=[2,2], numStudVerts=16, detail="High Detail"), "2x2 high").location = (.3,0,0)
#    newObjFromBmesh(4, makeBrick(dimensions=dimensions, brickSize=[2,6], numStudVerts=16, detail="Flat"), "2x6 flat").location = (-.3,0,0)
#    newObjFromBmesh(4, makeBrick(dimensions=dimensions, brickSize=[2,6], numStudVerts=16, detail="Low Detail"), "2x6 low").location = (0,0,0)
#    newObjFromBmesh(4, makeBrick(dimensions=dimensions, brickSize=[2,6], numStudVerts=16, detail="High Detail"), "2x6 high").location = (.3,0,0)
#
#    layerToOpen = 1

#    layerList = []
#    for i in range(20):
#        if i == layerToOpen-1: layerList.append(True)
#        else: layerList.append(False)
#    bpy.context.scene.layers = layerList

#main()
