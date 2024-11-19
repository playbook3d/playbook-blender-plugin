import bpy
from bpy.props import (
    PointerProperty,
    IntProperty,
    StringProperty,
    FloatProperty,
    EnumProperty,
    CollectionProperty,
    FloatVectorProperty,
    BoolProperty,
)
from bpy.types import Scene, PropertyGroup
from bpy.utils import register_class, unregister_class
from ..objects.visible_objects import set_visible_objects
from ..objects.objects import visible_objects, mask_objects
from ..ui.lists import MaskObjectListItem
from ..ui.icons import get_style_icon

NUM_MASKS_ALLOWED = 7

workflows = [
    (
        "RETEXTURE",
        "Generative Retexture",
        "Retexture a grayboxed scene with per-object segmentation and consistent geometry via ControlNet",
    ),
    (
        "STYLETRANSFER",
        "Style Transfer",
        "Transform your scene to match the style of an image reference via IPAdapter",
    ),
]


base_models = {
    # ("SD15", "SD 1.5", "Base model by Stability AI. Checkpoint by Juggernaut"),
    "STABLE": (
        "STABLE",
        "Stable Diffusion",
        "Base model by Stability AI. Checkpoint by Juggernaut",
    ),
    "FLUX": ("FLUX", "Flux", "SOTA model by Black Forest Labs. Best quality"),
}

models_in_workflow = {"RETEXTURE": ["STABLE", "FLUX"], "STYLETRANSFER": ["STABLE"]}

styles_in_model = {"STABLE": ["PHOTOREAL", "3DCARTOON", "ANIME"], "FLUX": ["PHOTOREAL"]}


# Available global model options
prompt_styles = [
    (
        "PHOTOREAL",
        "Photoreal",
        "Default. Works well with most scenes",
        "photoreal_style_icon",
    ),
    (
        "3DCARTOON",
        "3D Cartoon",
        "3D cartoon style with soft lighting",
        "3dcartoon_style_icon",
    ),
    ("ANIME", "Anime", "2D anime style with drawn outlines", "anime_style_icon"),
]

prompt_placeholders = {
    "Email": "Email",
    "API_Key": "API key",
    "Retexture": "Describe the scene...",
    "Mask": "Describe masked objects...",
}

angle_options = [
    ("TOPLEFT", "Top left", ""),
    ("TOPRIGHT", "Top right", ""),
    ("BOTTOMLEFT", "Bottom left", ""),
    ("BOTTOMRIGHT", "Bottom right", ""),
]

# Available upscale options
upscale_options = [("1", "1x", ""), ("2", "2x", ""), ("4", "4x", "")]

model_render_stats = {
    "STABLE": {"Height": 768, "Time": "15s - 30s", "Cost": 10},
    "FLUX": {"Height": 768, "Time": "45s - 1m", "Cost": 30},
}


#
class UserProperties(PropertyGroup):
    user_email: StringProperty(
        name="",
    )

    user_credits: IntProperty(name="")


#
class GlobalProperties(PropertyGroup):
    def get_workflow_models(self, context):
        return [
            base_models[model] for model in models_in_workflow[self.global_workflow]
        ]

    def get_prompt_styles(self, context):
        enum_items = []
        model = self.global_model
        for i, (id, name, desc, icon) in enumerate(prompt_styles):
            if id not in styles_in_model[model]:
                continue

            if icon:
                enum_items.append((id, name, desc, get_style_icon(icon), i))
            else:
                enum_items.append((id, name, desc))

        return enum_items

    def on_update_workflow(self, context):
        self.global_model = models_in_workflow[self.global_workflow][0]
        context.scene.show_retexture_panel = self.global_workflow == "RETEXTURE"

    def on_update_model(self, context):
        self.global_style = styles_in_model[self.global_model][0]

    global_workflow: EnumProperty(
        name="",
        items=workflows,
        update=lambda self, context: self.on_update_workflow(context),
    )
    global_model: EnumProperty(
        name="",
        items=get_workflow_models,
        update=lambda self, context: self.on_update_model(context),
    )
    global_style: EnumProperty(
        name="",
        items=get_prompt_styles,
    )


#
class RetextureProperties(PropertyGroup):
    #
    def on_update_prompt(self, context):
        if not self.retexture_prompt:
            self.retexture_prompt = prompt_placeholders["Retexture"]
            context.scene.flag_properties.retexture_flag = False
        else:
            context.scene.flag_properties.retexture_flag = True

    #
    def on_update_preserve_texture_mask(self, context):
        dropdown_item = self.preserve_texture_mask_dropdown
        items = self.get_texture_masks(context)

        index = next(
            (i for i, item in enumerate(items) if item[0] == dropdown_item), None
        )
        self.preserve_texture_mask_index = index

    #
    def get_texture_masks(self, context):
        scene = context.scene

        if hasattr(scene, "mask_list"):
            mask_list = scene.mask_list

            dropdown_options = [
                (mask.name.upper(), mask.name, mask.name) for mask in mask_list
            ]
            dropdown_options.insert(0, ("NONE", "None", "None"))
        else:
            dropdown_options = [("NONE", "None", "None")]

        return dropdown_options

    retexture_prompt: StringProperty(
        name="",
        default=prompt_placeholders["Retexture"],
        update=lambda self, context: self.on_update_prompt(context),
        options={"TEXTEDIT_UPDATE"},
    )
    retexture_structure_strength: FloatProperty(name="", default=50, min=0, max=100)
    preserve_texture_mask_dropdown: EnumProperty(
        name="",
        items=get_texture_masks,
        update=lambda self, context: self.on_update_preserve_texture_mask(context),
    )
    preserve_texture_mask_index: IntProperty(name="", default=0)


#
class MaskProperties(PropertyGroup):
    #
    def update_mask_name(self, context):
        masks = context.scene.mask_list
        mask_index = context.scene.mask_list_index

        masks[mask_index].name = self.mask_name

    # Return a list of the available objects in the scene
    def update_object_dropdown(self, context):
        set_visible_objects(context)
        items = [(obj.name, obj.name, "") for obj in visible_objects]

        # None option
        items.insert(0, ("NONE", "Select an object from the scene", ""))

        # Objects currently in masks
        object_names = [tup for obj_list in mask_objects.values() for tup in obj_list]

        items = [item for item in items if item[0] not in object_names]

        # More than one option available
        if len(items) > 1:
            # Add all option
            items.insert(1, ("ADDALL", "Add All", ""))

        # Background not part of any mask
        if "Background" not in object_names:
            # Background option
            items.insert(1, ("BACKGROUND", "Background", ""))

        return items

    def get_prompt_styles(self, context):
        enum_items = []
        for i, style in enumerate(prompt_styles):
            id, name, desc, icon = style
            if icon:
                enum_items.append((id, name, desc, get_style_icon(icon), i))
            else:
                enum_items.append((id, name, desc))

        return enum_items

    mask_name: StringProperty(
        name="", update=lambda self, context: self.update_mask_name(context)
    )
    mask_objects: CollectionProperty(type=MaskObjectListItem, name="")
    object_list_index: IntProperty(name="", default=-1)
    mask_prompt: StringProperty(name="", default=prompt_placeholders["Mask"])
    mask_isolate: FloatProperty(name="", default=50, min=0, max=100)
    mask_style: EnumProperty(
        name="",
        items=get_prompt_styles,
    )
    object_dropdown: EnumProperty(
        name="",
        items=update_object_dropdown,
    )


# Properties under the 'Style Transfer' panel
class StyleProperties(PropertyGroup):
    def on_update_image(self, context):
        context.scene.flag_properties.style_flag = self.style_image != None

    style_image: StringProperty(
        name="",
        subtype="FILE_PATH",
        update=lambda self, context: self.on_update_image(context),
    )
    style_strength: FloatProperty(name="", default=50, min=0, max=100)


# Properties under the 'Relight' panel
class RelightProperties(PropertyGroup):
    def on_update_image(self, context):
        context.scene.flag_properties.relight_flag = self.relight_image

    def on_update_prompt(self, context):
        if not self.relight_prompt:
            self.relight_prompt = "Describe the lighting..."
            context.scene.flag_properties.relight_flag = False
        else:
            context.scene.flag_properties.relight_flag = True

    def on_update_angle(self, context):
        context.scene.flag_properties.relight_flag = self.relight_angle != "TOPLEFT"

    def update_type(self, context):
        context.scene.is_relight_image = self.relight_type == "IMAGE"

    relight_type: EnumProperty(
        name="Type",
        items=[("IMAGE", "Image", ""), ("COLOR", "Color", "")],
        update=lambda self, context: self.update_type(context),
    )
    relight_image: StringProperty(
        name="",
        subtype="FILE_PATH",
        maxlen=1024,
        update=lambda self, context: self.on_update_image(context),
    )
    relight_color: FloatVectorProperty(
        name="", subtype="COLOR", default=(1, 1, 1, 1), size=4
    )
    relight_prompt: StringProperty(
        name="",
        default="Describe the lighting...",
        update=lambda self, context: self.on_update_prompt(context),
    )
    relight_angle: EnumProperty(
        name="",
        items=angle_options,
        update=lambda self, context: self.on_update_angle(context),
    )
    relight_strength: FloatProperty(name="", default=50, min=0, max=100)


# Properties under the 'Upscale' panel
class UpscaleProperties(PropertyGroup):
    def on_update_scale(self, context):
        context.scene.flag_properties.upscale_flag = self.upscale_value != "1"

    def get_prompt_styles(self, context):
        # Enum items should have an icon if provided
        enum_items = [
            (id, name, desc, get_style_icon(icon), i) if icon else (id, name, desc)
            for i, (id, name, desc, icon) in enumerate(prompt_styles)
        ]

        return enum_items

    upscale_model: EnumProperty(name="", items=get_prompt_styles)
    upscale_value: EnumProperty(
        name="",
        items=upscale_options,
        update=lambda self, context: self.on_update_scale(context),
    )
    upscale_creativity: FloatProperty(name="", default=50, min=0, max=100)
    upscale_prompt: StringProperty(name="", default="Describe the prompt...")


# Flags to keep track if the properties were modified
class FlagProperties(PropertyGroup):
    retexture_flag: BoolProperty(name="", default=False)
    style_flag: BoolProperty(name="", default=False)
    relight_flag: BoolProperty(name="", default=False)
    upscale_flag: BoolProperty(name="", default=False)


#
def get_user_credits() -> int:
    user_props = bpy.context.scene.user_properties

    if user_props:
        return user_props.user_credits

    # -1 is reserved for unlimited credits
    return -2


#
def set_user_credits(credits: int) -> None:
    user_props = bpy.context.scene.user_properties

    if user_props:
        user_props.user_credits = credits


#
def reset_properties():
    # Reset properties
    scene = bpy.context.scene

    global_properties = scene.global_properties
    global_properties.global_workflow = "RETEXTURE"
    global_properties.global_model = "STABLE"
    global_properties.global_style = "PHOTOREAL"

    retexture_properties = scene.retexture_properties
    retexture_properties.retexture_prompt = ""
    retexture_properties.retexture_structure_strength = 50
    retexture_properties.preserve_texture_mask_dropdown = "NONE"
    retexture_properties.preserve_texture_mask_index = 0

    scene.error_message = ""

    for i in range(NUM_MASKS_ALLOWED):
        mask_props = getattr(scene, f"mask_properties{i + 1}")
        mask_props.mask_objects.clear()
        mask_props.mask_prompt = prompt_placeholders["Mask"]


classes = [
    UserProperties,
    GlobalProperties,
    RetextureProperties,
    MaskProperties,
    StyleProperties,
    RelightProperties,
    UpscaleProperties,
    FlagProperties,
]


def register():
    for cls in classes:
        register_class(cls)

    Scene.user_properties = PointerProperty(type=UserProperties)
    Scene.global_properties = PointerProperty(type=GlobalProperties)
    Scene.retexture_properties = PointerProperty(type=RetextureProperties)
    Scene.style_properties = PointerProperty(type=StyleProperties)
    Scene.relight_properties = PointerProperty(type=RelightProperties)
    Scene.upscale_properties = PointerProperty(type=UpscaleProperties)
    Scene.flag_properties = PointerProperty(type=FlagProperties)
    Scene.error_message = StringProperty(default="")
    Scene.show_retexture_panel = BoolProperty(default=True)
    Scene.show_object_dropdown = BoolProperty(default=False)

    for i in range(NUM_MASKS_ALLOWED):
        setattr(
            Scene,
            f"mask_properties{i + 1}",
            PointerProperty(type=MaskProperties),
        )


def unregister():
    reset_properties()

    for cls in classes:
        unregister_class(cls)

    del Scene.user_properties
    del Scene.global_properties
    del Scene.retexture_properties
    del Scene.style_properties
    del Scene.relight_properties
    del Scene.upscale_properties
    del Scene.flag_properties
    del Scene.error_message
    del Scene.show_retexture_panel
    del Scene.show_object_dropdown

    for i in range(NUM_MASKS_ALLOWED):
        delattr(Scene, f"mask_properties{i + 1}")
