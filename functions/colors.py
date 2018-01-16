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
import numpy as np
import colorsys

# Rebrickr imports
from .general import *


def getColors():
    if not hasattr(getColors, 'colors'):
        colors = {}
        colors["ABS Plastic Black"] = [0.0, 0.008, 0.012, 1.0]
        colors["ABS Plastic Blue"] = [0.033, 0.098, 0.402, 1.0]
        colors["ABS Plastic Bright Green"] = [0.118, 0.576, 0.255, 1.0]
        colors["ABS Plastic Bright Light Orange"] = [0.984, 0.741, 0.173, 1.0]
        colors["ABS Plastic Brown"] = [0.478, 0.275, 0.149, 1.0]
        colors["ABS Plastic Dark Azur"] = [0.302, 0.608, 0.792, 1.0]
        colors["ABS Plastic Dark Brown"] = [0.318, 0.192, 0.114, 1.0]
        colors["ABS Plastic Dark Green"] = [0.012, 0.216, 0.129, 1.0]
        colors["ABS Plastic Dark Grey"] = [0.310, 0.349, 0.337, 1.0]
        colors["ABS Plastic Dark Red"] = [0.490, 0.098, 0.106, 1.0]
        colors["ABS Plastic Dark Tan"] = [0.467, 0.412, 0.267, 1.0]
        colors["ABS Plastic Gold"] = [0.718, 0.522, 0.129, 1.0]
        colors["ABS Plastic Green"] = [0.055, 0.463, 0.231, 1.0]
        colors["ABS Plastic Light Grey"] = [0.541, 0.537, 0.537, 1.0]
        colors["ABS Plastic Lime"] = [0.612, 0.745, 0.180, 1.0]
        colors["ABS Plastic Orange"] = [0.992, 0.447, 0.133, 1.0]
        colors["ABS Plastic Pink"] = [0.929, 0.329, 0.525, 1.0]
        colors["ABS Plastic Purple"] = [0.529, 0.173, 0.416, 1.0]
        colors["ABS Plastic Red"] = [0.753, 0.039, 0.106, 1.0]
        colors["ABS Plastic Sand Blue"] = [0.361, 0.416, 0.471, 1.0]
        colors["ABS Plastic Sand Green"] = [0.420, 0.573, 0.435, 1.0]
        colors["ABS Plastic Silver"] = [0.682, 0.682, 0.682, 1.0]
        colors["ABS Plastic Tan"] = [0.761, 0.667, 0.478, 1.0]
        colors["ABS Plastic Trans-Blue"] = [0.114, 0.686, 0.871, 0.4]
        colors["ABS Plastic Trans-Clear"] = [0.5, 0.5, 0.5, 0.1]
        colors["ABS Plastic Trans-Green"] = [0.114, 0.749, 0.341, 0.25]
        colors["ABS Plastic Trans-Light Blue"] = [0.114, 0.749, 0.341, 0.4]
        colors["ABS Plastic Trans-Light Green"] = [0.949, 0.992, 0.247, 0.4]
        colors["ABS Plastic Trans-Orange"] = [0.949, 0.992, 0.247, 0.4]
        colors["ABS Plastic Trans-Red"] = [0.969, 0.051, 0.106, 0.4]
        colors["ABS Plastic Trans-Reddish Orange"] = [0.992, 0.565, 0.153, 0.4]
        colors["ABS Plastic Trans-Yellow"] = [0.996, 0.945, 0.255, 0.4]
        colors["ABS Plastic Trans-Yellowish Clear"] = [0.949, 0.937, 0.898, 0.325]
        colors["ABS Plastic White"] = [1.0, 0.980, 0.949, 1.0]
        colors["ABS Plastic Yellow"] = [0.996, 0.855, 0.196, 1.0]
        # gamma correct RGB values
        for key in colors:
            colors[key] = gammaCorrect(colors[key], 2)
        getColors.colors = colors
    return getColors.colors


def rgbFromStr(s):
    # s starts with a #.
    r, g, b = int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16)
    return r, g, b


# def findNearestWebColorName((R, G, B)):
#     return ColorNames.findNearestColorName((R, G, B), ColorNames.WebColorMap)
#
#
# def findNearestImageMagickColorName((R, G, B)):
#     return ColorNames.findNearestColorName((R, G, B), ColorNames.ImageMagickColorMap)
#
#
def findNearestBrickColorName(rgba):
    return findNearestColorName(rgba, getColors())

def rgb_to_lab(rgb):
    def func(t):
        if (t > 0.008856):
            return np.power(t, 1/3.0);
        else:
            return 7.787 * t + 16 / 116.0;

    #Conversion Matrix
    matrix = [[0.412453, 0.357580, 0.180423],
              [0.212671, 0.715160, 0.072169],
              [0.019334, 0.119193, 0.950227]]

    # RGB values lie between 0 to 1.0
    rgb = [1.0, 0, 0] # RGB

    cie = np.dot(matrix, rgb);

    cie[0] = cie[0] /0.950456;
    cie[2] = cie[2] /1.088754;

    # Calculate the L
    L = 116 * np.power(cie[1], 1/3.0) - 16.0 if cie[1] > 0.008856 else 903.3 * cie[1];

    # Calculate the a
    a = 500*(func(cie[0]) - func(cie[1]));

    # Calculate the b
    b = 200*(func(cie[1]) - func(cie[2]));

    #  Values lie between -128 < b <= 127, -128 < a <= 127, 0 <= L <= 100
    lab = [b , a, L];
    return lab


def distance(c1, c2):
    r1, g1, b1, a1 = c1
    r2, g2, b2, a2 = c2
    # a1 = c1[3]
    # # r1, g1, b1 = rgb_to_lab(c1[:3])
    # r1, g1, b1 = colorsys.rgb_to_hsv(r1, g1, b1)
    # a2 = c2[3]
    # # r2, g2, b2 = rgb_to_lab(c2[:3])
    # r2, g2, b2 = colorsys.rgb_to_hsv(r1, g1, b1)
    diff =  0.30 * ((r1 - r2)**2)
    diff += 0.59 * ((g1 - g2)**2)
    diff += 0.11 * ((b1 - b2)**2)
    diff += 1.00 * ((a1 - a2)**2)
    return diff


def findNearestColorName(rgba, colorNames):
    mindiff = None
    for colorName in colorNames:
        diff = distance(rgba, colorNames[colorName])
        if mindiff is None or diff < mindiff:
            mindiff = diff
            mincolorname = colorName
    return mincolorname


def getMat(polygon, matType):
    materialD = {}
    obj.data.materials[0].alpha = 1
    slot = obj.material_slots[polygon.material_index]
    mat = slot.material

    if mat:
        if matType == "DIFFUSE_BSDF":
            materialD["RGB"] = mat.node_tree.nodes.find('Diffuse BSDF')
        elif matType == "DIFFUSE":
            materialD["RGB"] = mat.diffuse_color
            materialD["Alpha"] = mat.alpha
        return materialD
    else:
        return None
