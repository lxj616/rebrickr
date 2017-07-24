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
    * Priority 1:
      * Figure out a way to make the brick height more clear to the user
    * Priority 2:
      * Add option for very slightly randomizing rotation/location of bricks.
    * Priority 3:
      * Apply closest LEGO color based on color of nearest vertex
        * Apply unlimited materials or just LEGO material closest to original
      * Prefer overlapping and staggering over stacking of bricks
    * Priority 4:
      * New feature: SNOT (studs not on top) functionality
