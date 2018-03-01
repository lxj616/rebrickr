'''
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
'''

def addKeymaps(km):
    kmi = km.keymap_items.new("bricker.brickify", 'L', 'PRESS', alt=True, shift=True)
    kmi = km.keymap_items.new("bricker.delete", 'D', 'PRESS', alt=True, shift=True)
    kmi = km.keymap_items.new("bricker.draw_adjacent", 'EQUAL', 'PRESS', shift=True, alt=True)
    kmi = km.keymap_items.new("bricker.split_bricks", 'S', 'PRESS', shift=True, alt=True)
    kmi = km.keymap_items.new("bricker.merge_bricks", 'M', 'PRESS', shift=True, alt=True)
    kmi = km.keymap_items.new("bricker.set_exposure", 'UP_ARROW', 'PRESS', shift=True, alt=True).properties.side = "TOP"
    kmi = km.keymap_items.new("bricker.set_exposure", 'DOWN_ARROW', 'PRESS', shift=True, alt=True).properties.side = "BOTTOM"
    kmi = km.keymap_items.new("bricker.customize_model", 'I', 'PRESS', shift=True)
