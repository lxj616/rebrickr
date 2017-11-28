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
      * Add mode for selecting verts at locations next to bricks and adding bricks there
      * Add functionality for changing brick type
      * For animation, if last frame's brickFreqMatrix matches current frame's brickFreqMatrix, save time by just keeping that model around for another frame or duplicating it for the next frame or something
      * Prefer overlapping and staggering over stacking of bricks
      * New feature: SNOT (studs not on top) functionality
      * Add support for texture maps transferring to materials
      * Add support for smoke animations
      * Add support for rigid bodies
      * Write override for 'object.move_to_layer' that moves all frames from animation to another layer
  * Known issues:
      * In snapchat hotdog test file, when parents removed and transformation kept, then when model created then deleted, source shrinks
      * In bricks mode, bricks don't merge well
      * In bricks mode, when adding adj bricks to object and then adding adj bricks to brick above, the adj bricks of the first don't get top exposure updated
