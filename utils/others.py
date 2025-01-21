from typing import Any


def is_attribute_read_only(obj: Any, attr: str) -> bool:
    try:
        setattr(obj, attr, getattr(obj, attr))
        return False
    except AttributeError:
        return True
