import bpy
from bpy.types import Context, Mesh, Object, Operator
from bpy.utils import register_class, unregister_class

from .utils.debug import DEBUG_measure_execution_time
from .utils.materials import handle_object_materials
from .utils.mesh import merge_meshes
from .utils.modifiers import check_incompatible_modifiers, handle_hidden_modifiers
from .utils.object import transfer_object_properties
from .utils.scene import focus_object
from .utils.shapekeys import copy_with_modifiers_applied


class EB_OT_apply_and_merge(Operator):
    bl_idname = "eb.apply_and_merge"
    bl_label = "Apply Modifiers and Merge to Active"

    @classmethod
    def poll(cls, context: Context) -> bool:
        if not context.object:
            return False
        if not context.selected_objects:
            return False
        if context.object.type != "MESH":
            return False
        if context.object.get("eb_collapsed"):
            return False

        return True

    def execute(self, context):
        selected_objects = [object for object in context.selected_objects if object.type == "MESH"]

        active_object: Object | None = context.object
        if not active_object:
            raise ValueError("No active object is selected")

        active_name = active_object.name
        active_data_name = active_object.data.name

        active_result: Object | None = None
        collapsed_objects = []

        with DEBUG_measure_execution_time("Accumulate apply and merge"):
            for object in selected_objects:
                if object.type != "MESH":
                    continue

                skipped_modifiers = handle_hidden_modifiers(object)

                # TODO: Make sure collapsed object doesn't mess with base mesh
                check_incompatible_modifiers(self, object)

                collapsed_object = copy_with_modifiers_applied(self, object, skipped_modifiers)
                handle_object_materials(object, collapsed_object)
                object.hide_set(True)

                if collapsed_object.name.replace("_collapsed", "") == active_object.name:
                    active_result = collapsed_object
                    continue

                collapsed_objects.append(collapsed_object)

        if not active_result:
            raise ValueError("Could not create merged object")

        focus_object(active_result)
        if len(collapsed_objects) > 1:
            merge_meshes(active_result, collapsed_objects)

        # Changes the active object name so it doesn't collide with the collapsed object
        active_object.name = active_object.name + "_original"
        active_object.data.name = active_object.data.name + "_original"
        # Better safe than sorry
        active_object.data.use_fake_user = True

        for object in selected_objects:
            object["eb_linked_object"] = active_result

        transfer_object_properties(active_object, active_result, ["name", "data", "active_shape_key_index"])

        active_result.name = active_name
        active_result.data.name = active_data_name
        active_result.active_shape_key_index = 0
        active_result["eb_collapsed"] = True

        self.report({"INFO"}, "Modifiers applied and objects merged.")

        return {"FINISHED"}


class EB_OT_revert_apply_and_merge(Operator):
    bl_idname = "eb.revert_apply_and_merge"
    bl_label = "Revert Apply and Merge"

    @classmethod
    def poll(cls, context: Context) -> bool:
        if not context.object:
            return False
        if not context.selected_objects:
            return False
        if not context.object.get("eb_collapsed"):
            return False

        return True

    def execute(self, context: Context):
        active_object = context.object
        if not active_object:
            raise ValueError("Active object is undefined")
        active_name = active_object.name
        linked_objects: list[Object] = []

        for object in bpy.data.objects:
            if not object.get("eb_linked_object"):
                continue
            if not object.get("eb_linked_object") == active_object:
                continue

            linked_objects.append(object)

        if isinstance(active_object.data, Mesh):
            bpy.data.meshes.remove(active_object.data)

        for object in linked_objects:
            if object.name.replace("_original", "") == active_name:
                object.data.use_fake_user = False

                object.name = object.name.replace("_original", "")
                object.data.name = object.data.name.replace("_original", "")
                context.view_layer.objects.active = object

            object.hide_set(False)
            object.select_set(True)
            del object["eb_linked_object"]

        return {"FINISHED"}


def register_ops():
    register_class(EB_OT_apply_and_merge)
    register_class(EB_OT_revert_apply_and_merge)


def unregister_ops():
    unregister_class(EB_OT_apply_and_merge)
    unregister_class(EB_OT_revert_apply_and_merge)
