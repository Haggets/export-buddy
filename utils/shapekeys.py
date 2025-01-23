import bpy
from bpy.types import Modifier, Object

from .debug import DEBUG_measure_execution_time, print_colored
from .hashes import get_vertices_hash
from .mesh import copy_collapsed_basis, create_linked_duplicate
from .modifiers import handle_decimate_modifier, transfer_unapplied_modifiers


def linked_duplicate_per_shapekey(object: Object) -> dict[str, Object | None]:
    """Create a new (pinned) linked object for each shapekey using hashes (for fast comparison)"""
    object.show_only_shape_key = True
    object.active_shape_key_index = 0
    reference_hash = get_vertices_hash(object.data.vertices)

    shaped_objects = {}
    for index, shape_key in enumerate(object.data.shape_keys.key_blocks):
        object.active_shape_key_index = index
        shaped_hash = get_vertices_hash(shape_key.points)
        print(f"Base hash: {reference_hash}, {shape_key.name} hash: {shaped_hash}")

        # Only create objects for shapekeys with actual changes
        if reference_hash != shaped_hash:
            shaped_object = create_linked_duplicate(object, shape_key.name)
            bpy.context.collection.objects.link(shaped_object)

            shaped_objects.setdefault(shape_key.name, shaped_object)
        else:
            shaped_objects.setdefault(shape_key.name, None)

    object.active_shape_key_index = 0
    return shaped_objects


def insert_shapekeys_from_duplicates(
    target_object: Object, shaped_objects: dict[str, Object | None]
):
    """Create a new object for each duplicate object with the shapekey and modifiers applied, and then send the data to the reference object's shapekey"""
    depsgraph = bpy.context.evaluated_depsgraph_get()

    for name, shaped_object in shaped_objects.items():
        shape_key = target_object.shape_key_add(name=name)
        if not shaped_object:
            print(f"Shapekey {name} has no changes! Skipping.")
            continue

        collapsed_mesh = shaped_object.evaluated_get(depsgraph).to_mesh()

        if not len(shape_key.points) == len(collapsed_mesh.vertices):
            print(f"Mismatching vertex count for shapekey {name}! Shapekey lost.")
            continue

        print(f"Applying shapekey {name}")
        collapsed_coordinates = [
            coord for vertex in collapsed_mesh.vertices for coord in vertex.co
        ]
        shape_key.points.foreach_set("co", collapsed_coordinates)

        shaped_object.to_mesh_clear()
        # While this may seem counterintuitive, it's actually very fast since the depsgraph is only called one time,
        # as opposed to calling it each time you create a duplicate with the shapekey and modifiers applied.


def copy_with_modifiers_applied(
    object: Object, unapplied_modifiers: list[Modifier | None] = []
) -> Object:
    applied_modifiers: list[Modifier] = object.modifiers[:]
    for modifier in unapplied_modifiers:
        if not modifier:
            continue

        try:
            applied_modifiers.remove(modifier)
        except ValueError:
            pass

        modifier.show_viewport = False

    print_colored(applied_modifiers, color_code=33)

    # No modifiers to apply
    if not len(applied_modifiers):
        print(f"No modifiers to apply on {object.name}!")
        collapsed_reference = bpy.data.objects.new(
            object.name.replace("_copy", "_collapsed"), object.data
        )
        collapsed_reference.matrix_world = object.matrix_world
        bpy.context.collection.objects.link(collapsed_reference)

        transfer_unapplied_modifiers(collapsed_reference, unapplied_modifiers)

        return collapsed_reference

    collapsed_reference = copy_collapsed_basis(object)
    bpy.context.collection.objects.link(collapsed_reference)

    # No shapekeys
    if not getattr(object.data, "shape_keys"):
        print(f"No shapekeys found on {object.name}! Applying modifiers on basis.")
        transfer_unapplied_modifiers(collapsed_reference, unapplied_modifiers)

        handle_decimate_modifier(collapsed_reference, applied_modifiers)

        return collapsed_reference

    # TODO: Do it in batches of 10 shapekeys for very intensive models
    with DEBUG_measure_execution_time("Creating duplicates"):
        shaped_objects = linked_duplicate_per_shapekey(object)

    with DEBUG_measure_execution_time("Inserting shapekeys"):
        insert_shapekeys_from_duplicates(collapsed_reference, shaped_objects)

    handle_decimate_modifier(collapsed_reference, applied_modifiers)
    print_colored("Finished applying shapekeys.", color_code=32)

    # Restores skipped modifiers
    transfer_unapplied_modifiers(collapsed_reference, unapplied_modifiers)

    # Removes leftovers
    for shaped_object in shaped_objects.values():
        if not shaped_object:
            continue
        bpy.data.objects.remove(shaped_object)

    return collapsed_reference
