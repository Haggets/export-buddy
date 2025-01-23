import bpy
from bpy.types import Depsgraph, Mesh, Object

from .scene import change_mode, focus_object, select_objects


def create_linked_duplicate(object: Object, suffix: str) -> Object:
    duplicate_object: Object = object.copy()
    duplicate_object.name = f"{object.name}_{suffix}"

    duplicate_object.matrix_world = object.matrix_world
    return duplicate_object


def create_collapsed_mesh(depsgraph: Depsgraph, object: Object) -> Mesh:
    return object.evaluated_get(depsgraph).data.copy()


def merge_meshes(main_object: Object, objects_to_merge: list[Object]):
    change_mode("OBJECT")
    focus_object(main_object)
    select_objects(objects_to_merge)
    bpy.ops.object.join()


def copy_collapsed_basis(object: Object):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    reference_mesh = create_collapsed_mesh(depsgraph, object)
    collapsed_reference = bpy.data.objects.new(
        object.name.replace("_copy", "_collapsed"), reference_mesh
    )
    collapsed_reference.matrix_world = object.matrix_world
    return collapsed_reference
