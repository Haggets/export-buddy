from bpy.types import Object

from .attributes import transfer_attributes


def handle_object_materials(source: Object, target: Object):
    """Transfer materials from source to target object"""
    for index, slot in enumerate(source.material_slots):
        if index >= len(target.material_slots):
            return

        target_slot = target.material_slots[index]
        transfer_attributes(slot, target_slot)

    return target
