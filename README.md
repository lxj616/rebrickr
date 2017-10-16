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
      * For animation, if last frame's brickFreqMatrix matches current frame's brickFreqMatrix, save time by just keeping that model around for another frame or duplicating it for the next frame or something
      * Prefer overlapping and staggering over stacking of bricks
      * New feature: SNOT (studs not on top) functionality
      * Add support for texture maps transferring to materials
      * Add support for smoke animations
      * Add support for rigid bodies
      * Add "Bricks and Plates" option for merging stacked plates into bricks where possible
      * Write override for 'object.move_to_layer' that moves all frames from animation to another layer
  * Known bugs:
      * When source is dirty (mesh edited to change location of center of mass) for split Brick Model, model shifts to new center of mass after applied a second time.
