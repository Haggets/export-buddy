from bpy.types import Operator
from bpy.utils import register_class, unregister_class

from .utils.shapekeys import apply_modifiers_with_shapekeys


class EB_OT_test(Operator):
    bl_idname = "eb.test"
    bl_label = "Test Operator"

    def execute(self, context):
        apply_modifiers_with_shapekeys(context.object, ["Armature"])
        self.report({"INFO"}, "Modifiers applied successfully.")
        return {"FINISHED"}


def register_ops():
    register_class(EB_OT_test)


def unregister_ops():
    unregister_class(EB_OT_test)
