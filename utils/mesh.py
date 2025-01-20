from bpy.types import Depsgraph, Object


def create_duplicate_model(object: Object, suffix: str):
    duplicate_mesh = object.data.copy()
    duplicate_mesh.name = f"{object.data.name}_{suffix}"

    duplicate_object = object.copy()
    duplicate_object.name = f"{object.name}_{suffix}"
    duplicate_object.data = duplicate_mesh

    duplicate_object.matrix_world = object.matrix_world
    return duplicate_object


def create_collapsed_mesh(depsgraph: Depsgraph, object: Object):
    return object.evaluated_get(depsgraph).data.copy()
