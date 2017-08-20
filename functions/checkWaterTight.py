import bmesh

def addConnectedVerts(v_index, bme, connected_verts, marked_edges, max_depth=900, level=0):
    if level > max_depth:
        return "max_depth exceeded"
    for e in bme.verts[v_index].link_edges:
        if e not in marked_edges:
            marked_edges.append(e)
            for v in e.verts:
                if v.index not in connected_verts:
                    connected_verts.append(v.index)
                    addConnectedVerts(v.index, bme, connected_verts, marked_edges, level=level+1)

def getConnectedVerts(mesh, v_index=0):
    bpy.ops.object.mode_set(mode='EDIT', toggle=False) # Go to edit mode
    bpy.ops.mesh.select_all(action="DESELECT") # unselect everything

    loops = []
    faces = bm.faces

    while faces:
        faces[0].select_set(True) # select 1st face
        bpy.ops.mesh.select_linked() # select all linked faces makes a full loop
        loops.append([f.index for f in faces if f.select])
        bpy.ops.mesh.hide(unselected=False) # hide the detected loop
        faces = [f for f in bm.faces if not f.hide] # update faces

    return connected_verts

def isOneMesh(mesh):
    connected = getConnectedVerts(mesh)
    print(len(connected), len(mesh.vertices))

    if type(connected) == str:
        return connected
    elif len(connected) == len(mesh.vertices):
        return True
    else:
        return False
