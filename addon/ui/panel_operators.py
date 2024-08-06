import bpy
from bpy.types import Operator
from bpy.utils import register_class, unregister_class


# Operator to show / hide the 'General' panel
class RetexturePanelOperator(Operator):
    bl_idname = "op.retexture_panel"
    bl_label = "Retexture"

    def execute(self, context):
        bpy.context.scene.show_retexture_panel = (
            not bpy.context.scene.show_retexture_panel
        )
        return {"FINISHED"}


# Operator to show / hide the 'Object Masks' panel
class ObjectMaskPanelOperator(Operator):
    bl_idname = "op.object_mask_panel"
    bl_label = "Object Mask"

    def execute(self, context):
        bpy.context.scene.show_mask_panel = not bpy.context.scene.show_mask_panel
        return {"FINISHED"}


# Operator to show / hide the 'Style Transfer' panel
class StylePanelOperator(Operator):
    bl_idname = "op.style_panel"
    bl_label = "Style Transfer"

    def execute(self, context):
        bpy.context.scene.show_style_panel = not bpy.context.scene.show_style_panel
        return {"FINISHED"}


# Operator to show / hide the 'Relight' panel
class RelightPanelOperator(Operator):
    bl_idname = "op.relight_panel"
    bl_label = "Relight"

    def execute(self, context):
        bpy.context.scene.show_relight_panel = not bpy.context.scene.show_relight_panel
        return {"FINISHED"}


# Operator to show / hide the 'Upscale' panel
class UpscalePanelOperator(Operator):
    bl_idname = "op.upscale_panel"
    bl_label = "Upscale"

    def execute(self, context):
        bpy.context.scene.show_upscale_panel = not bpy.context.scene.show_upscale_panel
        return {"FINISHED"}


classes = [
    RetexturePanelOperator,
    ObjectMaskPanelOperator,
    StylePanelOperator,
    RelightPanelOperator,
    UpscalePanelOperator,
]


def register():
    global classes
    for cls in classes:
        register_class(cls)


def unregister():
    global classes
    for cls in classes:
        unregister_class(cls)
