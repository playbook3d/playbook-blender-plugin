import bpy
import os
import math
import requests


#
def is_valid_image_file(filepath: str) -> bool:
    valid_extensions = {".png", ".jpg", ".jpeg"}

    ext = filepath.lower().rsplit(".", 1)[-1]
    return f".{ext}" in valid_extensions


#
def get_filepath(filename, folder=""):
    dir = os.path.dirname(__file__)

    if not folder:
        return os.path.join(dir, filename)

    return os.path.join(dir, folder, filename)


#
def get_scaled_resolution_height(width: int):
    render = bpy.context.scene.render
    resolution_x = render.resolution_x
    resolution_y = render.resolution_y
    resolution_percentage = render.resolution_percentage

    final_resolution_x = resolution_x * (resolution_percentage / 100)
    final_resolution_y = resolution_y * (resolution_percentage / 100)

    resolution_scale = width / final_resolution_x
    return math.ceil(final_resolution_y * resolution_scale)


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


# Function to download the image from a URL and save it locally
def download_image(url, save_path):
    try:
        print(f"URL: {url}")
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"Image downloaded successfully and saved to {save_path}")
    except Exception as e:
        print(f"Failed to download the image: {e}")


# Function to load the image into Blender
def load_image_into_blender(file_path):
    if os.path.exists(file_path):
        image = bpy.data.images.load(filepath=file_path)
        print(f"Image loaded into Blender: {image.name}")
        return image
    else:
        print(f"File does not exist: {file_path}")
        return None