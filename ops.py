from bpy.types import Operator
from bpy.utils import register_class, unregister_class

from .utils.mesh import merge_meshes
from .utils.modifiers import check_modifiers
from .utils.shapekeys import copy_with_modifiers_applied


class EB_OT_test(Operator):
    bl_idname = "eb.apply_and_merge"
    bl_label = "Apply Modifiers & Merge to Active"

    def execute(self, context):
        active_reference = None
        collapsed_objects = []
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

            check_modifiers(self, object)

            collapsed_object = copy_with_modifiers_applied(object, skipped_modifiers)

            if collapsed_object.name.replace("_collapsed", "") == context.object.name:
                active_reference = collapsed_object
                continue

            collapsed_objects.append(collapsed_object)

        merge_meshes(active_reference, collapsed_objects)
        self.report({"INFO"}, "Modifiers applied successfully.")

        return {"FINISHED"}


def register_ops():
    register_class(EB_OT_test)


def unregister_ops():
    unregister_class(EB_OT_test)
