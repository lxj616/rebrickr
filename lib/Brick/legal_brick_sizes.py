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

import bpy

from ...functions.common import *

def getLegalBrickSizes():
    """ returns a list of legal brick sizes """

    legalBrickSizes = {
        1:{ "PLATE":[[1, 1],
                     [1, 2],
                     [1, 3],
                     [1, 4],
                     [1, 6],
                     [1, 8],
                     [1, 10],
                     [1, 12],
                     [2, 2],
                     [2, 3],
                     [2, 4],
                     [2, 6],
                     [2, 8],
                     [2, 10],
                     [2, 12],
                     [2, 14],
                     [2, 16],
                     [3, 3],
                     [4, 4],
                     [4, 6],
                     [4, 8],
                     [4, 10],
                     [4, 12],
                     [6, 6],
                     [6, 8],
                     [6, 10],
                     [6, 12],
                     [6, 14],
                     [6, 16],
                     [6, 24],
                     [8, 8],
                     [8, 11],
                     [8, 16],
                     [16, 16]],
            "TILE":[[1, 1],
                    [1, 2],
                    [1, 3],
                    [1, 4],
                    [1, 6],
                    [1, 8],
                    [2, 2],
                    [2, 4],
                    [3, 6],
                    [6, 6],
                    [8, 16]],
            "STUD":[[1, 1]],
            "STUD_HOLLOW":[[1, 1]],
            # "WING":[[2, 3],
            #         [2, 4],
            #         [3, 6],
            #         [3, 8],
            #         [3, 12],
            #         [4, 4],
            #         [6, 12],
            #         [7, 12]],
            # "ROUNDED_TILE":[[1, 1]],
            # "SHORT_SLOPE":[[1, 1],
            #             [1, 2]],
            "TILE_GRILL":[[1, 2]],
            # "TILE_ROUNDED":[[2, 2]],
            # "PLATE_ROUNDED":[[2, 2]],
            },
        3:{ "BRICK":[[1, 1],
                     [1, 2],
                     [1, 3],
                     [1, 4],
                     [1, 6],
                     [1, 8],
                     [1, 10],
                     [1, 12],
                     [1, 14],
                     [1, 16],
                     [2, 2],
                     [2, 3],
                     [2, 4],
                     [2, 6],
                     [2, 8],
                     [2, 10],
                     [4, 4],
                     [4, 6],
                     [4, 8],
                     [4, 10],
                     [4, 12],
                     [4, 18],
                     [8, 8],
                     [8, 16],
                     [10, 20],
                     [12, 24]],
            "SLOPE":[[1, 1],
                     [1, 2],
                     [1, 3],
                     [1, 4],
                     [2, 2],
                     [2, 3],
                     [2, 4],
                     [2, 6],
                     [4, 3]], # TODO: Add 6x3 option with studs missing between outer two (needs to be coded into slope.py generator)
            # "SLOPE_INVERTED":[[1, 2],
            #                   [1, 3],
            #                   [2, 2],
            #                   [2, 3]],
            "CYLINDER":[[1, 1]],
            "CONE":[[1, 1]],
            # "BRICK_STUD_ON_ONE_SIDE":[[1, 1]],
            # "BRICK_INSET_STUD_ON_ONE_SIDE":[[1, 1]],
            # "BRICK_STUD_ON_TWO_SIDES":[[1, 1]],
            # "BRICK_STUD_ON_ALL_SIDES":[[1, 1]],
            # "TILE_WITH_HANDLE":[[1, 2]],
            # "BRICK_PATTERN":[[1, 2]],
            # "DOME":[[2, 2]],
            # "DOME_INVERTED":[[2, 2]],
          },
        # 9:{
        #     "TALL_SLOPE":[[1, 2], [2, 2]]
        #     "TALL_SLOPE_INVERTED":[[1, 2]]
        #     "TALL_BRICK":[[2, 2]]
        # }
        # 15:{
        #     "TALL_BRICK":[[1, 2]]
        # }
        }
    # add reverses of brick sizes
    for heightKey,types in legalBrickSizes.items():
        for typ,sizes in types.items():
            reverseSizes = [size[::-1] for size in sizes]
            legalBrickSizes[heightKey][typ] = uniquify2(reverseSizes + sizes)

    return legalBrickSizes


def getBrickTypes(height):
    return bpy.props.Bricker_legal_brick_sizes[height].keys()


def getTypesObscuringAbove():
    return ["BRICK", "PLATE", "TILE", "STUD", "SLOPE_INVERTED"]


def getTypesObscuringBelow():
    return ["BRICK", "PLATE", "TILE", "STUD", "SLOPE"]
