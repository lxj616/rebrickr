# README

Blender add-on for automated generation of Brick sculptures and simulations from mesh objects (Blender version: 2.78-2.79)

## Rebrickr
  * Features:
      * Create Brick Models out of any 3D model in Blender
      * Adjust Brick settings after it's created
  * Instructions:
      * Create a new model with the 'New Model' button, and name it whatever you'd like
      * Select a source object with the 'Source Object' dropdown (defaults to active object when model was created)
      * Click 'Brickify Object'
      * Adjust settings for your desired result
      * Click 'Update Model' to view setting adjustments
  * Future improvements:
      * Priority 1:
          * Add UI panel drawn inside Blender like Retopoflow for adding/adjusting/maneuvering bricks
          * EITHER  Add UI for selecting verts at inside/outside locations and adding bricks there
          * OR      Add button for recalculating new shell
          * Add functionality for "add brick above/below/right/left/front/back" current selected brick
          * Add functionality for changing brick type
          * Don't recalculate matrix when shell depth adjusted
          * Try to reduce need to recalculate matrix (maybe keep around lastBrickHeight, lastGap, etc. so it only updates if changed, not just clicked)
      * Priority 2:
          * For animation, if last frame's brickFreqMatrix matches current frame's brickFreqMatrix, save time by just keeping that model around for another frame or duplicating it for the next frame or something
          * Prefer overlapping and staggering over stacking of bricks
          * New feature: SNOT (studs not on top) functionality
          * Add support for texture maps transferring to materials
          * Add support for smoke animations
          * Add support for rigid bodies
          * Test "Bricks and Plates" functionality for bugs
          * Write override for 'object.move_to_layer' that moves all frames from animation to another layer
  * Known bugs:
      * When source is dirty (mesh edited to change location of center of mass) for split Brick Model, model shifts to new center of mass after applied a second time.
