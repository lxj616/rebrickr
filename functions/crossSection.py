import bpy
import bmesh
from mathutils import Matrix, Vector

def run(z, bm):
    # create new bmesh object
    crossBMesh = bmesh.new()
    bm.transform(Matrix.Translation(Vector((0, 0, -z))))

    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    i = 0
    crossD = {}
    for vert in bm.verts:
        if(abs(vert.co.z) <= 0.001):
            crossBMesh.verts.new(vert.co)
            crossD[i] = {'faces': vert.link_faces, 'edges': vert.link_edges, 'type': 'vert'}
            i += 1
    for edge in bm.edges:
        p0 = edge.verts[0].co
        p1 = edge.verts[1].co
        if (p0.z < -0.001 and p1.z > 0.001) or (p0.z > 0.001 and p1.z < -0.001):
            vector = p1 - p0
            t = abs(p0.z) / abs(p1.z - p0.z)
            pos = (p1 * t) + (p0 * (1-t))
            crossBMesh.verts.new(pos)
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
                                crossBMesh.edges.new((crossBMesh.verts[key], crossBMesh.verts[key2]))
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

    bm.transform(Matrix.Translation(Vector((0, 0, z))))
    return crossBMesh

def equal(vec1, vec2):
    if (vec1 - vec2).length < .05:
        return True
    return False

def draw(crossBMesh, x, y, z):
    # create mesh and object
    # note: neither are linked to the scene, yet, so they won't show
    # in the 3d view
    crossMesh = bpy.data.meshes.new('crossMesh')
    crossOb = bpy.data.objects.new('crossOb', crossMesh)

    scn = bpy.context.scene # grab a reference to the scene
    scn.objects.link(crossOb)    # link new object to scene
    scn.objects.active = crossOb # make new object active
    crossOb.select = True        # make new object selected (does not deselect
                            # other objects)
    crossBMesh.to_mesh(crossMesh)         # push bmesh data into me

    bpy.context.active_object.location.z = z

def slices(drawSlices, numSlices):
    obj = bpy.context.object.data
    bm = bmesh.new()
    bm.from_mesh(obj)
    bm.transform(bpy.context.object.matrix_world)
    bm.verts.ensure_lookup_table()
    zMax = max(v.co.z for v in bm.verts)
    zMin = min(v.co.z for v in bm.verts)
    ran = zMax - zMin
    z = zMin
    x = -6
    y = -6
    slices = []
    for i in range(numSlices):
        if drawSlices:
            BMResult = run(z, bm)
            draw(BMResult, 0, 0, z)
            slices.append(BMResult)
        else:
            BMResult = run(z, bm)
            slices.append(BMResult)
        z += ran/(numSlices - 1)
        y += 3
        if i == 4:
            x = -3
            y = -6

    return {"slices":slices, "sliceHeight":ran/(numSlices - 1)}
