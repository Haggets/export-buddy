from bpy.types import MeshLoopColorLayer, Object


def apply_vertex_color(
    object: Object, color: tuple[float, float, float]
) -> MeshLoopColorLayer:
    mesh = object.data
    if not (color_layer := mesh.vertex_colors.get("Attribute")):
        color_layer = mesh.vertex_colors.new(name="Attribute")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            color_layer.data[loop_index].color = color

    return color_layer
