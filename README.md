# README

Blender add-on for automated generation of LEGO Bricks from mesh objects (Blender version: 2.78c)

## LEGOizer
  * Features:
      * Create LEGO models out of any 3D model in Blender
      * Adjust LEGO brick settings after it's created
  * Instructions:
      * Create a new model with the 'New Model' button, and name it whatever you'd like
      * Select a source object with the 'Source Object' dropdown (defaults to active object when model was created)
      * Click 'LEGOize Object'
      * Adjust settings for your desired result
      * Click 'Update Model' to view setting adjustments
  * Future improvements:
      * For animation, if last frame's brickFreqMatrix matches current frame's brickFreqMatrix, save time by just keeping that model around for another frame or duplicating it for the next frame or something
      * Prefer overlapping and staggering over stacking of bricks
      * New feature: SNOT (studs not on top) functionality
      * Add support for texture maps transferring to materials
      * Add support for smoke animations
