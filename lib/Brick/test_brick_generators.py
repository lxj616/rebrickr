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
import bpy

# Blender imports
# NONE!

# Rebrickr imports
from .mesh_generators import *
from .get_brick_dimensions import *
from ...functions.common import *
from ...functions.general import *
from ...functions.makeBricks_utils import *


class testBrickGenerators(bpy.types.Operator):
    """Draws some test bricks for testing of brick generators"""
    bl_idname = "rebrickr.test_brick_generators"
    bl_label = "Test Brick Generators"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            test_brick_generators()
        except:
            handle_exception()
        return{"FINISHED"}

    @staticmethod
    def drawUIButton():
        return False


def newObjFromBmesh(layer, bme, meshName, objName=None, loc=(0,0,0), edgeSplit=True):
    scn = bpy.context.scene
    # if only one name given, use it for both names
    objName = objName or meshName

    # create mesh and object
    me = bpy.data.meshes.new(meshName)
    ob = bpy.data.objects.new(objName, me)
    # move object to target location
    ob.location = loc
    # link and select object
    scn.objects.link(ob)
    select(ob, active=ob)
    scn.update()

    # send bmesh data to object data
    bme.to_mesh(me)
    ob.data.update()

    # add edge split modifier
    if edgeSplit:
        addEdgeSplitMod(ob)

    # move to appropriate layer
    layerList = [i == layer - 1 for i in range(20)]
    bpy.ops.object.move_to_layer(layers=layerList)

    print("Created object '" + objName + "'")

    return ob


def test_brick_generators():
    # try to delete existing objects
    delete(list(bpy.data.objects))

    # create objects
    scn, cm, _ = getActiveContextInfo()
    dimensions = get_brick_dimensions(height=0.5, zScale=getZStep(cm))
    offset = -2.5
    for detail in ["FLAT", "LOW", "MEDIUM", "HIGH"]:
        offset += 1
        # STANDARD BRICKS
        newObjFromBmesh(1,  makeStandardBrick(dimensions=dimensions, brickSize=[1,1,3], type=cm.brickType, circleVerts=16, detail=detail), "1x1 " + detail, loc=(offset,   0,0))
        newObjFromBmesh(2,  makeStandardBrick(dimensions=dimensions, brickSize=[1,2,3], type=cm.brickType, circleVerts=16, detail=detail), "1x2 " + detail, loc=(offset,   0,0))
        newObjFromBmesh(3,  makeStandardBrick(dimensions=dimensions, brickSize=[3,1,3], type=cm.brickType, circleVerts=16, detail=detail), "3x1 " + detail, loc=(0, offset,  0))
        newObjFromBmesh(4,  makeStandardBrick(dimensions=dimensions, brickSize=[1,8,3], type=cm.brickType, circleVerts=16, detail=detail), "1x8 " + detail, loc=(offset,   0,0))
        newObjFromBmesh(5,  makeStandardBrick(dimensions=dimensions, brickSize=[2,2,3], type=cm.brickType, circleVerts=16, detail=detail), "2x2 " + detail, loc=(offset*2, 0,0))
        newObjFromBmesh(11,  makeStandardBrick(dimensions=dimensions, brickSize=[2,6,3], type=cm.brickType, circleVerts=16, detail=detail), "2x6 " + detail, loc=(offset*2, 0,0))
        newObjFromBmesh(12,  makeStandardBrick(dimensions=dimensions, brickSize=[6,2,3], type=cm.brickType, circleVerts=15, detail=detail), "6x2 " + detail, loc=(0, offset*2,0))
        # ROUND BRICKS
        newObjFromBmesh(6,  makeRound1x1(dimensions=dimensions, circleVerts=16, type="CYLINDER",    detail=detail), "1x1 Round " + detail,  loc=(offset, 1.5,0))
        newObjFromBmesh(6,  makeRound1x1(dimensions=dimensions, circleVerts=16, type="CONE",        detail=detail), "1x1 Cone "  + detail,  loc=(offset, 0.5,0))
        newObjFromBmesh(6,  makeRound1x1(dimensions=dimensions, circleVerts=16, type="STUD",        detail=detail), "1x1 Stud "  + detail,  loc=(offset,-0.5,0))
        newObjFromBmesh(6,  makeRound1x1(dimensions=dimensions, circleVerts=16, type="STUD_HOLLOW", detail=detail), "1x1 Stud2 "  + detail, loc=(offset,-1.5,0))
        # SLOPE BRICKS
        i = 0
        for posNeg in ["+", "-"]:
            for j in [-1, 1]:
                direction = ("X" if j == 1 else "Y") + posNeg
                newObjFromBmesh(16 + i, makeSlope(dimensions=dimensions, brickSize=[2,1][::j] + [3], direction=direction, circleVerts=16, detail=detail), "2x1 Slope "  + detail, loc=[-5.5, offset][::j]               + [0])
                newObjFromBmesh(16 + i, makeSlope(dimensions=dimensions, brickSize=[3,1][::j] + [3], direction=direction, circleVerts=16, detail=detail), "3x1 Slope "  + detail, loc=[-4,   offset][::j]               + [0])
                newObjFromBmesh(16 + i, makeSlope(dimensions=dimensions, brickSize=[4,1][::j] + [3], direction=direction, circleVerts=16, detail=detail), "4x1 Slope "  + detail, loc=[-2,   offset][::j]               + [0])
                newObjFromBmesh(16 + i, makeSlope(dimensions=dimensions, brickSize=[2,2][::j] + [3], direction=direction, circleVerts=16, detail=detail), "2x2 Slope "  + detail, loc=[0.25, offset * 1.5 - 0.25][::j]  + [0])
                newObjFromBmesh(16 + i, makeSlope(dimensions=dimensions, brickSize=[3,2][::j] + [3], direction=direction, circleVerts=16, detail=detail), "3x2 Slope "  + detail, loc=[1.75, offset * 1.5 - 0.25][::j]  + [0])
                newObjFromBmesh(16 + i, makeSlope(dimensions=dimensions, brickSize=[4,2][::j] + [3], direction=direction, circleVerts=16, detail=detail), "4x2 Slope "  + detail, loc=[3.75, offset * 1.5 - 0.25][::j]  + [0])
                newObjFromBmesh(16 + i, makeSlope(dimensions=dimensions, brickSize=[3,4][::j] + [3], direction=direction, circleVerts=16, detail=detail), "4x3 Slope "  + detail, loc=[6.25, offset * 2.0 - 0.625][::j] + [0])
                i += 1

    openLayer(6)
