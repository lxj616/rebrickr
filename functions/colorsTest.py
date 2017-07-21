# from https://blender.stackexchange.com/questions/79236/access-color-of-a-point-given-the-3d-position-on-the-surface-of-a-polygon?rq=1
# also see: https://blender.stackexchange.com/questions/51782/get-material-and-color-of-material-on-a-face-of-an-object-in-python?rq=1
# and also: https://blender.stackexchange.com/questions/909/how-can-i-set-and-get-the-vertex-color-property

import bpy
import bmesh
from mathutils.bvhtree import BVHTree
from mathutils import Vector
from mathutils.geometry import barycentric_transform

def TriangulateMesh( obj ):
    bm = bmesh.new()
    bm.from_mesh( obj.data )
    bmesh.ops.triangulate( bm, faces=bm.faces[:] )
    bm.to_mesh( obj.data )
    bm.free()

def CopyMesh( obj ):
    copy = obj.copy()
    copy.data = obj.data.copy()
    bpy.context.scene.objects.link( copy )
    bpy.context.scene.update()
    return copy

def main():
    # get object
    obj = bpy.data.objects['Ogre']
    # triangulate it
    TriangulateMesh(obj)
    #Eventually, work on a copy:
    obj0 = CopyMesh(obj)

    # ray cast
    _, location, normal, index = obj0.ray_cast(Vector((0,0,0)),Vector((0,0,1)))

    #Get 3D vertices indices
    verticesIndices = obj.data.polygons[index].vertices
    #P vertices coordinates in 3D space
    p1, p2, p3 = [obj.data.vertices[verticesIndices[i]].co for i in range(3)]
    #P UV map vertices indices are found in:
    uvMapIndices = obj.data.polygons[index].loop_indices
    #The UV map
    uvMap = obj.data.uv_layers[0]
    # The coordinates of P vertices in the UV map space:
    uv1, uv2, uv3 = [uvMap.data[uvMapIndices[i]].uv for i in range(3)]

    # Calculate V' using barycentric_transform
    Vprime = barycentric_transform( location, p1, p2, p3, uv1, uv2, uv3 )
    print(Vprime)

    image = bpy.data.images['Material Diffuse Color']
    pixels = list( image.pixels ) #Faster than accessible image.pixels[x] each time
    width = image.size[0]
    height = image.size[1]

    print(Vprime)

main()
