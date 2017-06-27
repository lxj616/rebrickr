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
import random
import sys
import time
import os
import traceback
from math import *
props = bpy.props

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

def groupExists(groupName):
    """ check if group exists in blender's memory """

    groupExists = False
    for group in bpy.data.groups:
        if group.name == groupName:
            groupExists = True
    return groupExists

def insertKeyframes(objList, keyframeType, frame):
    """ insert key frames for given objects to given frames """
    if type(objList) == list:
        for obj in objList:
            obj.keyframe_insert(data_path=keyframeType, frame=frame)
    else: # assume objList is single object
        objList.keyframe_insert(data_path=keyframeType, frame=frame)

def deselectAll():
    bpy.ops.object.select_all(action='DESELECT')
def selectAll():
    bpy.ops.object.select_all(action='SELECT')

def confirmList(objList):
    """ if single object passed, convert to list """
    if type(objList) != list:
        objList = [objList]
    return objList

def hide(objList):
    objList = confirmList(objList)
    for obj in objList:
        obj.hide = True
def unhide(objList):
    objList = confirmList(objList)
    for obj in objList:
        obj.hide = False

def select(objList=[], active=None, action="select", exclusive=True):
    """ selects objs in list and deselects the rest """
    objList = confirmList(objList)
    try:
        if action == "select":
            # deselect all if selection is exclusive
            if exclusive and len(objList) > 0:
                deselectAll()
            # select objects in list
            for obj in objList:
                obj.select = True
        elif action == "deselect":
            # deselect objects in list
            for obj in objList:
                obj.select = False

        # set active object
        if active:
            try:
                bpy.context.scene.objects.active = active
            except:
                print("argument passed to 'active' parameter not valid (" + str(active) + ")")
    except:
        return False
    return True

def delete(objList):
    objList = confirmList(objList)
    if select(objList):
        unhide(objList)
        bpy.ops.object.delete()

def changeContext(context, areaType):
    """ Changes current context and returns previous area type """
    lastAreaType = context.area.type
    context.area.type = areaType
    return lastAreaType

def getLibraryPath():
    """ returns full path to module directory """
    functionsPath = os.path.dirname(os.path.abspath(__file__))
    libraryPath = functionsPath[:-10]
    if not os.path.exists(libraryPath):
        raise NameError("Did not find addon from path {}".format(libraryPath))
    return libraryPath

def bversion():
    bversion = '%03d.%03d.%03d' % (bpy.app.version[0],bpy.app.version[1],bpy.app.version[2])
    return bversion

def showErrorMessage(message, wrap=80):
    if not message: return
    lines = message.splitlines()
    if wrap > 0:
        nlines = []
        for line in lines:
            spc = len(line) - len(line.lstrip())
            while len(line) > wrap:
                i = line.rfind(' ',0,wrap)
                if i == -1:
                    nlines += [line[:wrap]]
                    line = line[wrap:]
                else:
                    nlines += [line[:i]]
                    line = line[i+1:]
                if line:
                    line = ' '*spc + line
            nlines += [line]
        lines = nlines
    def draw(self,context):
        for line in lines:
            self.layout.label(line)
    bpy.context.window_manager.popup_menu(draw, title="Error Message", icon="ERROR")
    return

# http://stackoverflow.com/questions/14519177/python-exception-handling-line-number
def print_exception():
    exc_type, exc_obj, tb = sys.exc_info()

    errormsg = 'EXCEPTION (%s): %s\n' % (exc_type, exc_obj)
    etb = traceback.extract_tb(tb)
    pfilename = None
    for i,entry in enumerate(reversed(etb)):
        filename,lineno,funcname,line = entry
        if filename != pfilename:
            pfilename = filename
            errormsg += '         %s\n' % (filename)
        errormsg += '%03d %04d:%s() %s\n' % (i, lineno, funcname, line.strip())

    print(errormsg)

    if 'AssemblMe_log' not in bpy.data.texts:
        # create a log file for error writing
        bpy.ops.text.new()
        bpy.data.texts[-1].name = 'AssemblMe_log'

    # write error to log text object
    bpy.data.texts['AssemblMe_log'].write(errormsg + '\n')

    #showErrorMessage(errormsg, wrap=240)

    return errormsg
