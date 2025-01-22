import bpy
from bpy.types import Modifier, Object, Operator

from .debug import DEBUG_measure_execution_time
from .hashes import get_vertices_hash
from .mesh import create_collapsed_mesh, create_linked_duplicate
from .others import is_attribute_read_only


def check_modifiers(self: Operator, object: Object):
    """Check if the object has any unsupported modifiers or settings"""
    for modifier in object.modifiers:
        if modifier.type == "BEVEL" and modifier.limit_method == "ANGLE":
            self.report(
                {"ERROR"},
                f"{object.name}: Bevel modifiers with 'Angle' limit are not supported, many shapekeys may get lost.",
            )

        # Decimate modifier is a special case
        if modifier.type == "DECIMATE":
            if modifier.decimate_type != "DISSOLVE":
                self.report(
                    {"WARNING"},
                    "Decimate modifiers without 'Dissolve' type are not supported.",
                )

            modifier.show_viewport = False


def transfer_modifiers(source: Object, target: Object):
    """Transfer modifiers from source to target object"""
    for modifier in source.modifiers:
        if modifier.show_viewport:
            continue

        modifier.show_viewport = True

        modifier = target.modifiers.new(name=modifier.name, type=modifier.type)
        for key in dir(modifier):
            if is_attribute_read_only(modifier, key):
                continue

            setattr(modifier, key, getattr(modifier, key))

    return target


def linked_duplicate_per_shapekey(object: Object):
    """Create a new (pinned) linked object for each shapekey using hashes (for fast comparison)"""
    object.show_only_shape_key = True
    object.active_shape_key_index = 0
    reference_hash = get_vertices_hash(object.data.vertices)

    shaped_objects = {}
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
    return shaped_objects


def insert_shapekeys_from_duplicates(
    target_object: Object, shaped_objects: dict[Object]
):
    """Create a new object for each duplicate object with the shapekey and modifiers applied, and then send the data to the reference object's shapekey"""
    depsgraph = bpy.context.evaluated_depsgraph_get()

    #
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
        for index, vertex in enumerate(shape_key.points):
            vertex.co = collapsed_mesh.vertices[index].co

        shaped_object.to_mesh_clear()
        # While this may seem counterintuitive, it's actually very fast since the depsgraph is only called one time,
        # as opposed to calling it each time you create a duplicate with the shapekey and modifiers applied.


def copy_collapsed_basis(object: Object):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    reference_mesh = create_collapsed_mesh(depsgraph, object)
    collapsed_reference = bpy.data.objects.new(
        object.name + "_collapsed", reference_mesh
    )
    collapsed_reference.matrix_world = object.matrix_world
    return collapsed_reference


def copy_with_modifiers_applied(
    object: Object, unapplied_modifiers: list[Modifier | None] = []
) -> Object:

    # TODO: Exception for decimate modifier (Use the decimate function instead)
    modifiers: list[Modifier] = object.modifiers[:]
    for unapplied_modifier in unapplied_modifiers:
        try:
            modifiers.remove(unapplied_modifier)
        except ValueError:
            pass

    if not len(modifiers):
        print(f"No modifiers to apply on {object.name}!")
        collapsed_reference = bpy.data.objects.new(
            object.name + "_collapsed", object.data
        )
        collapsed_reference.matrix_world = object.matrix_world
        bpy.context.collection.objects.link(collapsed_reference)

        transfer_modifiers(object, collapsed_reference)
        return collapsed_reference

    for modifier in unapplied_modifiers:
        if not modifier:
            continue

        modifier.show_viewport = False

    if not getattr(object.data, "shape_keys"):
        print(f"No shapekeys found on {object.name}! Applying modifiers on basis.")
        collapsed_reference = copy_collapsed_basis(object)
        bpy.context.collection.objects.link(collapsed_reference)

        transfer_modifiers(object, collapsed_reference)
        return collapsed_reference

    collapsed_reference = copy_collapsed_basis(object)
    bpy.context.collection.objects.link(collapsed_reference)

    with DEBUG_measure_execution_time("Applying shapekeys"):
        shaped_objects = linked_duplicate_per_shapekey(object)
        insert_shapekeys_from_duplicates(object, shaped_objects)

    print("Finished applying shapekeys.")

    # Restores skipped modifiers
    transfer_modifiers(object, collapsed_reference)

    # Removes leftovers
    for shaped_object in shaped_objects.values():
        if not shaped_object:
            continue
        bpy.data.objects.remove(shaped_object)

    return collapsed_reference
