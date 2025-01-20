import time
from contextlib import contextmanager

import bpy


@contextmanager
def DEBUG_measure_execution_time(name: str = ""):
    """Debug function. Measures time it takes to execute a set of operations. Used with the with keyword."""
    if not name:
        name = "Execution"

    time_start = time.time()
    yield
    print(f"{name} time: {round(time.time() - time_start, 3)} seconds")


def DEBUG_viewport_snapshot():
    """Debug function. Used in conjunction with breakpoints to diagnose issues."""
    bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)
