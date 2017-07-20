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
  * Known Bugs:
    * long, thin plane models don't turn out correctly (inside/outsideness seems to be broken)
    * 'UP' and 'DOWN' arrows in UI don't move models, they just change the 'cmlist_index'
  * Future improvements:
    * Priority 1:
      * None!
      * Fix 'UP' and 'DOWN' arrows in UI so they move cmlist items instead of changing 'cmlist_index'
    * Priority 2:
      * Apply closest LEGO color based on color of nearest vertex
      * Improve logo resolution (currently uses decimate)
    * Priority 3:
      * New feature: frame-by-frame generation of LEGO models (like the explosions in the LEGO Movie)
      * Allow for custom object to generate model from
