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
from operator import itemgetter

# Blender imports
import bpy
from bpy.props import *
from bpy.types import Panel, UIList
props = bpy.props

# Bricker imports
from ..functions import *
from ..buttons.bevel import *


def uniquifyName(self, context):
    """ if Brick Model exists with name, add '.###' to the end """
    scn, cm, _ = getActiveContextInfo()
    name = cm.name
    while scn.cmlist.keys().count(name) > 1:
        if name[-4] == ".":
            try:
                num = int(name[-3:])+1
            except ValueError:
                num = 1
            name = name[:-3] + "%03d" % (num)
        else:
            name = name + ".001"
    if cm.name != name:
        cm.name = name


def setNameIfEmpty(self, context):
    scn = context.scene
    last_cmlist_index = scn.cmlist_index
    cm0 = scn.cmlist[last_cmlist_index]
    # verify model doesn't exist with that name
    if cm0.source_name != "":
        for i, cm1 in enumerate(scn.cmlist):
            if cm1 != cm0 and cm1.source_name == cm0.source_name:
                cm0.source_name = ""
                scn.cmlist_index = i


def updateBevel(self, context):
    # get bricks to bevel
    try:
        scn, cm, n = getActiveContextInfo()
        cm = scn.cmlist[scn.cmlist_index]
        n = cm.source_name
        if cm.lastBevelWidth != cm.bevelWidth or cm.lastBevelSegments != cm.bevelSegments or cm.lastBevelProfile != cm.bevelProfile:
            bricks = getBricks()
            BrickerBevel.createBevelMods(bricks)
            cm.lastBevelWidth = cm.bevelWidth
            cm.lastBevelSegments = cm.bevelSegments
            cm.lastBevelProfile = cm.bevelProfile
    except Exception as e:
        print("[Bricker]", e)
        pass


def updateStartAndStopFrames(self, context):
    scn, cm, _ = getActiveContextInfo()
    if cm.useAnimation:
        cm.startFrame = scn.frame_start
        cm.stopFrame = scn.frame_end


def updateParentExposure(self, context):
    scn, cm, _ = getActiveContextInfo()
    if not (cm.modelCreated or cm.animated):
        return
    if cm.exposeParent:
        parentOb = bpy.data.objects.get(cm.parent_name)
        if parentOb:
            safeLink(parentOb, unhide=True, protect=True)
            select(parentOb, active=parentOb, only=True)
    else:
        parentOb = bpy.data.objects.get(cm.parent_name)
        if parentOb:
            safeUnlink(parentOb)


def updateModelScale(self, context):
    scn, cm, _ = getActiveContextInfo()
    if not (cm.modelCreated or cm.animated):
        return
    _, _, s = getTransformData(cm)
    parentOb = bpy.data.objects.get(cm.parent_name)
    if parentOb:
        parentOb.scale = Vector(s) * cm.transformScale


def dirtyAnim(self, context):
    scn, cm, _ = getActiveContextInfo()
    cm.animIsDirty = True


def dirtyMaterial(self, context):
    scn, cm, _ = getActiveContextInfo()
    cm.materialIsDirty = True


def dirtyModel(self, context):
    scn, cm, _ = getActiveContextInfo()
    cm.modelIsDirty = True


def dirtyMatrix(self=None, context=None):
    scn, cm, _ = getActiveContextInfo()
    cm.matrixIsDirty = True


def dirtyInternal(self, context):
    scn, cm, _ = getActiveContextInfo()
    cm.internalIsDirty = True


def dirtyBuild(self, context):
    scn, cm, _ = getActiveContextInfo()
    cm.buildIsDirty = True


def dirtyBricks(self, context):
    scn, cm, _ = getActiveContextInfo()
    cm.bricksAreDirty = True


def matchProperties(cmTo, cmFrom, bh=False):
    # list properties to match
    cm_attrs = ["shellThickness",
                "studDetail",
                "logoDetail",
                "logoResolution",
                "logoObjectName",
                "logoScale",
                "logoInset",
                "hiddenUndersideDetail",
                "exposedUndersideDetail",
                "circleVerts",
                "gap",
                "mergeSeed",
                "randomLoc",
                "randomRot",
                "brickType",
                "alignBricks",
                "offsetBrickLayers",
                "distOffsetX",
                "distOffsetY",
                "distOffsetZ",
                "customObjectName",
                "maxWidth",
                "maxDepth",
                "splitModel",
                "internalSupports",
                "matShellDepth",
                "latticeStep",
                "alternateXY",
                "colThickness",
                "colStep",
                "materialType",
                "materialName",
                "internalMatName",
                "matShellDepth",
                "mergeInconsistentMats",
                "randomMatSeed",
                "useUVMap",
                "useNormals",
                "verifyExposure",
                "insidenessRayCastDir",
                "castDoubleCheckRays",
                "startFrame",
                "stopFrame",
                "useAnimation",
                "autoUpdateExposed",
                "brickShell",
                "calculationAxes",
                "useLocalOrient"]
    # more properties to match if condition is true
    if bh:
        cm_attrs.append("brickHeight")
    if cmFrom.bevelAdded and cmTo.bevelAdded:
        cm_attrs.append("bevelWidth")
        cm_attrs.append("bevelSegments")
        cm_attrs.append("bevelProfile")
    # match properties from 'cmFrom' to 'cmTo'
    for attr in cm_attrs:
        oldVal = getattr(cmFrom, attr)
        setattr(cmTo, attr, oldVal)
