# README

Blender add-on for automated generation of Brick sculptures and simulations from mesh objects (Blender version: 2.78-2.79)

## Rebrickr
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
      * Add many more brick types, including inverted sloped bricks and tiles
      * For animation, if last frame's brickFreqMatrix matches current frame's brickFreqMatrix, save time by just keeping that model around for another frame or duplicating it for the next frame or something
      * Prefer overlapping and staggering over stacking of bricks
      * New feature: SNOT (studs not on top) functionality
      * Add support for texture maps transferring to materials
      * Add support for smoke animations
      * Add support for rigid bodies
      * Write override for 'object.move_to_layer' that moves all frames from animation to another layer
      * Simply calculate brick dimensions, then divide height by three if plate later on. (gets rid of zScale parameter in get_dimensions function)
      * Capitalize "Bricks and Plates", "Plates", "Bricks", "Custom" brickTypes throughout code
  * Known issues:
      * In snapchat hotdog test file, when parents removed and transformation kept, then when model created then deleted, source shrinks
      * In bricks mode, bricks don't merge well
      * In bricks mode, when adding adj bricks to object and then adding adj bricks to brick above, the adj bricks of the first don't get top exposure updated
      * For models with thin outer shells, Rebrickr may use color of inside face instead of outside face for brick material
      * In basketball test file, error occurs when attempting to generate model with materials based on UV map (index out of range)
      * For models created with Rebrickr v1.0, when opened in v1.1.1 and not-split model is selected and deleted with the 'x' key, model is not deleted
      * When customization applied to model, if model settings clicked on but not updated, 'Revert Settings' warning does not appear.
      * "Bricks and Plates" and "Custom" brickTypes have many bugs; requires testing
