"""Discord Components V2 component classes."""

from __future__ import annotations

from typing import Any, Optional, Sequence, Union

from .enums import (
    ButtonStyle,
    ComponentType,
    SeparatorSpacing,
)


class Component:
    """Base class for all components."""

    type: ComponentType

    def __init__(self, id: Optional[int] = None):
        self.id = id

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"type": int(self.type)}
        if self.id is not None:
            data["id"] = self.id
        return data
        
class TextDisplay(Component):
    """Markdown text block (type 10).

    Supports standard Discord markdown. Mentions respect message allowed_mentions.
    """

    type = ComponentType.TEXT_DISPLAY

    def __init__(self, content: str, *, id: Optional[int] = None):
        super().__init__(id=id)
        if not content or len(content) > 4000:
            raise ValueError("TextDisplay content must be 1-4000 characters")
        self.content = content

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["content"] = self.content
        return data


# backwards-compatible alias used in original library
Text = TextDisplay


class Thumbnail(Component):
    """Small image used as a Section accessory (type 11).

    Only images (including GIF/WEBP) are supported.
    """

    type = ComponentType.THUMBNAIL

    def __init__(
        self,
        url: str,
        *,
        description: Optional[str] = None,
        spoiler: bool = False,
        id: Optional[int] = None,
    ):
        super().__init__(id=id)
        self.url = url
        self.description = description
        self.spoiler = spoiler

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["media"] = {"url": self.url}
        if self.description is not None:
            data["description"] = self.description
        if self.spoiler:
            data["spoiler"] = True
        return data


class MediaGalleryItem:
    """A single item inside a MediaGallery."""

    def __init__(
        self,
        url: str,
        *,
        description: Optional[str] = None,
        spoiler: bool = False,
    ):
        self.url = url
        self.description = description
        self.spoiler = spoiler

    def to_dict(self) -> dict[str, Any]:
        item: dict[str, Any] = {"media": {"url": self.url}}
        if self.description is not None:
            item["description"] = self.description
        if self.spoiler:
            item["spoiler"] = True
        return item


class MediaGallery(Component):
    """Gallery of 1-10 media items (type 12)."""

    type = ComponentType.MEDIA_GALLERY

    def __init__(
        self,
        *items: Union[MediaGalleryItem, str],
        id: Optional[int] = None,
    ):
        super().__init__(id=id)
        if not 1 <= len(items) <= 10:
            raise ValueError("MediaGallery requires 1-10 items")
        self.items: list[MediaGalleryItem] = []
        for it in items:
            if isinstance(it, str):
                self.items.append(MediaGalleryItem(it))
            else:
                self.items.append(it)

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["items"] = [i.to_dict() for i in self.items]
        return data


class File(Component):
    """Displays an attached file (type 13).

    The file must be uploaded as a message attachment and referenced
    with the attachment://filename syntax.
    """

    type = ComponentType.FILE

    def __init__(
        self,
        filename: str,
        *,
        spoiler: bool = False,
        id: Optional[int] = None,
    ):
        super().__init__(id=id)
        if filename.startswith("attachment://"):
            self.filename = filename
        else:
            self.filename = f"attachment://{filename}"
        self.spoiler = spoiler

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["file"] = {"url": self.filename}
        if self.spoiler:
            data["spoiler"] = True
        return data

class ActionRow(Component):
    """Row of up to 5 buttons or a single select menu (type 1)."""

    type = ComponentType.ACTION_ROW

    def __init__(
        self,
        *components: Component,
        id: Optional[int] = None,
    ):
        super().__init__(id=id)
        if len(components) > 5:
            raise ValueError("ActionRow can contain at most 5 components")
        self.components = list(components)

    def add(self, component: Component) -> "ActionRow":
        if len(self.components) >= 5:
            raise ValueError("ActionRow already has 5 components")
        self.components.append(component)
        return self

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["components"] = [c.to_dict() for c in self.components]
        return data


class Section(Component):
    """Text content (1-3 TextDisplays) alongside an accessory (type 9).

    Accessory may be a Button or a Thumbnail.
    """

    type = ComponentType.SECTION

    def __init__(
        self,
        *text_components: TextDisplay,
        accessory: Optional[Union["Button", Thumbnail]] = None,
        id: Optional[int] = None,
    ):
        super().__init__(id=id)
        if not 1 <= len(text_components) <= 3:
            raise ValueError("Section requires 1-3 TextDisplay children")
        self.components = list(text_components)
        self.accessory = accessory

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["components"] = [c.to_dict() for c in self.components]
        if self.accessory is not None:
            data["accessory"] = self.accessory.to_dict()
        return data


class Separator(Component):
    """Vertical padding / divider between components (type 14)."""

    type = ComponentType.SEPARATOR

    def __init__(
        self,
        *,
        divider: bool = True,
        spacing: SeparatorSpacing = SeparatorSpacing.SMALL,
        id: Optional[int] = None,
    ):
        super().__init__(id=id)
        self.divider = divider
        self.spacing = spacing

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["divider"] = self.divider
        data["spacing"] = int(self.spacing)
        return data


class Container(Component):
    """Visually groups child components with optional accent colour (type 17).

    Allowed children: ActionRow, TextDisplay, Section, MediaGallery,
    Separator, File.
    """

    type = ComponentType.CONTAINER

    def __init__(
        self,
        *components: Component,
        accent_color: Optional[int] = None,
        spoiler: bool = False,
        id: Optional[int] = None,
    ):
        super().__init__(id=id)
        self.components = list(components)
        self.accent_color = accent_color
        self.spoiler = spoiler

    def add(self, component: Component) -> "Container":
        self.components.append(component)
        return self

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["components"] = [c.to_dict() for c in self.components]
        if self.accent_color is not None:
            data["accent_color"] = self.accent_color
        if self.spoiler:
            data["spoiler"] = True
        return data


class Button(Component):
    """Clickable button (type 2).

    Must live inside an ActionRow or as a Section accessory.
    Non-link / non-premium buttons require a custom_id.
    """

    type = ComponentType.BUTTON

    def __init__(
        self,
        label: Optional[str] = None,
        *,
        custom_id: Optional[str] = None,
        style: ButtonStyle = ButtonStyle.PRIMARY,
        url: Optional[str] = None,
        sku_id: Optional[str] = None,
        emoji: Optional[dict[str, Any]] = None,
        disabled: bool = False,
        id: Optional[int] = None,
    ):
        super().__init__(id=id)
        style = ButtonStyle(style)

        if style == ButtonStyle.LINK:
            if not url:
                raise ValueError("LINK buttons require a url")
            if custom_id:
                raise ValueError("LINK buttons cannot have a custom_id")
        elif style == ButtonStyle.PREMIUM:
            if not sku_id:
                raise ValueError("PREMIUM buttons require a sku_id")
        else:
            if not custom_id:
                raise ValueError("Non-link buttons require a custom_id")
            if url:
                raise ValueError("Only LINK buttons may have a url")

        if label is not None and len(label) > 80:
            raise ValueError("Button label max length is 80 characters")
        if custom_id is not None and not 1 <= len(custom_id) <= 100:
            raise ValueError("custom_id must be 1-100 characters")

        self.label = label
        self.custom_id = custom_id
        self.style = style
        self.url = url
        self.sku_id = sku_id
        self.emoji = emoji
        self.disabled = disabled

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["style"] = int(self.style)
        if self.label is not None:
            data["label"] = self.label
        if self.custom_id is not None:
            data["custom_id"] = self.custom_id
        if self.url is not None:
            data["url"] = self.url
        if self.sku_id is not None:
            data["sku_id"] = self.sku_id
        if self.emoji is not None:
            data["emoji"] = self.emoji
        if self.disabled:
            data["disabled"] = True
        return data


class SelectOption:
    """Option for a StringSelect menu."""

    def __init__(
        self,
        label: str,
        value: str,
        *,
        description: Optional[str] = None,
        emoji: Optional[dict[str, Any]] = None,
        default: bool = False,
    ):
        if len(label) > 100 or len(value) > 100:
            raise ValueError("label and value max length is 100")
        self.label = label
        self.value = value
        self.description = description
        self.emoji = emoji
        self.default = default

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "label": self.label,
            "value": self.value,
        }
        if self.description is not None:
            data["description"] = self.description
        if self.emoji is not None:
            data["emoji"] = self.emoji
        if self.default:
            data["default"] = True
        return data


class StringSelect(Component):
    """Dropdown for choosing from predefined string options (type 3)."""

    type = ComponentType.STRING_SELECT

    def __init__(
        self,
        custom_id: str,
        options: Sequence[SelectOption],
        *,
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        id: Optional[int] = None,
    ):
        super().__init__(id=id)
        if not 1 <= len(custom_id) <= 100:
            raise ValueError("custom_id must be 1-100 characters")
        if not 1 <= len(options) <= 25:
            raise ValueError("StringSelect requires 1-25 options")
        self.custom_id = custom_id
        self.options = list(options)
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values
        self.disabled = disabled

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["custom_id"] = self.custom_id
        data["options"] = [o.to_dict() for o in self.options]
        if self.placeholder is not None:
            data["placeholder"] = self.placeholder
        data["min_values"] = self.min_values
        data["max_values"] = self.max_values
        if self.disabled:
            data["disabled"] = True
        return data


class UserSelect(Component):
    """Select menu for users (type 5)."""

    type = ComponentType.USER_SELECT

    def __init__(
        self,
        custom_id: str,
        *,
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        id: Optional[int] = None,
    ):
        super().__init__(id=id)
        self.custom_id = custom_id
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values
        self.disabled = disabled

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["custom_id"] = self.custom_id
        if self.placeholder is not None:
            data["placeholder"] = self.placeholder
        data["min_values"] = self.min_values
        data["max_values"] = self.max_values
        if self.disabled:
            data["disabled"] = True
        return data


class RoleSelect(Component):
    """Select menu for roles (type 6)."""

    type = ComponentType.ROLE_SELECT

    def __init__(
        self,
        custom_id: str,
        *,
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        id: Optional[int] = None,
    ):
        super().__init__(id=id)
        self.custom_id = custom_id
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values
        self.disabled = disabled

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["custom_id"] = self.custom_id
        if self.placeholder is not None:
            data["placeholder"] = self.placeholder
        data["min_values"] = self.min_values
        data["max_values"] = self.max_values
        if self.disabled:
            data["disabled"] = True
        return data


class MentionableSelect(Component):
    """Select menu for users and roles (type 7)."""

    type = ComponentType.MENTIONABLE_SELECT

    def __init__(
        self,
        custom_id: str,
        *,
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        id: Optional[int] = None,
    ):
        super().__init__(id=id)
        self.custom_id = custom_id
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values
        self.disabled = disabled

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["custom_id"] = self.custom_id
        if self.placeholder is not None:
            data["placeholder"] = self.placeholder
        data["min_values"] = self.min_values
        data["max_values"] = self.max_values
        if self.disabled:
            data["disabled"] = True
        return data


class ChannelSelect(Component):
    """Select menu for channels (type 8)."""

    type = ComponentType.CHANNEL_SELECT

    def __init__(
        self,
        custom_id: str,
        *,
        channel_types: Optional[Sequence[int]] = None,
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        id: Optional[int] = None,
    ):
        super().__init__(id=id)
        self.custom_id = custom_id
        self.channel_types = list(channel_types) if channel_types else None
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values
        self.disabled = disabled

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["custom_id"] = self.custom_id
        if self.channel_types is not None:
            data["channel_types"] = self.channel_types
        if self.placeholder is not None:
            data["placeholder"] = self.placeholder
        data["min_values"] = self.min_values
        data["max_values"] = self.max_values
        if self.disabled:
            data["disabled"] = True
        return data
