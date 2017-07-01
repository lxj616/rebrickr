# README

Blender add-on for automated generation of LEGO Bricks from object (Blender version: 2.78b)

## LEGOizer
  * Features:
      * Adjust LEGO brick settings before committing model
  * Instructions:
      * Select an object with 'Source Object' UI box (defaults to active object if blank or if object doesn't exist)
      * Click 'LEGOize Object'
      * Adjust settings for your desired result
      * Click 'Update Model' to view setting adjustments
      * Click 'Commit Model' once the settings are correct to apply setting adjustments so that you can create more LEGOized models!
  * Future improvements:
    * Priority 1:
      * Improve logo resolution (currently uses decimate)
      * Don't import LEGO text every time (currently imports and decimates with every resolution adjustment)
      * Add functionality to 'Merge Bricks' button
      * Add functionality for only rendering LEGO text on exposed studs
      * Add functionality to Pre Hollow/Shell Thickness
      * Fix functionality for generating LEGO bricks on shell of source object
    * Priority 2:
      * Apply closest LEGO color based on color of nearest vertex
    * Priority 3:
      * New feature: frame-by-frame generation of LEGO models (like the explosions in the LEGO Movie)
      * Allow for custom object to generate model from
