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

def getColors():
    colors = {}
    colors["LEGO Plastic Black"] =
    colors["LEGO Plastic Bright Green"] =
    colors["LEGO Plastic Brown"] =
    colors["LEGO Plastic Dark Azur"] =
    colors["LEGO Plastic Dark Green"] =
    colors["LEGO Plastic Dark Grey"] =
    colors["LEGO Plastic Dark Red"] =
    colors["LEGO Plastic Gold"] =
    colors["LEGO Plastic Green"] =
    colors["LEGO Plastic Light Grey"] =
    colors["LEGO Plastic Lime"] =
    colors["LEGO Plastic Orange"] =
    colors["LEGO Plastic Pink"] =
    colors["LEGO Plastic Purple"] =
    colors["LEGO Plastic Red"] =
    colors["LEGO Plastic Tan"] =
    colors["LEGO Plastic Trans-Blue"] =
    colors["LEGO Plastic Trans-Clear"] =
    colors["LEGO Plastic Trans-Light Green"] =
    colors["LEGO Plastic Trans-Red"] =
    colors["LEGO Plastic Trans-Yellow"] =
    colors["LEGO Plastic White"] =
    colors["LEGO Plastic Yellow"] =



    return colors

def rgbFromStr(s):
    # s starts with a #.
    r, g, b = int(s[1:3],16), int(s[3:5], 16),int(s[5:7], 16)
    return r, g, b

def findNearestWebColorName((R,G,B)):
    return ColorNames.findNearestColorName((R,G,B),ColorNames.WebColorMap)

def findNearestImageMagickColorName((R,G,B)):
    return ColorNames.findNearestColorName((R,G,B),ColorNames.ImageMagickColorMap)

def findNearestColorName((R,G,B),Map):
    mindiff = None
    for d in Map:
        r, g, b = ColorNames.rgbFromStr(Map[d])
        diff = abs(R -r)*256 + abs(G-g)* 256 + abs(B- b)* 256
        if mindiff is None or diff < mindiff:
            mindiff = diff
            mincolorname = d
    return mincolorname

def getMaterial(polygon):
    materialD = {}
    obj.data.materials[0].alpha = 1
    print("face", polygon.index, "material_index", polygon.material_index)
    slot = obj.material_slots[polygon.material_index]
    mat = slot.material
    if mat is not None:
        materialD["RGB"] = mat.diffuse_color
        materialD["Alpha"] = mat.alpha
        return materialD
    else:
        return None

# ALTERNATE METHOD BELOW:
def distance(c1, c2):
    (r1,g1,b1) = c1
    (r2,g2,b2) = c2
    return math.sqrt((r1 - r2)**2 + (g1 - g2) ** 2 + (b1 - b2) **2)

colorsDict = getColors()
colors = list(colorsDict.keys())
closest_colors = sorted(colors, key=lambda color: distance(color, point))
closest_color = closest_colors[0]
code = colorsDict[closest_color]
