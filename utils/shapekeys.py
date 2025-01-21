import bpy
from bpy.types import Modifier, Object

from .debug import DEBUG_measure_execution_time
from .hashes import get_vertices_hash
from .mesh import create_collapsed_mesh, create_linked_duplicate
from .others import is_attribute_read_only


def check_modifiers(object: Object):
    for modifier in object.modifiers:
        if modifier.type == "BEVEL" and modifier.limit_method == "ANGLE":
            return (
                {"WARNING"},
                "Bevel modifiers with 'Angle' limit are not supported, many shapekeys may get lost.",
            )

    return None, None


def copy_with_modifiers_applied(
    object: Object, unapplied_modifiers: list[Modifier | None] = []
) -> Object:
    # TODO: skip if nothing needed to apply
    if not getattr(object.data, "shape_keys"):
        print(f"No shapekeys found on {object.name}! Skipping")
        return object

    modifiers: list[Modifier] = object.modifiers[:]
    for unapplied_modifier in unapplied_modifiers:
        try:
            modifiers.remove(unapplied_modifier)
        except ValueError:
            pass

    if not len(modifiers):
        print(f"No modifiers to apply on {object.name}! Skipping")
        return object

    for modifier_name in unapplied_modifiers:
        unapplied_mod = object.modifiers.get(modifier_name)
        if not unapplied_mod:
            continue

        unapplied_mod.show_viewport = False

    # Hashes the rest pose to compare with the shapekeys
    object.show_only_shape_key = True
    object.active_shape_key_index = 0
    reference_hash = get_vertices_hash(object.data.vertices)

    with DEBUG_measure_execution_time("Applying shapekeys"):
        shaped_objects = {}
        # Create a new (pinned) linked object for each shapekey using hashes (for fast comparison)
        for index, shape_key in enumerate(object.data.shape_keys.key_blocks):
            object.active_shape_key_index = index
            shaped_hash = get_vertices_hash(shape_key.points)
            # print(reference_hash, shaped_hash)

            # Only create objects for shapekeys with actual changes
            if reference_hash != shaped_hash:
                shaped_object = create_linked_duplicate(object, shape_key.name)
                bpy.context.collection.objects.link(shaped_object)

                shaped_objects.setdefault(shape_key.name, shaped_object)
            else:
                shaped_objects.setdefault(shape_key.name, None)

        object.active_shape_key_index = 0
        depsgraph = bpy.context.evaluated_depsgraph_get()

        reference_mesh = create_collapsed_mesh(depsgraph, object)
        collapsed_reference = bpy.data.objects.new(
            object.name + "_collapsed", reference_mesh
        )
        collapsed_reference.matrix_world = object.matrix_world
        bpy.context.collection.objects.link(collapsed_reference)

        # Create a new object for each duplicate object with the shapekey and modifiers applied, and then send the data to the reference object's shapekey
        for name, shaped_object in shaped_objects.items():
            shape_key = collapsed_reference.shape_key_add(name=name)
            if not shaped_object:
                print(f"Shapekey {name} has no changes! Skipping.")
                continue

            collapsed_mesh = shaped_object.evaluated_get(depsgraph).to_mesh()

            if not len(shape_key.points) == len(collapsed_mesh.vertices):
                print(f"Mismatching vertex count for shapekey {name}! Shapekey lost.")
                continue

            print(f"Applying shapekey {name}")
            for index, vertex in enumerate(shape_key.points):
                vertex.co = collapsed_mesh.vertices[index].co

            shaped_object.to_mesh_clear()
            # While this may seem counterintuitive, it's actually very fast since the depsgraph is only called one time,
            # as opposed to calling it each time you create a duplicate with the shapekey and modifiers applied.

    print("Finished applying shapekeys.")

    # Restores skipped modifiers
    for modifier_name in unapplied_modifiers:
        unapplied_mod = object.modifiers.get(modifier_name)
        if not unapplied_mod:
            continue

        unapplied_mod.show_viewport = True

        modifier = collapsed_reference.modifiers.new(
            name=modifier_name, type=unapplied_mod.type
        )
        for key in dir(unapplied_mod):
            if is_attribute_read_only(unapplied_mod, key):
                continue

            setattr(modifier, key, getattr(unapplied_mod, key))

    # Removes leftovers
    for shaped_object in shaped_objects.values():
        if not shaped_object:
            continue
        bpy.data.objects.remove(shaped_object)

    return collapsed_reference
