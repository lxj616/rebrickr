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

def getLegalBrickSizes():
    """ returns a list of legal brick sizes """

    legalBrickSizes = {
        # tiles
        0.9:[[1, 1],
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
        # plates
        1:  [[1, 1],
             [1, 2],
             [1, 3],
             [1, 4],
             [1, 6],
             [1, 8],
             [1, 10],
             [1, 12],
             [2, 1],
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
        # bricks
        3:  [[1, 1],
             [1, 2],
             [1, 3],
             [1, 4],
             [1, 6],
             [1, 8],
             [1, 10],
             [1, 12],
             [1, 14],
             [1, 16],
             [2, 1],
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
             [12, 24]]}

    # add reverses of brick sizes
    for heightKey in legalBrickSizes:
        sizes = legalBrickSizes[heightKey]
        for size in sizes:
            if size[::-1] not in sizes:
                sizes.append(size[::-1])

    # return resulting list of legal brick sizes
    return legalBrickSizes