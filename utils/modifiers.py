import bpy
from bpy.types import DecimateModifier, Modifier, Object, Operator

from .others import is_attribute_read_only
from .scene import change_mode, focus_object, select_objects


def check_incompatible_modifiers(self: Operator, object: Object):
    """Check if the object has any unsupported modifiers or settings"""
    for modifier in object.modifiers:
        if modifier.type == "BEVEL" and modifier.limit_method == "ANGLE":
            self.report(
                {"ERROR"},
                f"{object.name}: Bevel modifiers with 'Angle' limit are not supported. Shapekeys may be lost.",
            )
            continue

        # Decimate modifier is a special case
        if modifier.type == "DECIMATE":
            if modifier.decimate_type != "COLLAPSE":
                self.report(
                    {"ERROR"},
                    f"{object.name}: Decimate modifiers without 'Dissolve' type are not supported.",
                )

                modifier.show_viewport = False
                continue

        if modifier.type == "WELD":
            self.report(
                {"ERROR"},
                f"{object.name}: Weld modifiers causes issues with big distance values. Shapekeys may be lost",
            )
            continue


def handle_decimate_modifier(object: Object, modifiers: list[Modifier]):
    """Apply decimate modifier to object"""

    decimate_modifier = None
    for modifier in modifiers:
        if modifier.type != "DECIMATE":
            continue

        decimate_modifier: DecimateModifier = modifier

    if not decimate_modifier:
        return

    current_mode = object.mode
    selected_objects = bpy.context.selected_objects
    active_object = bpy.context.object

    focus_object(object)
    bpy.context.view_layer.objects.active = object
    change_mode("EDIT")
    bpy.ops.mesh.select_all(action="SELECT")

    if decimate_modifier.vertex_group:
        vertex_group = object.vertex_groups.get(decimate_modifier.vertex_group)
        object.vertex_groups.active = vertex_group

    bpy.ops.mesh.decimate(
        ratio=decimate_modifier.ratio,
        use_vertex_group=True if decimate_modifier.vertex_group else False,
        vertex_group_factor=decimate_modifier.vertex_group_factor,
        invert_vertex_group=decimate_modifier.invert_vertex_group,
        use_symmetry=decimate_modifier.use_symmetry,
        symmetry_axis=decimate_modifier.symmetry_axis,
    )

    change_mode(current_mode)
    focus_object(active_object)
    select_objects(selected_objects)


def transfer_unapplied_modifiers(
    target: Object, unapplied_modifiers: list[Modifier | None]
):
    """Transfer modifiers from source to target object"""
    for modifier in unapplied_modifiers:
        if not modifier:
            continue

        modifier.show_viewport = True

        new_modifier = target.modifiers.new(name=modifier.name, type=modifier.type)
        for key in dir(modifier):
            if is_attribute_read_only(modifier, key):
                continue

            setattr(new_modifier, key, getattr(modifier, key))

    return target
