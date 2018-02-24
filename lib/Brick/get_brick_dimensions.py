
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
    brick_dimensions["height"] = round(scale*9.6*(zScale/3), 8)
    brick_dimensions["width"] = round(scale*8, 8)
    brick_dimensions["gap"] = round(scale*9.6*gap_percentage, 8)
    brick_dimensions["stud_height"] = round(scale*1.8, 8)
    brick_dimensions["stud_radius"] = round(scale*2.4, 8)
    brick_dimensions["stud_offset"] = round((brick_dimensions["height"] / 2) + (brick_dimensions["stud_height"] / 2), 8)
    brick_dimensions["stud_offset_triple"] = round(((brick_dimensions["height"]*3) / 2) + (brick_dimensions["stud_height"] / 2), 8)
    brick_dimensions["thickness"] = round(scale*1.6, 8)
    brick_dimensions["tube_thickness"] = round(scale*0.855, 8)
    brick_dimensions["bar_radius"] = round(scale*1.6, 8)
    brick_dimensions["logo_width"] = round(scale*4.8, 8) # originally round(scale*3.74, 8)
    brick_dimensions["support_width"] = round(scale*0.8, 8)
    brick_dimensions["tick_width"] = round(scale*0.6, 8)
    brick_dimensions["tick_depth"] = round(scale*0.3, 8)
    brick_dimensions["support_height"] = round(brick_dimensions["height"]*0.65, 8)
    brick_dimensions["support_height_triple"] = round((brick_dimensions["height"]*3)*0.65, 8)

    brick_dimensions["logo_offset"] = round((brick_dimensions["height"] / 2) + (brick_dimensions["stud_height"]), 8)
    return brick_dimensions
