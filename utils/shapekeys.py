import bpy
from bpy.types import Depsgraph, Object

from .hashes import get_vertices_hash


def apply_modifiers_with_shapekeys(object: Object):
    if not getattr(object.data, "shape_keys"):
        print(f"No shapekeys found on {object.name}! Skipping")
        return

    shaped_objects = {}

    # Hashes the rest pose to compare with the shapekeys
    object.show_only_shape_key = True
    object.active_shape_key_index = 0
    base_hash = get_vertices_hash(object.data.vertices)

    despgraph = bpy.context.evaluated_depsgraph_get()
    collapsed_object = create_collapsed_mesh(despgraph, object, "collapsed")

    # TODO: Duplicate all and collapse on a single depsgraph update
    # For each shapekey, create a new object and apply modifiers individually
    for index, shape_key in enumerate(object.data.shape_keys.key_blocks):
        object.active_shape_key_index = index
        shaped_hash = get_vertices_hash(shape_key.points)

        print(base_hash, shaped_hash)

        # Only create objects for shapekeys with actual changes
        if base_hash != shaped_hash:
            despgraph.update()
            shaped_object = create_collapsed_mesh(despgraph, object, shape_key.name)

            shaped_objects.setdefault(shape_key.name, shaped_object)
        else:
            shaped_objects.setdefault(shape_key.name, None)

    # Adds shapekeys into the new base object
    for name, shape_object in shaped_objects.items():
        shape_key = collapsed_object.shape_key_add(name=name)
        if not shape_object:
            print(f"Shapekey {name} has no changes! Skipping.")
            continue
        if not len(shape_key.points) == len(shape_object.data.vertices):
            print(f"Mismatching vertex count for shapekey {name}! Shapekey lost.")
            continue

        for index, vertex in enumerate(shape_key.points):
            vertex.co = shape_object.data.vertices[index].co

    bpy.context.collection.objects.link(collapsed_object)

    # Removes leftovers
    for shaped_object in shaped_objects.values():
        if not shaped_object:
            continue

        bpy.data.meshes.remove(shaped_object.data)

    object.active_shape_key_index = 0
    return collapsed_object


def create_collapsed_mesh(despgraph: Depsgraph, object: Object, suffix: str):
    evaluated_mesh = object.evaluated_get(despgraph).data.copy()
    collapsed_object = bpy.data.objects.new(object.name + f"_{suffix}", evaluated_mesh)

    collapsed_object.matrix_world = object.matrix_world
    return collapsed_object
