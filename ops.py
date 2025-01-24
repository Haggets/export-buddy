from bpy.types import Context, Object, Operator
from bpy.utils import register_class, unregister_class

from .utils.debug import DEBUG_measure_execution_time
from .utils.materials import handle_object_materials
from .utils.mesh import merge_meshes
from .utils.modifiers import check_incompatible_modifiers
from .utils.scene import focus_object
from .utils.shapekeys import copy_with_modifiers_applied


class EB_OT_apply_and_merge(Operator):
    bl_idname = "eb.apply_and_merge"
    bl_label = "Apply Modifiers & Merge to Active"

    @classmethod
    def poll(cls, context: Context):
        if not context.object:
            return
        if not context.selected_objects:
            return
        if context.object.type != "MESH":
            return

        return True

    def execute(self, context):
        active_object: Object = context.object
        active_reference = None
        collapsed_objects = []
        with DEBUG_measure_execution_time("Accumulate apply and merge"):
            for object in context.selected_objects:
                if object.type != "MESH":
                    continue

                skipped_modifiers = []
                for modifier in object.modifiers:
                    if not modifier.show_viewport:
                        skipped_modifiers.append(modifier)
                        continue

                    if modifier.type == "ARMATURE":
                        skipped_modifiers.append(modifier)
                        continue

                check_incompatible_modifiers(self, object)

                collapsed_object = copy_with_modifiers_applied(self, object, skipped_modifiers)
                handle_object_materials(object, collapsed_object)
                object.hide_set(True)

                if collapsed_object.name.replace("_collapsed", "") == active_object.name:
                    active_reference = collapsed_object
                    continue

                collapsed_objects.append(collapsed_object)

            focus_object(active_reference)
            if len(collapsed_objects) > 1:
                merge_meshes(active_reference, collapsed_objects)

        # Shouldn't happen
        if not active_reference:
            return {"FINISHED"}

        active_reference.active_shape_key_index = 0

        # self.report({"INFO"}, "Modifiers applied successfully.")

        return {"FINISHED"}


def register_ops():
    register_class(EB_OT_apply_and_merge)


def unregister_ops():
    unregister_class(EB_OT_apply_and_merge)
