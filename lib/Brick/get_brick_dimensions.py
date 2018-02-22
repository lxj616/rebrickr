
def get_brick_dimensions(height=1, zScale=1, gap_percentage=0.01):
    """
    returns the dimensions of a brick in Blender units

    Keyword Arguments:
    height         -- height of a standard brick in Blender units
    zScale         -- height of the brick in plates (1: standard plate, 3: standard brick)
    gap_percentage -- gap between bricks relative to brick height
    """
    scale = height/9.6
    brick_dimensions = {}
    brick_dimensions["height"] = scale*9.6*(zScale/3)
    brick_dimensions["width"] = scale*8
    brick_dimensions["gap"] = scale*9.6*gap_percentage
    brick_dimensions["stud_height"] = scale*1.8
    brick_dimensions["stud_radius"] = scale*2.4
    brick_dimensions["stud_offset"] = (brick_dimensions["height"] / 2) + (brick_dimensions["stud_height"] / 2)
    brick_dimensions["thickness"] = scale*1.6
    brick_dimensions["tube_thickness"] = scale*0.855
    brick_dimensions["bar_radius"] = scale*1.6
    brick_dimensions["logo_width"] = scale*3.74
    brick_dimensions["support_width"] = scale*0.8
    brick_dimensions["tick_width"] = scale*0.6
    brick_dimensions["tick_depth"] = scale*0.3
    brick_dimensions["support_height"] = brick_dimensions["height"]*0.65

    brick_dimensions["logo_offset"] = (brick_dimensions["height"] / 2) + (brick_dimensions["stud_height"])
    return brick_dimensions
