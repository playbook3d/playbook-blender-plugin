import asyncio
import bpy
import os
import base64
from .beauty_render import render_beauty_pass
from .mask_render import render_mask_pass
from .depth_render import render_depth_pass
from .outline_render import render_outline_pass
from .workspace import open_render_window
from .properties import set_visible_objects
from .visible_objects import color_hex
from .comfy_deploy_api.network import (
    GlobalRenderSettings,
    RetextureRenderSettings,
    MaskData,
    StyleTransferRenderSettings,
    ComfyDeployClient,
    PlaybookWebsocket,
)

# VARIABLES

api_url = os.getenv("API_URL")


# Returns True if an error occurs while attempting to render the image.
def error_exists_in_flow(scene) -> bool:
    # [workflow, condition for error message]
    workflow_checks = {
        "RETEXTURE": scene.retexture_properties.retexture_prompt
        == "Describe the scene...",
        "STYLETRANSFER": not scene.style_properties.style_image,
    }

    # [workflow, error message]
    messages = {
        "RETEXTURE": "Scene prompt is missing.",
        "STYLETRANSFER": "Style transfer image is missing.",
    }

    if workflow_checks.get(scene.global_properties.global_workflow):
        scene.error_message = messages[scene.global_properties.global_workflow]
        return True

    scene.error_message = ""
    return False


#
def clear_render_folder():
    dir = os.path.dirname(__file__)

    folder_path = os.path.join(dir, "renders")

    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(path):
                    os.unlink(path)
            except Exception as e:
                print(f"Failed to delete {path}: {e}")


#
def clean_up_files():
    dir = os.path.dirname(__file__)

    folder_path = os.path.join(dir, "renders")

    if os.path.exists(folder_path):
        render_mist = os.path.join(folder_path, "render_mist.png")
        render_edge = os.path.join(folder_path, "render_edge.png")
        render_depth = os.path.join(folder_path, "depth0001.png")
        render_outline = os.path.join(folder_path, "outline0001.png")
        render_depth_new = os.path.join(folder_path, "depth.png")
        render_outline_new = os.path.join(folder_path, "outline.png")

        if os.path.exists(render_mist):
            os.remove(render_mist)
        if os.path.exists(render_edge):
            os.remove(render_edge)

        if os.path.exists(render_depth):
            os.rename(render_depth, render_depth_new)
        if os.path.exists(render_outline):
            os.rename(render_outline, render_outline_new)


# -------------------------------------------
# RENDER TO API
# -------------------------------------------


#
def get_workflow_id(global_props) -> int:
    workflow = global_props.global_workflow
    model = global_props.global_model
    style = global_props.global_style

    if style == "PHOTOREAL":
        if workflow == "RETEXTURE":
            if model == "SDXL":
                return 0
            elif model == "FLUX":
                return 1
        elif workflow == "STYLETRANSFER":
            if model == "SDXL":
                return 2
            elif model == "FLUX":
                return 3


#
def get_global_settings() -> GlobalRenderSettings:
    global_props = bpy.context.scene.global_properties

    return GlobalRenderSettings(
        global_props.global_workflow,
        global_props.global_model,
        global_props.global_style,
        0,
    )


#
def get_retexture_settings() -> RetextureRenderSettings:
    scene = bpy.context.scene

    retexture_props = scene.retexture_properties

    mask_props = [
        MaskData(
            getattr(scene, f"mask_properties{index + 1}").mask_prompt,
            color_hex[f"MASK{index + 1}"],
        )
        for index in range(7)
    ]

    return RetextureRenderSettings(
        retexture_props.retexture_prompt,
        retexture_props.retexture_structure_strength,
        *mask_props,
    )


#
def get_style_transfer_settings() -> StyleTransferRenderSettings:
    style_props = bpy.context.scene.style_properties

    return StyleTransferRenderSettings("", style_props.style_strength, 0)


#
def set_comfy_images(comfy_deploy: ComfyDeployClient):
    dir = os.path.dirname(__file__)

    beauty_path = os.path.join(dir, "renders", "beauty.png")
    mask_path = os.path.join(dir, "renders", "mask.png")
    depth_path = os.path.join(dir, "renders", "depth.png")
    outline_path = os.path.join(dir, "renders", "outline.png")

    print(f"Render path: {beauty_path}")
    print(f"Render path: {mask_path}")
    print(f"Render path: {depth_path}")
    print(f"Render path: {outline_path}")

    # Open the PNG file in binary mode
    with open(beauty_path, "rb") as beauty_file:
        beauty_blob = base64.b64encode(beauty_file.read())
    with open(mask_path, "rb") as mask_file:
        mask_blob = base64.b64encode(mask_file.read())
    with open(depth_path, "rb") as depth_file:
        depth_blob = base64.b64encode(depth_file.read())
    with open(outline_path, "rb") as outline_file:
        outline_blob = base64.b64encode(outline_file.read())

    comfy_deploy.save_image(beauty_blob, "beauty")
    comfy_deploy.save_image(mask_blob, "mask")
    comfy_deploy.save_image(depth_blob, "depth")
    comfy_deploy.save_image(outline_blob, "outline")


#
async def run_comfy_workflow(comfy_deploy: ComfyDeployClient):
    # flags = bpy.context.scene.flag_properties

    global_settings = get_global_settings()
    retexture_settings = get_retexture_settings()
    style_settings = get_style_transfer_settings()

    response = await comfy_deploy.run_workflow(
        global_settings, retexture_settings, style_settings
    )

    print(f"Response: {response}")


# Render the image from the active camera
def render_image():
    scene = bpy.context.scene

    print("----------------------------------------------")

    asyncio.run(PlaybookWebsocket().websocket_message())

    if error_exists_in_flow(scene):
        return

    scene.is_rendering = True

    set_visible_objects(bpy.context)
    clear_render_folder()

    # Render unmodified image
    render_beauty_pass()

    # Render mask image
    render_mask_pass()

    # Render depth image
    render_depth_pass()

    # Render outline image
    render_outline_pass()

    # Open the render workspace
    open_render_window()

    clean_up_files()

    comfy = ComfyDeployClient()
    set_comfy_images(comfy)
    asyncio.run(run_comfy_workflow(comfy))

    scene.is_rendering = False
