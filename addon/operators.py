import bpy
import webbrowser
from .objects import visible_objects, mask_objects
from .render_image import render_image
from bpy.props import StringProperty
from bpy.types import Operator
from bpy.utils import register_class, unregister_class
from bpy.app.handlers import persistent


#
class LoginOperator(Operator):
    bl_idname = "op.login"
    bl_label = "skylar@playbookxr.com"
    bl_description = "Logout of Playbook"

    def execute(self, context):
        return {"FINISHED"}


#
class UpgradeOperator(Operator):
    bl_idname = "op.upgrade"
    bl_label = "Upgrade"
    bl_description = "Upgrade"

    def execute(self, context):
        return {"FINISHED"}


#
class RandomizePromptOperator(Operator):
    bl_idname = "op.randomize_prompt"
    bl_label = "Randomize"
    bl_description = "Randomize"

    def execute(self, context):
        return {"FINISHED"}


#
class RandomizeMaskPromptOperator(Operator):
    bl_idname = "op.randomize_mask_prompt"
    bl_label = "Randomize"
    bl_description = "Randomize"

    def execute(self, context):
        return {"FINISHED"}


#
class QueueOperator(Operator):
    bl_idname = "op.queue"
    bl_label = "Open Queue"
    bl_description = "Open queue"

    def execute(self, context):
        return {"FINISHED"}


# Render the image according to the settings
class RenderOperator(Operator):
    bl_idname = "op.render_image"
    bl_label = "Render"
    bl_description = "Render the image"

    @classmethod
    def poll(cls, context):
        return not context.scene.is_rendering

    def execute(self, context):
        render_image()
        return {"FINISHED"}


# Direct the user to the Playbook website
class PlaybookWebsiteOperator(Operator):
    bl_idname = "op.send_to_playbook"
    bl_label = ""
    bl_description = "Go to Playbook3D"

    url: StringProperty(name="", default="https://www.playbook3d.com/")

    def execute(self, context):
        webbrowser.open(self.url)
        return {"FINISHED"}


# Direct the user to the Playbook Discord
class PlaybookDiscordOperator(Operator):
    bl_idname = "op.send_to_discord"
    bl_label = ""
    bl_description = "Join our Discord"

    url: StringProperty(name="", default="https://discord.com/invite/FDFEa836Pc")

    def execute(self, context):
        webbrowser.open(self.url)
        return {"FINISHED"}


# Direct the user to the Playbook Twitter
class PlaybookTwitterOperator(Operator):
    bl_idname = "op.send_to_twitter"
    bl_label = ""
    bl_description = "Check out our Twitter"

    url: StringProperty(name="", default="https://x.com/playbook3d")

    def execute(self, context):
        webbrowser.open(self.url)
        return {"FINISHED"}


#
class ClearStyleImageOperator(Operator):
    bl_idname = "op.clear_style_image"
    bl_label = ""
    bl_description = "Choose an image from local files"

    def execute(self, context):
        bpy.context.scene.style_properties.style_image = ""
        return {"FINISHED"}


#
class ClearRelightImageOperator(Operator):
    bl_idname = "op.clear_relight_image"
    bl_label = ""
    bl_description = "Choose an image from local files"

    def execute(self, context):
        bpy.context.scene.relight_properties.relight_image = ""
        return {"FINISHED"}


classes = [
    LoginOperator,
    UpgradeOperator,
    RandomizePromptOperator,
    RandomizeMaskPromptOperator,
    QueueOperator,
    RenderOperator,
    PlaybookWebsiteOperator,
    PlaybookDiscordOperator,
    PlaybookTwitterOperator,
    ClearStyleImageOperator,
    ClearRelightImageOperator,
]


# Automatically add Mask 1 to the mask list if it is empty
def on_register():
    list = bpy.context.scene.mask_list

    if not list:
        item = list.add()
        item.name = "Mask 1"


previous_objects = {}


#
def update_object_dropdown():
    update_object_dropdown_handler(bpy.context.scene)


# Set the currently selected object in the viewport as the object
# dropdown option
@persistent
def update_object_dropdown_handler(scene):
    # No mask exists
    if scene.mask_list_index == -1:
        return

    selected_obj = bpy.context.view_layer.objects.active

    if selected_obj and selected_obj.select_get():
        scene.show_object_dropdown = False
    else:
        scene.show_object_dropdown = True


@persistent
def check_for_deleted_objects_handler(scene):
    global previous_objects

    if not previous_objects:
        previous_objects = set(scene.objects.keys())
        return

    current_objects = set(scene.objects.keys())
    deleted_objects = previous_objects - current_objects

    if deleted_objects:
        for del_obj in deleted_objects:
            for key, value in mask_objects.items():
                # Object is part of the mask. Delete from mask
                if del_obj in value:
                    remove_object_from_list(scene, key, del_obj)

    previous_objects = current_objects


# Remove the given objects from the mask lists
def remove_object_from_list(scene, mask: str, obj_name: str):
    mask_index = mask[-1]
    mask_props = getattr(scene, f"mask_properties{mask_index}")

    obj_index = mask_objects[mask].index(obj_name)

    mask_props.mask_objects.remove(obj_index)
    mask_objects[mask].pop(obj_index)

    mask_props.object_list_index = 0 if mask_props.mask_objects else -1


def register():
    global classes
    for cls in classes:
        register_class(cls)

    bpy.app.handlers.depsgraph_update_post.append(update_object_dropdown_handler)
    bpy.app.handlers.depsgraph_update_post.append(check_for_deleted_objects_handler)
    bpy.app.timers.register(update_object_dropdown, first_interval=1)
    bpy.app.timers.register(on_register, first_interval=0.1)


def unregister():
    global classes
    for cls in classes:
        unregister_class(cls)

    bpy.app.handlers.depsgraph_update_post.remove(update_object_dropdown_handler)
    bpy.app.handlers.depsgraph_update_post.remove(check_for_deleted_objects_handler)
