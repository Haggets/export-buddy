from bpy.types import Object

from .attributes import transfer_attributes


def create_linked_duplicate(object: Object, suffix: str) -> Object:
    duplicate_object: Object = object.copy()
    duplicate_object.name = f"{object.name}_{suffix}"

    duplicate_object.matrix_world = object.matrix_world
    return duplicate_object


def transfer_object_properties(source: Object, target: Object, ignored_attrs: list[str] = []):
    """Transfer properties from source to target object"""

    transfer_attributes(source, target, ignored_attrs)
