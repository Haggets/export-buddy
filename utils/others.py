from typing import Any


def is_attribute_read_only(obj: Any, attr: str) -> bool:
    try:
        setattr(obj, attr, getattr(obj, attr))
        return False
    except AttributeError:
        return True


def transfer_attributes(source: Any, target: Any):
    for key in dir(source):
        if is_attribute_read_only(source, key):
            continue

        setattr(target, key, getattr(source, key))

    return target
