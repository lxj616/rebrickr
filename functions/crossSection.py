import bpy
import bmesh
from mathutils import Matrix, Vector

def run(bm, x=None, y=None, z=None):
    # initialize values based on plane being tested
    if x != None:
        translationMatrix1 = Matrix.Translation(Vector((-x, 0, 0)))
        translationMatrix2 = Matrix.Translation(Vector(( x, 0, 0)))
    elif y != None:
        translationMatrix1 = Matrix.Translation(Vector((0, -y, 0)))
        translationMatrix2 = Matrix.Translation(Vector((0,  y, 0)))
    else:
        translationMatrix1 = Matrix.Translation(Vector((0, 0, -z)))
        translationMatrix2 = Matrix.Translation(Vector((0, 0,  z)))


    # create new bmesh object
    crossBMesh = bmesh.new()
    bm.transform(translationMatrix1)

    # ensure lookup tables for indexing
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    i = 0
    crossD = {}
    # if vertex from source on plane, create equivalent vert in bmesh
    for vert in bm.verts:
        if (z != None and abs(vert.co.z) <= 0.001) or (y != None and abs(vert.co.y) <= 0.001) or (x != None and abs(vert.co.x) <= 0.001):
            bmv = crossBMesh.verts.new(vert.co)
            bmv.normal = vert.normal
            crossD[i] = {'faces': vert.link_faces, 'edges': vert.link_edges, 'type': 'vert'}
            i += 1
    # if edge from source intersects plane, create vert at intersection in bmesh
    for edge in bm.edges:
        v0 = edge.verts[0]
        v1 = edge.verts[1]
        p0 = v0.co
        p1 = v1.co
        if z != None:
            if (p0.z < -0.001 and p1.z > 0.001) or (p0.z > 0.001 and p1.z < -0.001):
                t = abs(p0.z) / abs(p1.z - p0.z)
                pos = (p1 * t) + (p0 * (1-t))
                bmv = crossBMesh.verts.new(pos)
                bmv.normal = (v0.normal + v1.normal) / 2
                crossD[i] = {'faces': edge.link_faces, 'edges': vert.link_edges, 'type': 'edge'}
                i += 1
        elif y != None:
            if (p0.y < -0.001 and p1.y > 0.001) or (p0.y > 0.001 and p1.y < -0.001):
                t = abs(p0.y) / abs(p1.y - p0.y)
                pos = (p1 * t) + (p0 * (1-t))
                bmv = crossBMesh.verts.new(pos)
                bmv.normal = (v0.normal + v1.normal) / 2
                crossD[i] = {'faces': edge.link_faces, 'edges': vert.link_edges, 'type': 'edge'}
                i += 1
        else:
            if (p0.x < -0.001 and p1.x > 0.001) or (p0.x > 0.001 and p1.x < -0.001):
                t = abs(p0.x) / abs(p1.x - p0.x)
                pos = (p1 * t) + (p0 * (1-t))
                bmv = crossBMesh.verts.new(pos)
                bmv.normal = (v0.normal + v1.normal) / 2
                crossD[i] = {'faces': edge.link_faces, 'edges': vert.link_edges, 'type': 'edge'}
                i += 1

    crossBMesh.verts.ensure_lookup_table()
    crossBMesh.edges.ensure_lookup_table()
    #take two vertices
    for key in crossD:
        for key2 in crossD:
            #This will tell us if we need to check edges (yes if false)
            linked = False
            if key2 <= key:
                continue
            #For all of the connected faces of one vertex:
            for face in crossD[key]['faces']:
                #If the same face is connected to the other vertex
                if face in crossD[key2]['faces']:
                    #If one is an edge, make the new edge
                    if crossD[key]['type'] == 'edge' or crossD[key2]['type'] == 'edge':
                        crossBMesh.edges.new((crossBMesh.verts[key], crossBMesh.verts[key2]))
                        linked = True
                        break
                    else:
                        breakOuter = False
                        vert1 = crossBMesh.verts[key].co
                        vert2 = crossBMesh.verts[key2].co
                        for edge in bm.edges:
                            bmVert1 = edge.verts[0].co
                            bmVert2 = edge.verts[1].co
                            if (equal(vert1, bmVert1) and equal(vert2, bmVert2)) or (equal(vert2, bmVert1) and equal(vert1, bmVert2)):
                                e = crossBMesh.edges.new((crossBMesh.verts[key], crossBMesh.verts[key2]))
                                breakOuter = True
                                linked = True
                                break
                        if breakOuter:
                            linked = True
                            break
            #no edge was created
            if not linked:
                for edge in crossD[key]['edges']:
                    if edge in crossD[key2]['edges']:
                        vert1 = crossBMesh.verts[key].co
                        vert2 = crossBMesh.verts[key2].co
                        bmVert1 = edge.verts[0].co
                        bmVert2 = edge.verts[1].co
                        if (equal(vert1, bmVert1) and equal(vert2, bmVert2)) or (equal(vert2, bmVert1) and equal(vert1, bmVert2)):
                            try:
                                crossBMesh.edges.new((crossBMesh.verts[key], crossBMesh.verts[key2]))
                            except:
                                continue

    crossBMesh.transform(translationMatrix2)
    bm.transform(translationMatrix2)
    return crossBMesh

def equal(vec1, vec2):
    if (vec1 - vec2).length < .05:
        return True
    return False

def drawBMesh(BMesh, name="drawnBMesh"):
    """ create mesh and object from bmesh """
    # note: neither are linked to the scene, yet, so they won't show in the 3d view
    m = bpy.data.meshes.new(name + "_mesh")
    obj = bpy.data.objects.new(name, m)

    scn = bpy.context.scene  # grab a reference to the scene
    scn.objects.link(obj)    # link new object to scene
    scn.objects.active = obj # make new object active
    obj.select = True        # make new object selected (does not deselect other objects)
    BMesh.to_mesh(m)         # push bmesh data into m
    return obj

def slices(obj, numSlices, brickHeight, axis="z", drawSlices=False):
    if axis not in "xyz":
        return []
    if numSlices <= 1:
        return []
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    bm.verts.ensure_lookup_table()
    if axis == "z":
        Max = max(v.co.z for v in bm.verts)
        Min = min(v.co.z for v in bm.verts)
        z = Min
    elif axis == "y":
        Max = max(v.co.y for v in bm.verts)
        Min = min(v.co.y for v in bm.verts)
        y = Min
    else:
        Max = max(v.co.x for v in bm.verts)
        Min = min(v.co.x for v in bm.verts)
        x = Min
    ran = Max - Min
    slices = []
    for i in range(numSlices):
        if axis == "z":
            BMResult = run(bm, z=z)
            z += brickHeight
        elif axis == "y":
            BMResult = run(bm, y=y)
            y += brickHeight
        else:
            BMResult = run(bm, x=x)
            x += brickHeight
        if len(BMResult.verts) > 0:
            slices.append(BMResult)
            if drawSlices:
                drawBMesh(BMResult)

    return slices
