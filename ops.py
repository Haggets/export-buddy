from bpy.types import Operator
from bpy.utils import register_class, unregister_class

from .utils.mesh import merge_meshes
from .utils.shapekeys import copy_with_modifiers_applied


class EB_OT_test(Operator):
    bl_idname = "eb.test"
    bl_label = "Test Operator"

    def execute(self, context):
        collapsed_objects = []
        for object in context.selected_objects:
            if object.type != "MESH":
                continue

            skipped_modifiers = []
            for mod in object.modifiers:
                if mod.type == "ARMATURE":
                    skipped_modifiers.append(mod)

            # self.report()
            collapsed_object = copy_with_modifiers_applied(object, skipped_modifiers)
            collapsed_objects.append(collapsed_object)

        merge_meshes(context.object, collapsed_objects)
        self.report({"INFO"}, "Modifiers applied successfully.")

        return {"FINISHED"}


def register_ops():
    register_class(EB_OT_test)


def unregister_ops():
    unregister_class(EB_OT_test)
