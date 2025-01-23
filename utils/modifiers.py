import bpy
from bpy.types import DecimateModifier, Object, Operator

from .others import is_attribute_read_only
from .scene import change_mode, focus_object, select_objects


def check_modifiers(self: Operator, object: Object):
    """Check if the object has any unsupported modifiers or settings"""
    for modifier in object.modifiers:
        if modifier.type == "BEVEL" and modifier.limit_method == "ANGLE":
            self.report(
                {"WARNING"},
                f"{object.name}: Bevel modifiers with 'Angle' limit are not supported.",
            )
            modifier.show_viewport = False

        # Decimate modifier is a special case
        if modifier.type == "DECIMATE":
            if modifier.decimate_type != "DISSOLVE":
                self.report(
                    {"WARNING"},
                    f"{object.name}: Decimate modifiers without 'Dissolve' type are not supported.",
                )
            modifier.show_viewport = False


def handle_decimate_modifier(object: Object, modifier: DecimateModifier):
    """Apply decimate modifier to object"""
    selected_objects = bpy.context.selected_objects
    active_object = bpy.context.object

    focus_object(object)
    bpy.context.view_layer.objects.active = object
    change_mode("EDIT")
    if modifier.vertex_group:
        object.vertex_groups.active = modifier.vertex_group

    bpy.ops.mesh.decimate(
        ratio=modifier.ratio,
        use_vertex_group=True if modifier.vertex_group else False,
        vertex_group_factor=modifier.vertex_group_factor,
        invert_vertex_group=modifier.vertex_group_factor,
        use_symmetry=modifier.use_symmetry,
        symmetry_axis=modifier.symmetry_axis,
    )

    focus_object(active_object)
    select_objects(selected_objects)

    object.modifiers.remove(modifier)


def transfer_unapplied_modifiers(source: Object, target: Object):
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
