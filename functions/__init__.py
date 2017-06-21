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

# system imports
import bpy
from .crossSection import slices, drawBMesh

def stopWatch(text, value):
    '''From seconds to Days;Hours:Minutes;Seconds'''

    valueD = (((value/365)/24)/60)
    Days = int(valueD)

    valueH = (valueD-Days)*365
    Hours = int(valueH)

    valueM = (valueH - Hours)*24
    Minutes = int(valueM)

    valueS = (valueM - Minutes)*60
    Seconds = int(valueS)

    # valueMs = (valueS - Seconds)*60
    # Miliseconds = int(valueMs)
    #
    print(str(text) + ": " + str(Days) + ";" + str(Hours) + ":" + str(Minutes) + ";" + str(Seconds)) # + ";;" + str(Miliseconds))

def writeBinvox(obj):
    ''' creates binvox file and returns filepath '''

    scn = bpy.context.scene
    binvoxPath = props.binvoxPath
    projectName = bpy.path.display_name_from_filepath(bpy.data.filepath).replace(" ", "_")

    # export obj to obj_exports_folder
    objExportPath = None # TODO: Write this code

    # send
    resolution = props.voxelResolution
    outputFilePath = props.final_output_folder + "/" + projectName + "_" + scn.voxelResolution + ".obj"
    binvoxCall = "'%(binvoxPath)s' -pb -d %(resolution)s '%(objExportPath)s'" % locals()

    subprocess.call()

    return binvoxPath

def groupExists(groupName):
    """ check if group exists in blender's memory """

    groupExists = False
    for group in bpy.data.groups:
        if group.name == groupName:
            groupExists = True
    return groupExists

def deselectAll():
    bpy.ops.object.select_all(action='DESELECT')

def selectOnly(objList, active=None):
    """ selects objs in list and deselects the rest """
    # if single object passed, put it in a list
    if type(objList) != list:
        objList = [objList]
    deselectAll()
    # select objects in list
    for obj in objList:
        obj.select = True
    # set active object
    if active:
        try:
            bpy.context.scene.objects.active = active
        except:
            print("argument passed to 'active' parameter not valid (" + str(active) + ")")
    # return bpy.context.selected_objects
