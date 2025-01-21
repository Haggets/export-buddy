import bpy
from bpy.types import Object


def change_mode(mode: str):
    bpy.ops.object.mode_set(mode=mode)


def focus_object(object: Object):
    for obj in bpy.context.selected_objects:
        obj.select_set(False)

    object.select_set(True)
    bpy.context.view_layer.objects.active = object


def select_objects(objects: list[Object]):
    for obj in objects:
        obj.select_set(True)
