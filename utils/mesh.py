import bpy
from bpy.types import Depsgraph, Mesh, Object

from .scene import change_mode, focus_object, select_objects


def create_collapsed_mesh(depsgraph: Depsgraph, object: Object) -> Mesh:
    return object.evaluated_get(depsgraph).data.copy()


def merge_meshes(main_object: Object, objects_to_merge: list[Object]):
    mesh_data = []
    for object in objects_to_merge:
        mesh_data.append(object.data)

    change_mode("OBJECT")
    focus_object(main_object)
    select_objects(objects_to_merge)
    bpy.ops.object.join()

    for mesh in mesh_data:
        bpy.data.meshes.remove(mesh)


def copy_collapsed_basis(object: Object):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    reference_mesh = create_collapsed_mesh(depsgraph, object)
    collapsed_reference = bpy.data.objects.new(object.name + "_collapsed", reference_mesh)
    collapsed_reference.data.name = object.name + "_collapsed"
    collapsed_reference.matrix_world = object.matrix_world
    return collapsed_reference
