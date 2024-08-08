import bpy


# Create a new simple RGB material
def create_rgb_material(name: str, color: tuple) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)

    mat.use_nodes = True
    nodes = mat.node_tree.nodes

    # Clear the material's nodes
    for node in nodes:
        nodes.remove(node)

    rgb_node = nodes.new(type="ShaderNodeRGB")
    rgb_node.outputs["Color"].default_value = color

    material_output = nodes.new(type="ShaderNodeOutputMaterial")

    # Link the created nodes
    mat.node_tree.links.new(
        rgb_node.outputs["Color"], material_output.inputs["Surface"]
    )

    return mat


# Convert a Blender FloatVectorProperty color to a hexadecimal color string
def color_to_hex(color) -> str:
    r, g, b, a = [int(c * 255) for c in color]

    # Format the RGBA components into a hex string
    hex_color = "#{:02X}{:02X}{:02X}{:02X}".format(r, g, b, a)

    return hex_color
