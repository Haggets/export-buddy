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
        col.label(text="Test!")
        col.operator("eb.test")


def register_ui():
    register_class(EB_PT_mainpanel)


def unregister_ui():
    unregister_class(EB_PT_mainpanel)
