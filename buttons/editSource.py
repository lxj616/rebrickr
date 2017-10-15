"""
    Copyright (C) 2017 Bricks Brought to Life
    http://bblanimation.com/
    chris@bblanimation.com
    Created by Christopher Gearhart
        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.
        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.
        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <http://www.gnu.org/licenses/>.
    """

# System imports
import time

# Blender imports
import bpy
from mathutils import Vector, Euler
props = bpy.props

# Rebrickr imports
from ..functions import *


class RebrickrEditSource(bpy.types.Operator):
    """ Edit Source Object Mesh """                                             # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "rebrickr.edit_source"                                             # unique identifier for buttons and menu items to reference.
    bl_label = "Edit Source Object Mesh"                                        # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns false) """
        scn = context.scene
        if scn.cmlist_index == -1:
            return False
        cm = scn.cmlist[scn.cmlist_index]
        if not cm.modelCreated:
            return False
        if scn.name == "Rebrickr_storage (DO NOT RENAME)":
            return False
        return True

    def modal(self, context, event):
        """ runs while editing source; cleans up when finished """
        try:
            scn = bpy.context.scene
            source = bpy.data.objects.get(self.source_name)
            # if file was saved while editing source, break modal gracefully
            if not bpy.context.window_manager["editingSourceInStorage"]:
                bpy.props.Rebrickr_commitEdits = False
                redraw_areas("VIEW_3D")
                scn.update()
                return {"FINISHED"}
            if bpy.props.Rebrickr_commitEdits or source is None or bpy.context.scene.name != "Rebrickr_storage (DO NOT RENAME)" or source.mode != "EDIT" or event.type in {"ESC"} or (event.type in {"TAB"} and event.value == "PRESS"):
                self.report({"INFO"}, "Edits Committed")
                # if Rebrickr_storage scene is not active, set to active
                sto_scn = bpy.data.scenes.get("Rebrickr_storage (DO NOT RENAME)")
                if bpy.context.scene != sto_scn:
                    for screen in bpy.data.screens:
                        screen.scene = sto_scn
                # set source to object mode
                select(source, active=source)
                bpy.ops.object.mode_set(mode='OBJECT')
                setOriginToObjOrigin(toObj=source, fromLoc=self.lastSourceOrigLoc)
                # reset source origin to adjusted location
                if source["before_edit_location"] != -1:
                    source.location = source["before_edit_location"]
                source.rotation_mode = "XYZ"
                source.rotation_euler = Euler(tuple(source["previous_rotation"]), "XYZ")
                source.scale = source["previous_scale"]
                setOriginToObjOrigin(toObj=source, fromLoc=source["before_origin_set_location"])
                if bpy.context.scene.name == "Rebrickr_storage (DO NOT RENAME)":
                    for screen in bpy.data.screens:
                        screen.scene = bpy.data.scenes.get(bpy.props.Rebrickr_origScene)
                bpy.props.Rebrickr_commitEdits = False
                bpy.context.window_manager["editingSourceInStorage"] = False
                redraw_areas("VIEW_3D")
                scn.update()
                return {"FINISHED"}
        except:
            if bpy.context.scene.name == "Rebrickr_storage (DO NOT RENAME)":
                for screen in bpy.data.screens:
                    screen.scene = bpy.data.scenes.get(bpy.props.Rebrickr_origScene)
            self.handle_exception()
            return {"CANCELLED"}

        return {"PASS_THROUGH"}

    def execute(self, context):
        """ prepares original source object for editing """
        try:
            # initialize variables
            scn = context.scene
            bpy.props.Rebrickr_origScene = scn.name
            cm = scn.cmlist[scn.cmlist_index]
            n = cm.source_name
            self.source_name = cm.source_name + " (DO NOT RENAME)"
            Rebrickr_bricks_gn = "Rebrickr_" + cm.source_name + "_bricks"
            Rebrickr_parent_on = "Rebrickr_%(n)s_parent" % locals()
            Rebrickr_last_origin_on = "Rebrickr_%(n)s_last_origin" % locals()
            brickLoc = None
            parentOb = None

            # if model isn't split, get brick loc/rot/scale
            if not cm.lastSplitModel and groupExists(Rebrickr_bricks_gn):
                brickGroup = bpy.data.groups[Rebrickr_bricks_gn]
                bgObjects = list(brickGroup.objects)
                b = bgObjects[0]
                scn.update()
                brickLoc = b.matrix_world.to_translation().copy()
                brickRot = b.matrix_world.to_euler().copy()
                brickScale = b.matrix_world.to_scale().copy()


            # get Rebrickr_storage (DO NOT RENAME) scene
            sto_scn = bpy.data.scenes.get("Rebrickr_storage (DO NOT RENAME)")
            if sto_scn is None:
                self.report({"WARNING"}, "'Rebrickr_storage (DO NOT RENAME)' scene could not be found")
                return {"CANCELLED"}
            # get source object
            source = bpy.data.objects.get(self.source_name)
            if source is None:
                self.report({"WARNING"}, "Source object '" + self.source_name + "' could not be found")
                return {"CANCELLED"}

            # set cursor location of Rebrickr_storage scene to cursor loc of original scene
            sto_scn.cursor_location = tuple(scn.cursor_location)

            # set active scene as Rebrickr_storage (DO NOT RENAME)
            for screen in bpy.data.screens:
                screen.scene = sto_scn

            # make source visible and active selection
            sto_scn.layers = source.layers
            for obj in sto_scn.objects:
                obj.hide = True
            source.hide = False
            bGroup = bpy.data.groups.get(Rebrickr_bricks_gn)
            source["before_edit_location"] = -1
            self.last_origin_obj = bpy.data.objects.get(Rebrickr_last_origin_on)
            if bGroup is not None and len(bGroup.objects) > 0:
                if not cm.lastSplitModel:
                    obj = bGroup.objects[0]
                else:
                    obj = None
                objParent = bpy.data.objects.get("Rebrickr_%(n)s_parent" % locals())
                l = cm.lastSourceMid.split(",")
                for i in range(len(l)):
                    l[i] = float(l[i])
                source["before_origin_set_location"] = source.matrix_world.to_translation().to_tuple()
                setOriginToObjOrigin(toObj=source, fromLoc=tuple(l))
                source["before_edit_location"] = source.location.to_tuple()
                if brickLoc is not None:
                    source.location = source.location + brickLoc - source.matrix_world.to_translation()
                    setSourceTransform(source, obj=obj, objParent=objParent, skipLocation=True)
                else:
                    setSourceTransform(source, obj=obj, objParent=objParent)


            select(source, active=source)

            # set sourceOrig origin to previous origin location
            scn.update()
            self.lastSourceOrigLoc = source.matrix_world.to_translation().to_tuple()
            setOriginToObjOrigin(toObj=source, fromObj=self.last_origin_obj)
            scn.update()

            # enter edit mode
            bpy.ops.object.mode_set(mode='EDIT')

            bpy.context.window_manager["editingSourceInStorage"] = {"source_name":self.source_name, "lastSourceOrigLoc":self.lastSourceOrigLoc}

            # push current
            if not cm.sourceIsDirty:
                bpy.ops.ed.undo_push(message="Toggle Source Editmode")
            cm.sourceIsDirty = True

            # run modal
            context.window_manager.modal_handler_add(self)
        except:
            if bpy.context.scene.name == "Rebrickr_storage (DO NOT RENAME)":
                for screen in bpy.data.screens:
                    screen.scene = bpy.data.scenes.get(bpy.props.Rebrickr_origScene)
            self.handle_exception()
            return {"CANCELLED"}

        return {"RUNNING_MODAL"}

    def handle_exception(self):
        errormsg = print_exception('Rebrickr_log')
        # if max number of exceptions occur within threshold of time, abort!
        print('\n'*5)
        print('-'*100)
        print("Something went wrong. Please start an error report with us so we can fix it! (press the 'Report a Bug' button under the 'Brick Models' dropdown menu of the Rebrickr)")
        print('-'*100)
        print('\n'*5)
        showErrorMessage("Something went wrong. Please start an error report with us so we can fix it! (press the 'Report a Bug' button under the 'Brick Models' dropdown menu of the Rebrickr)", wrap=240)

class RebrickrCommitEdits(bpy.types.Operator):
    """ Commit Edits to Source Object Mesh """                                  # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "rebrickr.commit_edits"                                   # unique identifier for buttons and menu items to reference.
    bl_label = "Commit Edits to Source Object Mesh"                             # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        """ ensures operator can execute (if not, returns false) """
        scn = context.scene
        if scn.name != "Rebrickr_storage (DO NOT RENAME)":
            return False
        return True

    def execute(self, context):
        bpy.props.Rebrickr_commitEdits = True
        return{"FINISHED"}
