from .ops import register_ops, unregister_ops
from .ui import register_ui, unregister_ui


def register():
    register_ops()
    register_ui()


def unregister():
    unregister_ops()
    unregister_ui()
