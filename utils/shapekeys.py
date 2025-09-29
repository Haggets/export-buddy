import bpy
from bpy.types import Modifier, Object, Operator

from .debug import DEBUG_measure_execution_time, print_colored
from .hashes import get_vertices_hash
from .mesh import copy_collapsed_basis
from .modifiers import handle_decimate_modifier, transfer_unapplied_modifiers
from .object import create_linked_duplicate


def linked_duplicate_per_shapekey(object: Object) -> dict[str, Object | None]:
    """Create a new (pinned) linked object for each shapekey using hashes (for fast comparison)"""
    reference_hash = get_vertices_hash(object.data.vertices)

    shaped_objects = {}
    for i, shape_key in enumerate(object.data.shape_keys.key_blocks):
        object.active_shape_key_index = i
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


def insert_shapekeys_from_duplicates(self: Operator, target_object: Object, shaped_objects: dict[str, Object | None]):
    """Create a new object for each duplicate object with the shapekey and modifiers applied, and then send the data to the reference object's shapekey"""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    shapekeys_lost = []
    for name, shaped_object in shaped_objects.items():
        shape_key = target_object.shape_key_add(name=name)
        if not shaped_object:
            print(f"Shapekey {name} has no changes! Skipping.")
            continue

        collapsed_mesh = shaped_object.evaluated_get(depsgraph).to_mesh()

        if not len(shape_key.points) == len(collapsed_mesh.vertices):
            shapekeys_lost.append(name)
            print(f"Mismatching vertex count for shapekey {name}! Shapekey lost.")
            shaped_object.to_mesh_clear()

            continue

        print(f"Applying shapekey {name}")
        collapsed_coordinates = [coord for vertex in collapsed_mesh.vertices for coord in vertex.co]
        shape_key.points.foreach_set("co", collapsed_coordinates)

        shaped_object.to_mesh_clear()
        # While this may seem counterintuitive, it's actually very fast since the depsgraph is only called one time,
        # as opposed to calling it each time you create a duplicate with the shapekey and modifiers applied.

    if len(shapekeys_lost):
        self.report({"ERROR"}, f"Shapekeys lost: {', '.join(shapekeys_lost) }")


def copy_with_modifiers_applied(
    self: Operator, object: Object, unapplied_modifiers: list[Modifier | None] = []
) -> Object:
    applied_modifiers: list[Modifier] = list(object.modifiers)

    for modifier in unapplied_modifiers:
        if not modifier:
            continue

        applied_modifiers.remove(modifier)

        modifier.show_viewport = False

    # No modifiers to apply
    if not len(applied_modifiers):
        self.report({"WARNING"}, f"No modifiers to apply on {object.name}!")
        mesh_copy = object.data.copy()
        mesh_copy.name = object.data.name + "_collapsed"
        object_copy = bpy.data.objects.new(object.name + "_collapsed", mesh_copy)
        object_copy.matrix_world = object.matrix_world
        bpy.context.collection.objects.link(object_copy)

        transfer_unapplied_modifiers(object_copy, unapplied_modifiers)

        return object_copy

    decimate_modifier = None
    # Decimate gets applied last
    for modifier in applied_modifiers:
        if modifier.type == "DECIMATE":
            modifier.show_viewport = False
            decimate_modifier = modifier

    object.show_only_shape_key = True
    object.active_shape_key_index = 0
    collapsed_reference = copy_collapsed_basis(object)
    bpy.context.collection.objects.link(collapsed_reference)

    # No shapekeys
    if not getattr(object.data, "shape_keys"):
        self.report(
            {"INFO"},
            f"No modifiers to apply on {object.name}! Applying modifiers on basis.",
        )
        transfer_unapplied_modifiers(collapsed_reference, unapplied_modifiers)

        handle_decimate_modifier(collapsed_reference, applied_modifiers)

        if decimate_modifier:
            decimate_modifier.show_viewport = True

        return collapsed_reference

    # TODO: Do it in batches of 10 shapekeys for very intensive models
    print_colored(f"Applying shapekeys to {collapsed_reference.name}", color_code=33)
    with DEBUG_measure_execution_time("Creating duplicates"):
        shaped_objects = linked_duplicate_per_shapekey(object)

    with DEBUG_measure_execution_time("Inserting shapekeys"):
        insert_shapekeys_from_duplicates(self, collapsed_reference, shaped_objects)

    handle_decimate_modifier(collapsed_reference, applied_modifiers)
    print_colored(f"Finished applying shapekeys to {collapsed_reference.name}", color_code=32)

    # Restores skipped modifiers
    transfer_unapplied_modifiers(collapsed_reference, unapplied_modifiers)

    if decimate_modifier:
        decimate_modifier.show_viewport = True

    # Removes leftovers
    for shaped_object in shaped_objects.values():
        if not shaped_object:
            continue
        bpy.data.objects.remove(shaped_object)

    return collapsed_reference
