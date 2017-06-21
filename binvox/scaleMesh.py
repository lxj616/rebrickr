import bpy
import subprocess

inputBasePath = "/media/sf_sharedFiles/"
outputBasePath = "/media/sf_sharedFiles/binvox/scaled_obj_files/"

# set import & export filepaths with user input
print("\nImport OBJ File")
user_input = input("What file would you like to import? => ")
if user_input[-4:] != ".obj":
    user_input = user_input + ".obj"
import_filepath = inputBasePath + user_input
export_filepath = outputBasePath + user_input.replace(".obj", "") + "_scaled.obj"

# import obj file from filepath given by user input
bpy.ops.import_scene.obj(filepath=import_filepath)

# select all objects and set active object
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.context.scene.objects.active = bpy.context.selected_objects[0]

# join all objects (joined object automatically set active)
bpy.ops.object.join()

bpy.ops.transform.resize(value=(1,1,0.833))

bpy.ops.export_scene.obj(filepath=(export_filepath), use_selection=True, use_materials=False)

subprocess.call("killall blender", shell=True)

print("Type 'ctrl c' x2")
