# README

Blender add-on for automated generation of LEGO Bricks from object (Blender version: 2.78c)

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
    * Priority 1:
      * Improve bevel so that number of verts doesn't affect it
    * Priority 2:
      * Apply closest LEGO color based on color of nearest vertex
      * Improve logo resolution (currently uses decimate)
    * Priority 3:
      * New feature: frame-by-frame generation of LEGO models (like the explosions in the LEGO Movie)
      * Allow for custom object to generate model from
