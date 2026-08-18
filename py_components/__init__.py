"""Discord Components V2 for discord.py — lightweight helper library."""

from .enums import (
    ButtonStyle,
    ComponentType,
    IS_COMPONENTS_V2,
    SeparatorSpacing,
    TextInputStyle,
)
from .components import (
    ActionRow,
    Button,
    ChannelSelect,
    Component,
    Container,
    File,
    MediaGallery,
    MediaGalleryItem,
    MentionableSelect,
    RoleSelect,
    Section,
    SelectOption,
    Separator,
    StringSelect,
    Text,
    TextDisplay,
    Thumbnail,
    UserSelect,
)
from .ui import UI, send_ui
from .view import View, button
from .registry import Registry, default_registry
from .http import send_message, edit_message, respond_interaction

__version__ = "1.0.0"
__all__ = [
    # enums
    "ButtonStyle",
    "ComponentType",
    "IS_COMPONENTS_V2",
    "SeparatorSpacing",
    "TextInputStyle",
    # components
    "ActionRow",
    "Button",
    "ChannelSelect",
    "Component",
    "Container",
    "File",
    "MediaGallery",
    "MediaGalleryItem",
    "MentionableSelect",
    "RoleSelect",
    "Section",
    "SelectOption",
    "Separator",
    "StringSelect",
    "Text",
    "TextDisplay",
    "Thumbnail",
    "UserSelect",
    # high-level
    "UI",
    "send_ui",
    "View",
    "button",
    "Registry",
    "default_registry",
    # HTTP
    "send_message",
    "edit_message",
    "respond_interaction",
]
