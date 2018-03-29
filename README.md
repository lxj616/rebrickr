# README

Blender add-on for automated generation of Brick sculptures and simulations from mesh objects (Blender version: 2.79)

## Bricker
  * Features:
      * Convert any 3D Mesh into a photo-real 3D brick model
      * Generate animated brick models from keyframed animation, simulations (soft body physics, fluid, cloth, etc), armature, and much more
      * Adjust model settings after it's been created
      * Customize the model after it's been auto-generated using handy tools like split bricks, merge bricks, add adjacent bricks, change brick type, and more!
  * Instructions:
      * Create a new model with the 'New Model' button, and name it whatever you'd like
      * Select a source object with the 'Source Object' eyedropper (defaults to active object when model was created)
      * Click 'Brickify Object'
      * Adjust model settings for your desired result
      * Click 'Update Model' to view setting adjustments
      * Once you're satisfied with the settings, make adjustments to your model in the 'Customize Model' dropdown menu
  * Future improvements:
      * Add mode for selecting verts at locations next to bricks and adding bricks there
      * For animation, if last frame's brickFreqMatrix matches current frame's brickFreqMatrix, save time by just keeping that model around for another frame or duplicating it for the next frame or something
      * New feature: SNOT (studs not on top) functionality
      * Add support for smoke animations
      * Add support for rigid bodies
      * Write override for 'object.move_to_layer' that moves all frames from animation to another layer
      * Simply calculate brick dimensions, then divide height by three if plate later on. (gets rid of zScale parameter in get_dimensions function)
      * Add 'exclusion' functionality so that one model doesn’t create bricks where another model already did
      * Add many more brick types, including inverted sloped bricks and tiles
      * Generate model with bricks and slopes to more closely approximate original mesh
      * Add merge option that creates either biggest bricks possible or randomly sampled like normal.
  * Known issues:
      * For models with thin outer shells, Bricker may use color of inside face instead of outside face for brick material
      * When drawing adjacent bricks, exposure is incorrect when obstructed by ignored brick types
      * Applying model rotation when deleting brickified model with source's origin not in mesh center doesn't work reliably
      * Updating brick animation results in error
