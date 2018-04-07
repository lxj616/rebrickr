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

# Addon imports
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
        colors["ABS Plastic Trans-Green"] = [0.114, 0.749, 0.341, 0.4]
        colors["ABS Plastic Trans-Light Blue"] = [0.114, 0.749, 0.341, 0.4]
        colors["ABS Plastic Trans-Light Green"] = [0.949, 0.992, 0.247, 0.4]
        colors["ABS Plastic Trans-Orange"] = [0.949, 0.992, 0.247, 0.4]
        colors["ABS Plastic Trans-Red"] = [0.969, 0.051, 0.106, 0.4]
        colors["ABS Plastic Trans-Reddish Orange"] = [0.992, 0.565, 0.153, 0.4]
        colors["ABS Plastic Trans-Yellow"] = [0.996, 0.945, 0.255, 0.4]
        colors["ABS Plastic Trans-Yellowish Clear"] = [0.949, 0.937, 0.898, 0.2]
        colors["ABS Plastic White"] = [1.0, 0.980, 0.949, 1.0]
        colors["ABS Plastic Yellow"] = [0.996, 0.855, 0.196, 1.0]
        # gamma correct RGB values
        for key in colors:
            colors[key] = gammaCorrect(colors[key], 2)
        getColors.colors = colors
    return getColors.colors


def findNearestBrickColorName(rgba, cm=None):
    cm = cm or getActiveContextInfo()[1]
    return findNearestColorName(rgba, cm, getColors())


def distance(c1, c2, aWt=1):
    r1, g1, b1, a1 = c1
    r2, g2, b2, a2 = c2
    # a1 = c1[3]
    # # r1, g1, b1 = rgb_to_lab(c1[:3])
    # r1, g1, b1 = colorsys.rgb_to_hsv(r1, g1, b1)
    # a2 = c2[3]
    # # r2, g2, b2 = rgb_to_lab(c2[:3])
    # r2, g2, b2 = colorsys.rgb_to_hsv(r1, g1, b1)
    # diff =  0.33 * ((r1 - r2)**2)
    # diff += 0.33 * ((g1 - g2)**2)
    # diff += 0.33 * ((b1 - b2)**2)
    # diff += 1.0 * ((a1 - a2)**2)
    diff =  0.30 * ((r1 - r2)**2)
    diff += 0.59 * ((g1 - g2)**2)
    diff += 0.11 * ((b1 - b2)**2)
    diff += aWt * ((a1 - a2)**2)
    return diff


def findNearestColorName(rgba, cm, colorNames):
    mindiff = None
    for colorName in colorNames:
        diff = distance(rgba, colorNames[colorName], cm.transparentWeight)
        if mindiff is None or diff < mindiff:
            mindiff = diff
            mincolorname = colorName
    return mincolorname
