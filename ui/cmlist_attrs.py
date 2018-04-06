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
# NONE!

# Blender imports
import bpy
from bpy.props import *

# Addon imports
from ..functions import *
from .cmlist_utils import *


# Create custom property group
class Bricker_CreatedModels(bpy.types.PropertyGroup):
    # CMLIST ITEM SETTINGS
    name = StringProperty(update=uniquifyName)
    id = IntProperty()
    idx = IntProperty()

    # NAME OF SOURCE
    source_name = StringProperty(
        name="Source Object Name",
        description="Name of the source object to Brickify",
        default="",
        update=setNameIfEmpty)

    # TRANSFORMATION SETTINGS
    modelLoc = StringProperty(default="-1,-1,-1")
    modelRot = StringProperty(default="-1,-1,-1")
    modelScale = StringProperty(default="-1,-1,-1")
    transformScale = FloatProperty(
        name="Scale",
        description="Scale of the brick model",
        update=updateModelScale,
        step=1,
        default=1.0)
    applyToSourceObject = BoolProperty(
        name="Apply to source",
        description="Apply transformations to source object when Brick Model is deleted",
        default=True)
    parent_name = StringProperty(default="")
    exposeParent = BoolProperty(
        name="Expose parent object",
        description="Expose the parent object for this model and make it active for simple transformations",
        update=updateParentExposure,
        default=False)

    # ANIMATION SETTINGS
    startFrame = IntProperty(
        name="Start Frame",
        description="Start frame of Brick animation",
        update=dirtyAnim,
        min=0, max=500000,
        default=1)
    stopFrame = IntProperty(
        name="Stop Frame",
        description="Stop frame of Brick animation",
        update=dirtyAnim,
        min=0, max=500000,
        default=10)
    useAnimation = BoolProperty(
        name="Use Animation",
        description="Create Brick Model for each frame, from start to stop frame (WARNING: Calculation takes time, and may result in large blend file size)",
        update=updateStartAndStopFrames,
        default=False)

    # BASIC MODEL SETTINGS
    brickHeight = FloatProperty(
        name="Brick Height",
        description="Height of the bricks in the final Brick Model",
        update=dirtyMatrix,
        step=1,
        precision=3,
        min=0.001, max=10,
        default=0.1)
    gap = FloatProperty(
        name="Gap Between Bricks",
        description="Distance between bricks",
        update=dirtyMatrix,
        step=1,
        precision=3,
        min=0, max=0.1,
        default=0.01)
    mergeSeed = IntProperty(
        name="Random Seed",
        description="Random seed for brick merging calculations",
        update=dirtyBuild,
        min=-1, max=5000,
        default=1000)
    connectThresh = IntProperty(
        name="Connectivity",
        description="Quality of the model's brick connectivity (higher numbers are slower but better quality)",
        update=dirtyBuild,
        min=1, max=50,
        default=1)
    smokeThresh = FloatProperty(
        name="Smoke Threshold",
        description="Threshold for turning smoke density into bricks (lower values for denser model)",
        update=dirtyMatrix,
        min=0.0000000001, max=1,
        default=0.1)
    splitModel = BoolProperty(
        name="Split Model",
        description="Split model into separate objects (slower)",
        update=dirtyModel,
        default=False)
    randomLoc = FloatProperty(
        name="Random Location",
        description="Max random location applied to each brick",
        update=dirtyModel,
        step=1,
        precision=3,
        min=0, max=1,
        default=0.005)
    randomRot = FloatProperty(
        name="Random Rotation",
        description="Max random rotation applied to each brick",
        update=dirtyModel,
        step=1,
        precision=3,
        min=0, max=1,
        default=0.025)
    brickShell = EnumProperty(
        name="Brick Shell",
        description="Choose whether the shell of the model will be inside or outside source mesh",
        items=[("INSIDE", "Inside Mesh (recommended)", "Draw brick shell inside source mesh (Recommended)"),
               ("OUTSIDE", "Outside Mesh", "Draw brick shell outside source mesh"),
               ("INSIDE AND OUTSIDE", "Inside and Outside", "Draw brick shell inside and outside source mesh (two layers)")],
        update=dirtyMatrix,
        default="INSIDE")
    calculationAxes = EnumProperty(
        name="Expanded Axes",
        description="The brick shell will be drawn on the outside in these directions",
        items=[("XYZ", "XYZ", "PLACEHOLDER"),
               ("XY", "XY", "PLACEHOLDER"),
               ("YZ", "YZ", "PLACEHOLDER"),
               ("XZ", "XZ", "PLACEHOLDER"),
               ("X", "X", "PLACEHOLDER"),
               ("Y", "Y", "PLACEHOLDER"),
               ("Z", "Z", "PLACEHOLDER")],
        update=dirtyMatrix,
        default="XY")
    shellThickness = IntProperty(
        name="Shell Thickness",
        description="Thickness of the Brick shell",
        update=dirtyBuild,
        min=1, max=100,
        default=1)

    # BRICK TYPE SETTINGS
    brickType = EnumProperty(
        name="Brick Type",
        description="Type of brick used to build the model",
        items=[("PLATES", "Plates Only", "Use plates to build the model"),
               ("BRICKS", "Bricks Only (fast)", "Use bricks to build the model"),
               ("BRICKS AND PLATES", "Bricks and Plates", "Use bricks and plates to build the model"),
               ("CUSTOM", "Custom", "Use custom object to build the model")],
        update=dirtyMatrix,
        default="BRICKS")
    alignBricks = BoolProperty(
        name="Align Bricks Horizontally",
        description="Keep bricks aligned horizontally, and fill the gaps with plates",
        update=dirtyBuild,
        default=True)
    offsetBrickLayers = IntProperty(
        name="Offset Brick Layers",
        description="Offset the layers that will be merged into bricks if possible",
        update=dirtyBuild,
        step=1,
        min=0, max=2,
        default=1)
    maxWidth = IntProperty(
        name="Max Width",
        description="Maximum brick width",
        update=dirtyBuild,
        step=1,
        min=1, max=16,
        default=2)
    maxDepth = IntProperty(
        name="Max Depth",
        description="Maximum brick depth",
        update=dirtyBuild,
        step=1,
        min=1, max=24,
        default=10)
    customObjectName = StringProperty(
        name="Custom Object Name",
        description="Name of the object to use as bricks",
        update=dirtyMatrix,
        default="")
    distOffsetX = FloatProperty(
        name="X",
        description="Offset of custom bricks on X axis (1.0 = side-by-side)",
        update=dirtyMatrix,
        step=1,
        precision=3,
        min=0.001, max=2,
        default=1)
    distOffsetY = FloatProperty(
        name="Y",
        description="Offset of custom bricks on Y axis (1.0 = side-by-side)",
        step=1,
        update=dirtyMatrix,
        precision=3,
        min=0.001, max=2,
        default=1)
    distOffsetZ = FloatProperty(
        name="Z",
        description="Offset of custom bricks on Z axis (1.0 = side-by-side)",
        step=1,
        update=dirtyMatrix,
        precision=3,
        min=0.001, max=2,
        default=1)

    # CUSTOMIZE SETTINGS
    autoUpdateExposed = BoolProperty(
        name="Auto Update Exposed",
        description="When bricks are deleted, automatically update bricks that become exposed",
        default=True)

    # MATERIAL & COLOR SETTINGS
    materialType = EnumProperty(
        name="Material Type",
        description="Choose what materials will be applied to model",
        items=[("NONE", "None", "No material applied to bricks"),
               ("RANDOM", "Random", "Apply a random material from Brick materials to each generated brick"),
               ("CUSTOM", "Custom", "Choose a custom material to apply to all generated bricks"),
               ("SOURCE", "Use Source Materials", "Apply material based on closest intersecting face")],
        update=dirtyMaterial,
        default="SOURCE")
    materialName = StringProperty(
        name="Material Name",
        description="Name of the material to apply to all bricks",
        default="")
    internalMatName = StringProperty(
        name="Material Name",
        description="Name of the material to apply to bricks inside material shell",
        update=dirtyMaterial,
        default="")
    matShellDepth = IntProperty(
        name="Material Shell Depth",
        description="Depth to which the outer materials should be applied (1 = Only exposed bricks",
        step=1,
        min=1, max=100,
        default=1,
        update=dirtyModel)
    mergeInconsistentMats = BoolProperty(
        name="Merge Inconsistent Materials",
        description="Merge 1x1 bricks to form larger bricks whether or not they share a material",
        default=False,
        update=dirtyBuild)
    randomMatSeed = IntProperty(
        name="Random Seed",
        description="Random seed for material assignment",
        min=-1, max=5000,
        default=1000)
    useUVMap = BoolProperty(
        name="Use UV Map",
        description="Transfer colors from source UV map",
        default=True,
        update=dirtyMaterial)
    uvImageName = StringProperty(
        name="UV Image",
        description="UV Image to use for UV Map color transfer (defaults to active UV if left blank)",
        default="",
        update=dirtyBuild)
    colorSnap = EnumProperty(
        name="Color Snaping",
        description="Snap nearest source materials",
        items=[("NONE", "None", "Use source materials as is"),
               ("ABS", "ABS Plastic", "Use ABS Plastic Materials"),
               ("RGB", "RGB Average", "Use average RGB value of snapped colors")],
        update=dirtyMaterial,
        default="NONE")
    colorSnapAmount = FloatProperty(
        name="Color Snap Amount",
        description="Amount to snap colors by",
        precision=3,
        min=0.000001, max=1.0,
        default=0.00001,
        update=dirtyBuild)

    # BRICK DETAIL SETTINGS
    studDetail = EnumProperty(
        name="Stud Detailing",
        description="Choose where to draw the studs",
        items=[("ALL", "On All Bricks", "Include Brick Logo only on bricks with studs exposed"),
               ("EXPOSED", "On Exposed Bricks", "Include Brick Logo only on bricks with studs exposed"),
               ("NONE", "None", "Don't include Brick Logo on bricks")],
        update=dirtyBricks,
        default="EXPOSED")
    logoDetail = EnumProperty(
        name="Logo Detailing",
        description="Choose where to draw the logo",
        items=[("CUSTOM", "Custom Logo", "Choose a mesh object to use as the brick stud logo"),
               ("LEGO", "LEGO Logo", "Include a LEGO logo on each stud"),
               ("NONE", "None", "Don't include Brick Logo on bricks")],
        update=dirtyBricks,
        default="NONE")
    logoResolution = FloatProperty(
        name="Logo Resolution",
        description="Resolution of the Brick Logo",
        update=dirtyBricks,
        min=0.1, max=1,
        step=1,
        precision=1,
        default=0.2)
    logoObjectName = StringProperty(
        name="Logo Object Name",
        description="Name of the logo object",
        update=dirtyBricks,
        default="")
    logoScale = FloatProperty(
        name="Logo Scale",
        description="Scale of the logo (relative to stud scale)",
        step=1,
        update=dirtyBricks,
        precision=2,
        min=0.000001, max=2,
        default=0.78)
    logoInset = FloatProperty(
        name="Logo Inset",
        description="How deep to inset the logo into the stud",
        step=1,
        update=dirtyBricks,
        precision=2,
        min=0.0, max=1.0,
        default=0.02)
    hiddenUndersideDetail = EnumProperty(
        name="Underside Detailing of Obstructed Bricks",
        description="Choose the level of detail to include for the underside of obstructed bricks",
        items=[("FLAT", "Flat", "draw single face on brick underside"),
               ("LOW", "Low", "Draw minimal details on brick underside"),
               ("MEDIUM", "Medium", "Draw most details on brick underside"),
               ("HIGH", "High", "Draw intricate details on brick underside")],
        update=dirtyBricks,
        default="FLAT")
    exposedUndersideDetail = EnumProperty(
        name="Underside Detailing of Exposed Bricks",
        description="Choose the level of detail to include for the underside of exposed bricks",
        items=[("FLAT", "Flat", "draw single face on brick underside"),
               ("LOW", "Low", "Draw minimal details on brick underside"),
               ("MEDIUM", "Medium", "Draw most details on brick underside"),
               ("HIGH", "High", "Draw intricate details on brick underside")],
        update=dirtyBricks,
        default="FLAT")
    circleVerts = IntProperty(
        name="Num Verts",
        description="Number of vertices for each circle of brick mesh",
        update=updateCircleVerts,
        min=4, max=64,
        default=16)
    # BEVEL SETTINGS
    bevelWidth = FloatProperty(
        name="Bevel Width",
        description="Bevel value/amount",
        step=1,
        min=0.000001, max=10,
        default=-1,
        update=updateBevel)
    bevelSegments = IntProperty(
        name="Bevel Resolution",
        description="Number of segments for round edges/verts",
        step=1,
        min=1, max=10,
        default=1,
        update=updateBevel)
    bevelProfile = FloatProperty(
        name="Bevel Profile",
        description="The profile shape (0.5 = round)",
        step=1,
        min=0, max=1,
        default=0.7,
        update=updateBevel)

    # INTERNAL SUPPORTS SETTINGS
    internalSupports = EnumProperty(
        name="Internal Supports",
        description="Choose what type of brick support structure to use inside your model",
        items=[("NONE", "None", "No internal supports"),
               ("LATTICE", "Lattice", "Use latice inside model"),
               ("COLUMNS", "Columns", "Use columns inside model")],
        update=dirtyInternal,
        default="NONE")
    latticeStep = IntProperty(
        name="Step",
        description="Distance between cross-beams",
        update=dirtyInternal,
        step=1,
        min=2, max=25,
        default=2)
    alternateXY = BoolProperty(
        name="Alternate X and Y",
        description="Alternate back-and-forth and side-to-side beams",
        update=dirtyInternal,
        default=False)
    colThickness = IntProperty(
        name="Thickness",
        description="Thickness of the columns",
        update=dirtyInternal,
        min=1, max=25,
        default=2)
    colStep = IntProperty(
        name="Step",
        description="Distance between columns",
        update=dirtyInternal,
        step=1,
        min=1, max=25,
        default=2)

    # ADVANCED SETTINGS
    insidenessRayCastDir = EnumProperty(
        name="Insideness Ray Cast Direction",
        description="Choose which axis/axes to cast rays for calculation of insideness",
        items=[("HIGH EFFICIENCY", "High Efficiency", "Reuses single ray casted in brickFreqMatrix calculations"),
               ("X", "X", "Cast rays along X axis for insideness calculations"),
               ("Y", "Y", "Cast rays along Y axis for insideness calculations"),
               ("Z", "Z", "Cast rays along Z axis for insideness calculations"),
               ("XYZ", "XYZ (Best Result)", "Cast rays in all axis directions for insideness calculation (slowest; uses result consistent for at least 2 of the 3 rays)")],
        update=dirtyMatrix,
        default="HIGH EFFICIENCY")
    castDoubleCheckRays = BoolProperty(
        name="Cast Both Directions",
        description="Cast rays in both positive and negative directions on the axes specified for insideness calculation (Favors outside; uncheck to cast only in positive direction)",
        default=True,
        update=dirtyMatrix)
    useNormals = BoolProperty(
        name="Use Normals",
        description="Use normals to calculate insideness of bricks (WARNING: May produce inaccurate model if source is not single closed mesh)",
        default=False,
        update=dirtyMatrix)
    verifyExposure = BoolProperty(
        name="Verify Exposure",
        description="Run additional calculations to verify exposure of studs and underside detailing (WARNING: May compromise 'Shell Thickness' functionality if source is not single closed mesh)",
        default=False,
        update=dirtyMatrix)
    useLocalOrient = BoolProperty(
        name="Use Local Orient",
        description="When bricks are deleted, automatically update bricks that become exposed",
        default=False)

    # EXPORT SETTINGS
    exportPath = StringProperty(
        name="Export Path",
        description="Destination path for exported files",
        subtype="FILE_PATH",
        default="//")

    # Source Object Properties
    modelScaleX = FloatProperty(default=-1)
    modelScaleY = FloatProperty(default=-1)
    modelScaleZ = FloatProperty(default=-1)
    objVerts = IntProperty(default=0)
    objPolys = IntProperty(default=0)
    objEdges = IntProperty(default=0)
    isWaterTight = BoolProperty(default=False)


    # Deep Cache of bricksDict
    BFMCache = StringProperty(default="")

    # Blender State for Undo Stack
    blender_undo_state = IntProperty(default=0)

    # Back-End UI Properties
    activeKeyX = IntProperty(default=-1)
    activeKeyY = IntProperty(default=-1)
    activeKeyZ = IntProperty(default=-1)
    firstKey = StringProperty(default="")

    # Internal Model Properties
    modelCreated = BoolProperty(default=False)
    animated = BoolProperty(default=False)
    materialApplied = BoolProperty(default=False)
    armature = BoolProperty(default=False)
    bevelAdded = BoolProperty(default=False)
    customized = BoolProperty(default=True)
    brickSizesUsed = StringProperty(default="")  # list of brickSizes used separated by | (e.g. '5,4,3|7,4,5|8,6,5')
    brickTypesUsed = StringProperty(default="")  # list of brickTypes used separated by | (e.g. 'PLATE|BRICK|STUD')
    modelCreatedOnFrame = IntProperty(default=-1)
    numBricksGenerated = IntProperty(default=-1)
    isSmoke = BoolProperty(default=False)

    # Properties for checking of model needs updating
    animIsDirty = BoolProperty(default=True)
    materialIsDirty = BoolProperty(default=True)
    brickMaterialsAreDirty = BoolProperty(default=True)
    modelIsDirty = BoolProperty(default=True)
    buildIsDirty = BoolProperty(default=True)
    bricksAreDirty = BoolProperty(default=True)
    matrixIsDirty = BoolProperty(default=True)
    internalIsDirty = BoolProperty(default=True)
    lastLogoDetail = StringProperty(default="NONE")
    lastLogoResolution = FloatProperty(default=0)
    lastSplitModel = BoolProperty(default=False)
    lastStartFrame = IntProperty(default=-1)
    lastStopFrame = IntProperty(default=-1)
    lastSourceMid = StringProperty(default="-1,-1,-1")
    lastMaterialType = StringProperty(default="SOURCE")
    lastShellThickness = IntProperty(default=1)
    lastBrickType = StringProperty(default="BRICKS")
    lastMatrixSettings = StringProperty(default="")
    lastBevelWidth = FloatProperty()
    lastBevelSegments = IntProperty()
    lastBevelProfile = IntProperty()
    lastIsSmoke = BoolProperty()

    # Bricker Version of Model
    version = StringProperty(default="1.0.4")
    # Left over attrs from earlier versions
    maxBrickScale1 = IntProperty(default=-1)
    maxBrickScale2 = IntProperty(default=-1)
