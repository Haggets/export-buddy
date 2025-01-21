from functools import lru_cache


@lru_cache(maxsize=None)
def vertices_to_tuples(vertices) -> tuple:
    return tuple((vertex.co.x, vertex.co.y, vertex.co.z) for vertex in vertices)


def get_vertices_hash(vertices) -> int:
    return hash(vertices_to_tuples(vertices))
