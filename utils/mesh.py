from bpy.types import Depsgraph, Object


def create_linked_duplicate(object: Object, suffix: str):
    duplicate_object: Object = object.copy()
    duplicate_object.name = f"{object.name}_{suffix}"

    duplicate_object.matrix_world = object.matrix_world
    return duplicate_object


def create_collapsed_mesh(depsgraph: Depsgraph, object: Object):
    return object.evaluated_get(depsgraph).data.copy()
