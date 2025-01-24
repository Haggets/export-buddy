from bpy.types import Panel
from bpy.utils import register_class, unregister_class


class EB_PT_mainpanel(Panel):
    bl_idname = "EB_PT_mainpanel"
    bl_label = "Export Buddy"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Export Buddy"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.operator("eb.apply_and_merge")
        col.operator("eb.revert_apply_and_merge")

        active_object = context.object
        if not active_object:
            return
        if active_object.get("eb_linked_object"):
            col.label(text=f"Linked object: {active_object['eb_linked_object'].name}")


def register_ui():
    register_class(EB_PT_mainpanel)


def unregister_ui():
    unregister_class(EB_PT_mainpanel)
