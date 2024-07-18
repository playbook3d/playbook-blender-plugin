import bpy

original_settings = {}


# Save the current color management settings
def save_settings():
    original_settings.clear()
    original_settings.update = {
        "display_device": bpy.context.scene.display_settings.display_device,
        "view_transform": bpy.context.scene.view_settings.view_transform,
        "look": bpy.context.scene.view_settings.look,
        "exposure": bpy.context.scene.view_settings.exposure,
        "gamma": bpy.context.scene.view_settings.gamma,
        "sequencer": bpy.context.scene.sequencer_colorspace_settings.name,
        "user_curves": bpy.context.scene.view_settings.use_curve_mapping,
        "use_nodes": bpy.context.scene.use_nodes,
    }


# Prepare the color management settings for render
def set_settings():
    scene = bpy.context.scene
    scene.display_settings.display_device = "sRGB"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.sequencer_colorspace_settings.name = "sRGB"
    scene.view_settings.use_curve_mapping = False
    scene.use_nodes = False


# Reset the color management settings to their previous values
def reset_settings():
    scene = bpy.context.scene
    scene.display_settings.display_device = original_settings["display_device"]
    scene.view_settings.view_transform = original_settings["view_transform"]
    scene.view_settings.look = original_settings["look"]
    scene.view_settings.exposure = original_settings["exposure"]
    scene.view_settings.gamma = original_settings["gamma"]
    scene.sequencer_colorspace_settings.name = original_settings["sequencer"]
    scene.view_settings.use_curve_mapping = original_settings["user_curves"]
    scene.use_nodes = original_settings["use_nodes"]
