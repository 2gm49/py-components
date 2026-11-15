"""Discord Components V2 component classes."""

from __future__ import annotations

import warnings
from typing import Any, ClassVar, Iterator, Optional, Sequence, Union

from .enums import (
    ButtonStyle,
    ChannelType,
    ComponentType,
    SeparatorSpacing,
    TextInputStyle,
)

_REGISTRY: dict[int, type["Component"]] = {}


def _check_custom_id(custom_id: Optional[str]) -> None:
    if not isinstance(custom_id, str) or not 1 <= len(custom_id) <= 100:
        raise ValueError("custom_id must be 1-100 characters")


def _check_max(name: str, value: Optional[str], maximum: int) -> None:
    if value is not None and len(value) > maximum:
        raise ValueError(f"{name} max length is {maximum}")


def make_emoji(
    name: str,
    *,
    id: Optional[str | int] = None,
    animated: bool = False,
) -> dict[str, Any]:
    """Partial emoji object. Unicode: make_emoji("🔥"). Custom: make_emoji("name", id=...)."""
    data: dict[str, Any] = {"name": name}
    if id is not None:
        data["id"] = str(id)
        data["animated"] = animated
    return data


def _emoji(value: Any) -> Optional[dict[str, Any]]:
    if value is None or isinstance(value, dict):
        return value
    if isinstance(value, str):
        if value.startswith("<") and value.endswith(">") and value.count(":") == 2:
            animated, name, eid = value[1:-1].split(":")
            return make_emoji(name, id=eid, animated=animated == "a")
        return make_emoji(value)
    name = getattr(value, "name", None)
    if name is not None:
        eid = getattr(value, "id", None)
        return make_emoji(name, id=eid, animated=bool(getattr(value, "animated", False)))
    raise TypeError("emoji must be a str, dict or emoji object")


def _colour(value: Any) -> Optional[int]:
    if value is None:
        return None
    if not isinstance(value, int):
        value = getattr(value, "value", value)
    if not isinstance(value, int) or not 0 <= value <= 0xFFFFFF:
        raise ValueError("accent_color must be an int between 0x000000 and 0xFFFFFF")
    return value


def _media_url(data: dict[str, Any], key: str = "media") -> str:
    media = data.get(key) or {}
    return media.get("url", "")


class Component:
    """Base component."""

    type: ClassVar[ComponentType]

    def __init__(self, id: Optional[int] = None):
        if id is not None and (not isinstance(id, int) or not 0 <= id <= 2_147_483_647):
            raise ValueError("id must be a 32-bit positive integer")
        self.id = id

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        t = cls.__dict__.get("type")
        if isinstance(t, ComponentType):
            _REGISTRY[int(t)] = cls

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"type": int(self.type)}
        if self.id is not None:
            data["id"] = self.id
        return data

    def children(self) -> list["Component"]:
        return []

    def walk(self) -> Iterator["Component"]:
        """Yield this component and everything nested inside it."""
        yield self
        for child in self.children():
            yield from child.walk()

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Component":
        """Build the right component class from a raw payload dict."""
        return component_from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "Component":
        raise NotImplementedError

    def __repr__(self) -> str:
        fields = ", ".join(f"{k}={v!r}" for k, v in vars(self).items() if v not in (None, [], False))
        return f"{type(self).__name__}({fields})"


class UnknownComponent(Component):
    """A component type this library doesn't know yet. Keeps the raw payload."""

    def __init__(self, data: dict[str, Any]):
        super().__init__(id=data.get("id"))
        self.raw = dict(data)

    @property
    def type(self) -> int:
        return self.raw.get("type", 0)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.raw)


def component_from_dict(data: dict[str, Any]) -> Component:
    """Turn a raw component dict (from a message or interaction) into a component object."""
    cls = _REGISTRY.get(data.get("type"))
    if cls is None:
        return UnknownComponent(data)
    return cls._from_dict(data)


def components_from_dicts(data: Sequence[dict[str, Any]]) -> list[Component]:
    return [component_from_dict(d) for d in data]


class TextDisplay(Component):
    """Markdown text (type 10)."""

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

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "TextDisplay":
        return cls(data.get("content") or " ", id=data.get("id"))


Text = TextDisplay


class Thumbnail(Component):
    """Section accessory image (type 11). Images only, including gif and webp."""

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
        if not url:
            raise ValueError("Thumbnail needs a url")
        _check_max("Thumbnail description", description, 1024)
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

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "Thumbnail":
        return cls(_media_url(data), description=data.get("description"),
                   spoiler=bool(data.get("spoiler")), id=data.get("id"))


class MediaGalleryItem:
    """One item in a MediaGallery."""

    def __init__(
        self,
        url: str,
        *,
        description: Optional[str] = None,
        spoiler: bool = False,
    ):
        if not url:
            raise ValueError("MediaGalleryItem needs a url")
        _check_max("MediaGalleryItem description", description, 1024)
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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MediaGalleryItem":
        return cls(_media_url(data), description=data.get("description"), spoiler=bool(data.get("spoiler")))

    def __repr__(self) -> str:
        return f"MediaGalleryItem(url={self.url!r})"


class MediaGallery(Component):
    """1-10 images or videos (type 12)."""

    type = ComponentType.MEDIA_GALLERY

    def __init__(
        self,
        *items: Union[MediaGalleryItem, str],
        id: Optional[int] = None,
    ):
        super().__init__(id=id)
        if not 1 <= len(items) <= 10:
            raise ValueError("MediaGallery requires 1-10 items")
        self.items: list[MediaGalleryItem] = [
            MediaGalleryItem(it) if isinstance(it, str) else it for it in items
        ]

    def add(self, item: Union[MediaGalleryItem, str]) -> "MediaGallery":
        if len(self.items) >= 10:
            raise ValueError("MediaGallery already has 10 items")
        self.items.append(MediaGalleryItem(item) if isinstance(item, str) else item)
        return self

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["items"] = [i.to_dict() for i in self.items]
        return data

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "MediaGallery":
        items = [MediaGalleryItem.from_dict(i) for i in data.get("items", [])]
        return cls(*items, id=data.get("id"))


class File(Component):
    """Attached file shown through attachment:// (type 13)."""

    type = ComponentType.FILE

    def __init__(
        self,
        filename: str,
        *,
        spoiler: bool = False,
        id: Optional[int] = None,
    ):
        super().__init__(id=id)
        if not filename:
            raise ValueError("File needs a filename")
        self.filename = filename if filename.startswith("attachment://") else f"attachment://{filename}"
        self.spoiler = spoiler
        self.name: Optional[str] = None
        self.size: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["file"] = {"url": self.filename}
        if self.spoiler:
            data["spoiler"] = True
        return data

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "File":
        url = _media_url(data, "file") or f"attachment://{data.get('name') or 'file'}"
        obj = cls(url, spoiler=bool(data.get("spoiler")), id=data.get("id"))
        obj.name = data.get("name")
        obj.size = data.get("size")
        return obj


class ActionRow(Component):
    """Up to 5 buttons, or exactly one select (type 1)."""

    type = ComponentType.ACTION_ROW

    def __init__(
        self,
        *components: Component,
        id: Optional[int] = None,
    ):
        super().__init__(id=id)
        self.components: list[Component] = []
        for c in components:
            self.add(c)

    def add(self, component: Component) -> "ActionRow":
        current = self.components + [component]
        if any(isinstance(c, (BaseSelect, TextInput)) for c in current):
            if len(current) > 1:
                raise ValueError("an ActionRow with a select or text input can't hold anything else")
        elif not all(isinstance(c, (Button, UnknownComponent)) for c in current):
            raise ValueError("ActionRow can only hold Buttons or one select")
        elif len(current) > 5:
            raise ValueError("ActionRow can contain at most 5 buttons")
        self.components.append(component)
        return self

    def children(self) -> list[Component]:
        return list(self.components)

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["components"] = [c.to_dict() for c in self.components]
        return data

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "ActionRow":
        row = cls(id=data.get("id"))
        row.components = components_from_dicts(data.get("components", []))
        return row


class Section(Component):
    """1-3 TextDisplays with a Button or Thumbnail on the side (type 9)."""

    type = ComponentType.SECTION

    def __init__(
        self,
        *text_components: Union[TextDisplay, str],
        accessory: Optional[Union["Button", Thumbnail]] = None,
        id: Optional[int] = None,
    ):
        super().__init__(id=id)
        if not 1 <= len(text_components) <= 3:
            raise ValueError("Section requires 1-3 TextDisplay children")
        self.components: list[Component] = [
            TextDisplay(t) if isinstance(t, str) else t for t in text_components
        ]
        if not all(isinstance(c, (TextDisplay, UnknownComponent)) for c in self.components):
            raise ValueError("Section children must be TextDisplays")
        if accessory is not None and not isinstance(accessory, (Button, Thumbnail, UnknownComponent)):
            raise ValueError("Section accessory must be a Button or Thumbnail")
        self.accessory = accessory

    def children(self) -> list[Component]:
        return self.components + ([self.accessory] if self.accessory is not None else [])

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["components"] = [c.to_dict() for c in self.components]
        if self.accessory is not None:
            data["accessory"] = self.accessory.to_dict()
        return data

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "Section":
        texts = components_from_dicts(data.get("components", [])) or [TextDisplay(" ")]
        accessory = component_from_dict(data["accessory"]) if data.get("accessory") else None
        obj = cls(TextDisplay(" "), id=data.get("id"))
        obj.components = texts
        obj.accessory = accessory
        return obj


class Separator(Component):
    """Space or a divider line between components (type 14)."""

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
        self.spacing = SeparatorSpacing(spacing)

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["divider"] = self.divider
        data["spacing"] = int(self.spacing)
        return data

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "Separator":
        return cls(divider=data.get("divider", True), spacing=data.get("spacing", 1), id=data.get("id"))


class Container(Component):
    """Box around other components, with an optional accent colour (type 17)."""

    type = ComponentType.CONTAINER

    def __init__(
        self,
        *components: Component,
        accent_color: Any = None,
        spoiler: bool = False,
        id: Optional[int] = None,
        accent_colour: Any = None,
    ):
        super().__init__(id=id)
        self.components: list[Component] = []
        for c in components:
            self.add(c)
        self.accent_color = _colour(accent_color if accent_color is not None else accent_colour)
        self.spoiler = spoiler

    def add(self, *components: Component) -> "Container":
        for component in components:
            if not isinstance(component, (ActionRow, TextDisplay, Section, MediaGallery, Separator, File, UnknownComponent)):
                raise ValueError(
                    "Container children must be ActionRow, TextDisplay, Section, MediaGallery, Separator or File"
                )
            self.components.append(component)
        return self

    def children(self) -> list[Component]:
        return list(self.components)

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["components"] = [c.to_dict() for c in self.components]
        if self.accent_color is not None:
            data["accent_color"] = self.accent_color
        if self.spoiler:
            data["spoiler"] = True
        return data

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "Container":
        obj = cls(accent_color=data.get("accent_color"), spoiler=bool(data.get("spoiler")), id=data.get("id"))
        obj.components = components_from_dicts(data.get("components", []))
        return obj


class Button(Component):
    """Button (type 2). Needs custom_id unless it's a LINK or PREMIUM button."""

    type = ComponentType.BUTTON

    def __init__(
        self,
        label: Optional[str] = None,
        *,
        custom_id: Optional[str] = None,
        style: ButtonStyle = ButtonStyle.PRIMARY,
        url: Optional[str] = None,
        sku_id: Optional[str | int] = None,
        emoji: Any = None,
        disabled: bool = False,
        id: Optional[int] = None,
    ):
        super().__init__(id=id)
        style = ButtonStyle(style)

        if style == ButtonStyle.LINK:
            if not url:
                raise ValueError("LINK buttons require a url")
            if custom_id or sku_id:
                raise ValueError("LINK buttons can't have a custom_id or sku_id")
            _check_max("Button url", url, 512)
        elif style == ButtonStyle.PREMIUM:
            if not sku_id:
                raise ValueError("PREMIUM buttons require a sku_id")
            if custom_id or url or label or emoji:
                raise ValueError("PREMIUM buttons can't have a custom_id, url, label or emoji")
        else:
            _check_custom_id(custom_id)
            if url or sku_id:
                raise ValueError("only LINK buttons can have a url, and only PREMIUM buttons a sku_id")

        if style != ButtonStyle.PREMIUM and label is None and emoji is None:
            raise ValueError("Button needs a label or an emoji")
        _check_max("Button label", label, 80)

        self.label = label
        self.custom_id = custom_id
        self.style = style
        self.url = url
        self.sku_id = str(sku_id) if sku_id is not None else None
        self.emoji = _emoji(emoji)
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

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "Button":
        obj = cls.__new__(cls)
        Component.__init__(obj, id=data.get("id"))
        obj.label = data.get("label")
        obj.custom_id = data.get("custom_id")
        obj.style = ButtonStyle(data.get("style", 1))
        obj.url = data.get("url")
        obj.sku_id = data.get("sku_id")
        obj.emoji = data.get("emoji")
        obj.disabled = bool(data.get("disabled"))
        return obj


class SelectOption:
    """Option for a StringSelect."""

    def __init__(
        self,
        label: str,
        value: Optional[str] = None,
        *,
        description: Optional[str] = None,
        emoji: Any = None,
        default: bool = False,
    ):
        value = label if value is None else value
        if not label or not value:
            raise ValueError("SelectOption needs a label and value")
        _check_max("SelectOption label", label, 100)
        _check_max("SelectOption value", value, 100)
        _check_max("SelectOption description", description, 100)
        self.label = label
        self.value = value
        self.description = description
        self.emoji = _emoji(emoji)
        self.default = default

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"label": self.label, "value": self.value}
        if self.description is not None:
            data["description"] = self.description
        if self.emoji is not None:
            data["emoji"] = self.emoji
        if self.default:
            data["default"] = True
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SelectOption":
        return cls(data["label"], data["value"], description=data.get("description"),
                   emoji=data.get("emoji"), default=bool(data.get("default")))

    def __repr__(self) -> str:
        return f"SelectOption(label={self.label!r}, value={self.value!r})"


class SelectDefaultValue:
    """Pre-selected value for a User, Role, Mentionable or Channel select."""

    TYPES = ("user", "role", "channel")

    def __init__(self, id: str | int, type: str):
        if type not in self.TYPES:
            raise ValueError("SelectDefaultValue type must be 'user', 'role' or 'channel'")
        self.id = str(id)
        self.type = type

    @classmethod
    def user(cls, id: Any) -> "SelectDefaultValue":
        return cls(getattr(id, "id", id), "user")

    @classmethod
    def role(cls, id: Any) -> "SelectDefaultValue":
        return cls(getattr(id, "id", id), "role")

    @classmethod
    def channel(cls, id: Any) -> "SelectDefaultValue":
        return cls(getattr(id, "id", id), "channel")

    def to_dict(self) -> dict[str, str]:
        return {"id": self.id, "type": self.type}

    def __repr__(self) -> str:
        return f"SelectDefaultValue(id={self.id!r}, type={self.type!r})"


def _guess_kind(value: Any) -> Optional[str]:
    name = type(value).__name__
    if name in ("User", "Member", "ClientUser"):
        return "user"
    if name == "Role":
        return "role"
    if hasattr(value, "id") and ("Channel" in name or name == "Thread"):
        return "channel"
    return None


class BaseSelect(Component):
    """Shared fields for every select menu."""

    def __init__(
        self,
        custom_id: str,
        *,
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        required: Optional[bool] = None,
        id: Optional[int] = None,
    ):
        super().__init__(id=id)
        _check_custom_id(custom_id)
        _check_max("placeholder", placeholder, 150)
        if not 0 <= min_values <= 25:
            raise ValueError("min_values must be 0-25")
        if not 1 <= max_values <= 25:
            raise ValueError("max_values must be 1-25")
        if min_values > max_values:
            raise ValueError("min_values can't be more than max_values")
        if required is True and min_values < 1:
            raise ValueError("min_values must be at least 1 when required is True")
        self.custom_id = custom_id
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values
        self.disabled = disabled
        self.required = required

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["custom_id"] = self.custom_id
        if self.placeholder is not None:
            data["placeholder"] = self.placeholder
        data["min_values"] = self.min_values
        data["max_values"] = self.max_values
        if self.disabled:
            data["disabled"] = True
        if self.required is not None:
            data["required"] = self.required
        return data

    @staticmethod
    def _common(data: dict[str, Any]) -> dict[str, Any]:
        return {
            "placeholder": data.get("placeholder"),
            "min_values": data.get("min_values", 1),
            "max_values": data.get("max_values", 1),
            "disabled": bool(data.get("disabled")),
            "required": data.get("required"),
            "id": data.get("id"),
        }


class StringSelect(BaseSelect):
    """Dropdown of your own options (type 3)."""

    type = ComponentType.STRING_SELECT

    def __init__(
        self,
        custom_id: str,
        options: Sequence[Union[SelectOption, str]],
        *,
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        required: Optional[bool] = None,
        id: Optional[int] = None,
    ):
        super().__init__(custom_id, placeholder=placeholder, min_values=min_values, max_values=max_values,
                         disabled=disabled, required=required, id=id)
        if not 1 <= len(options) <= 25:
            raise ValueError("StringSelect requires 1-25 options")
        self.options = [SelectOption(o) if isinstance(o, str) else o for o in options]
        if max_values > len(self.options):
            raise ValueError("max_values can't be more than the number of options")
        if len({o.value for o in self.options}) != len(self.options):
            raise ValueError("StringSelect option values must be unique")

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["options"] = [o.to_dict() for o in self.options]
        return data

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "StringSelect":
        options = [SelectOption.from_dict(o) for o in data.get("options", [])]
        return cls(data["custom_id"], options, **cls._common(data))


class _EntitySelect(BaseSelect):
    allowed_types: ClassVar[tuple[str, ...]] = ()

    def __init__(
        self,
        custom_id: str,
        *,
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        required: Optional[bool] = None,
        default_values: Optional[Sequence[Any]] = None,
        id: Optional[int] = None,
    ):
        super().__init__(custom_id, placeholder=placeholder, min_values=min_values, max_values=max_values,
                         disabled=disabled, required=required, id=id)
        self.default_values = [self._default(v) for v in default_values] if default_values else None
        if self.default_values is not None and not min_values <= len(self.default_values) <= max_values:
            raise ValueError("the number of default_values must be between min_values and max_values")

    def _default(self, value: Any) -> SelectDefaultValue:
        if isinstance(value, SelectDefaultValue):
            dv = value
        elif isinstance(value, dict):
            dv = SelectDefaultValue(value["id"], value["type"])
        else:
            kind = _guess_kind(value)
            if kind is None:
                if len(self.allowed_types) != 1:
                    raise ValueError(
                        f"{type(self).__name__} default_values need a type: use SelectDefaultValue.user/role"
                    )
                kind = self.allowed_types[0]
            dv = SelectDefaultValue(getattr(value, "id", value), kind)
        if dv.type not in self.allowed_types:
            raise ValueError(f"{type(self).__name__} default_values can only be {', '.join(self.allowed_types)}")
        return dv

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        if self.default_values is not None:
            data["default_values"] = [v.to_dict() for v in self.default_values]
        return data

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "_EntitySelect":
        return cls(data["custom_id"], default_values=data.get("default_values"), **cls._common(data))


class UserSelect(_EntitySelect):
    """Pick members (type 5)."""

    type = ComponentType.USER_SELECT
    allowed_types = ("user",)


class RoleSelect(_EntitySelect):
    """Pick roles (type 6)."""

    type = ComponentType.ROLE_SELECT
    allowed_types = ("role",)


class MentionableSelect(_EntitySelect):
    """Pick members and roles (type 7)."""

    type = ComponentType.MENTIONABLE_SELECT
    allowed_types = ("user", "role")


class ChannelSelect(_EntitySelect):
    """Pick channels, optionally limited to some channel types (type 8)."""

    type = ComponentType.CHANNEL_SELECT
    allowed_types = ("channel",)

    def __init__(
        self,
        custom_id: str,
        *,
        channel_types: Optional[Sequence[int | ChannelType]] = None,
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        required: Optional[bool] = None,
        default_values: Optional[Sequence[Any]] = None,
        id: Optional[int] = None,
    ):
        super().__init__(custom_id, placeholder=placeholder, min_values=min_values, max_values=max_values,
                         disabled=disabled, required=required, default_values=default_values, id=id)
        self.channel_types = [int(getattr(t, "value", t)) for t in channel_types] if channel_types else None

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        if self.channel_types is not None:
            data["channel_types"] = self.channel_types
        return data

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "ChannelSelect":
        return cls(data["custom_id"], channel_types=data.get("channel_types"),
                   default_values=data.get("default_values"), **cls._common(data))


class TextInput(Component):
    """Text field for modals (type 4). Put it inside a Label."""

    type = ComponentType.TEXT_INPUT

    def __init__(
        self,
        custom_id: str,
        *,
        style: int | TextInputStyle = TextInputStyle.SHORT,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        required: bool = True,
        value: Optional[str] = None,
        placeholder: Optional[str] = None,
        label: Optional[str] = None,
        id: Optional[int] = None,
    ):
        super().__init__(id=id)
        _check_custom_id(custom_id)
        if min_length is not None and not 0 <= min_length <= 4000:
            raise ValueError("min_length must be 0-4000")
        if max_length is not None and not 1 <= max_length <= 4000:
            raise ValueError("max_length must be 1-4000")
        if min_length is not None and max_length is not None and min_length > max_length:
            raise ValueError("min_length can't be more than max_length")
        _check_max("value", value, 4000)
        _check_max("placeholder", placeholder, 100)
        if label is not None:
            warnings.warn("TextInput(label=...) is deprecated by Discord, wrap it in a Label instead",
                          DeprecationWarning, stacklevel=2)
            _check_max("label", label, 45)
        self.custom_id = custom_id
        self.style = TextInputStyle(int(style))
        self.min_length = min_length
        self.max_length = max_length
        self.required = required
        self.value = value
        self.placeholder = placeholder
        self.label = label

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["custom_id"] = self.custom_id
        data["style"] = int(self.style)
        if self.label is not None:
            data["label"] = self.label
        if self.min_length is not None:
            data["min_length"] = self.min_length
        if self.max_length is not None:
            data["max_length"] = self.max_length
        data["required"] = self.required
        if self.value is not None:
            data["value"] = self.value
        if self.placeholder is not None:
            data["placeholder"] = self.placeholder
        return data

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "TextInput":
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            return cls(data["custom_id"], style=data.get("style", 1), min_length=data.get("min_length"),
                       max_length=data.get("max_length"), required=data.get("required", True),
                       value=data.get("value"), placeholder=data.get("placeholder"),
                       label=data.get("label"), id=data.get("id"))


class FileUpload(Component):
    """File upload for modals (type 19). Put it inside a Label."""

    type = ComponentType.FILE_UPLOAD

    FILE_TYPE_GROUPS = ("image", "video", "audio")

    def __init__(
        self,
        custom_id: str,
        *,
        min_values: int = 1,
        max_values: int = 1,
        required: bool = True,
        file_types: Optional[Sequence[str]] = None,
        id: Optional[int] = None,
    ):
        super().__init__(id=id)
        _check_custom_id(custom_id)
        if not 0 <= min_values <= 10 or not 1 <= max_values <= 10:
            raise ValueError("min_values must be 0-10 and max_values 1-10")
        if min_values > max_values:
            raise ValueError("min_values can't be more than max_values")
        if required and min_values < 1:
            raise ValueError("min_values must be at least 1 when required is True")
        if file_types is not None:
            if len(file_types) > 10:
                raise ValueError("file_types can have at most 10 entries")
            for ft in file_types:
                if ft not in self.FILE_TYPE_GROUPS and not (ft.startswith(".") and len(ft) > 1):
                    raise ValueError(f"file type {ft!r} must be image, video, audio or an extension like .pdf")
        self.custom_id = custom_id
        self.min_values = min_values
        self.max_values = max_values
        self.required = required
        self.file_types = list(file_types) if file_types else None

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["custom_id"] = self.custom_id
        data["min_values"] = self.min_values
        data["max_values"] = self.max_values
        data["required"] = self.required
        if self.file_types is not None:
            data["file_types"] = self.file_types
        return data

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "FileUpload":
        return cls(data["custom_id"], min_values=data.get("min_values", 1), max_values=data.get("max_values", 1),
                   required=data.get("required", True), file_types=data.get("file_types"), id=data.get("id"))


class GroupOption:
    """Option for a RadioGroup or CheckboxGroup."""

    def __init__(
        self,
        label: str,
        value: Optional[str] = None,
        *,
        description: Optional[str] = None,
        default: bool = False,
    ):
        value = label if value is None else value
        if not label or not value:
            raise ValueError("GroupOption needs a label and value")
        _check_max("label", label, 100)
        _check_max("value", value, 100)
        _check_max("description", description, 100)
        self.label = label
        self.value = value
        self.description = description
        self.default = default

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"label": self.label, "value": self.value}
        if self.description is not None:
            data["description"] = self.description
        if self.default:
            data["default"] = True
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GroupOption":
        return cls(data["label"], data["value"], description=data.get("description"), default=bool(data.get("default")))

    def __repr__(self) -> str:
        return f"GroupOption(label={self.label!r}, value={self.value!r})"


RadioGroupOption = GroupOption
CheckboxGroupOption = GroupOption


def _group_options(options: Sequence[Union[GroupOption, str]]) -> list[GroupOption]:
    out = [GroupOption(o) if isinstance(o, str) else o for o in options]
    if len({o.value for o in out}) != len(out):
        raise ValueError("option values must be unique")
    return out


class RadioGroup(Component):
    """Pick one option, for modals (type 21). Put it inside a Label."""

    type = ComponentType.RADIO_GROUP

    def __init__(
        self,
        custom_id: str,
        options: Sequence[Union[GroupOption, str]],
        *,
        required: bool = True,
        id: Optional[int] = None,
    ):
        super().__init__(id=id)
        _check_custom_id(custom_id)
        if not 2 <= len(options) <= 10:
            raise ValueError("RadioGroup requires 2-10 options")
        self.custom_id = custom_id
        self.options = _group_options(options)
        if sum(1 for o in self.options if o.default) > 1:
            raise ValueError("RadioGroup can only have one default option")
        self.required = required

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["custom_id"] = self.custom_id
        data["options"] = [o.to_dict() for o in self.options]
        data["required"] = self.required
        return data

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "RadioGroup":
        options = [GroupOption.from_dict(o) for o in data.get("options", [])]
        return cls(data["custom_id"], options, required=data.get("required", True), id=data.get("id"))


class CheckboxGroup(Component):
    """Pick several options, for modals (type 22). Put it inside a Label."""

    type = ComponentType.CHECKBOX_GROUP

    def __init__(
        self,
        custom_id: str,
        options: Sequence[Union[GroupOption, str]],
        *,
        min_values: int = 1,
        max_values: Optional[int] = None,
        required: bool = True,
        id: Optional[int] = None,
    ):
        super().__init__(id=id)
        _check_custom_id(custom_id)
        if not 1 <= len(options) <= 10:
            raise ValueError("CheckboxGroup requires 1-10 options")
        self.custom_id = custom_id
        self.options = _group_options(options)
        self.min_values = min_values
        self.max_values = max_values if max_values is not None else len(self.options)
        if not 0 <= self.min_values <= 10 or not 1 <= self.max_values <= 10:
            raise ValueError("min_values must be 0-10 and max_values 1-10")
        if self.min_values > self.max_values or self.max_values > len(self.options):
            raise ValueError("min_values <= max_values <= number of options")
        if required and self.min_values < 1:
            raise ValueError("min_values must be at least 1 when required is True")
        self.required = required

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["custom_id"] = self.custom_id
        data["options"] = [o.to_dict() for o in self.options]
        data["min_values"] = self.min_values
        data["max_values"] = self.max_values
        data["required"] = self.required
        return data

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "CheckboxGroup":
        options = [GroupOption.from_dict(o) for o in data.get("options", [])]
        return cls(data["custom_id"], options, min_values=data.get("min_values", 1),
                   max_values=data.get("max_values"), required=data.get("required", True), id=data.get("id"))


class Checkbox(Component):
    """Single yes/no checkbox for modals (type 23). Put it inside a Label. It can't be required."""

    type = ComponentType.CHECKBOX

    def __init__(
        self,
        custom_id: str,
        *,
        default: bool = False,
        id: Optional[int] = None,
    ):
        super().__init__(id=id)
        _check_custom_id(custom_id)
        self.custom_id = custom_id
        self.default = default

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["custom_id"] = self.custom_id
        if self.default:
            data["default"] = True
        return data

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "Checkbox":
        return cls(data["custom_id"], default=bool(data.get("default")), id=data.get("id"))


LABEL_CHILDREN = (TextInput, BaseSelect, FileUpload, RadioGroup, CheckboxGroup, Checkbox, UnknownComponent)


class Label(Component):
    """A label and optional description around one modal control (type 18)."""

    type = ComponentType.LABEL

    def __init__(
        self,
        label: str,
        component: Component,
        *,
        description: Optional[str] = None,
        id: Optional[int] = None,
    ):
        super().__init__(id=id)
        if not label or len(label) > 45:
            raise ValueError("Label text must be 1-45 characters")
        _check_max("Label description", description, 100)
        if not isinstance(component, LABEL_CHILDREN):
            raise ValueError(
                "Label child must be a TextInput, a select, FileUpload, RadioGroup, CheckboxGroup or Checkbox"
            )
        self.label = label
        self.description = description
        self.component = component

    def children(self) -> list[Component]:
        return [self.component]

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["label"] = self.label
        if self.description is not None:
            data["description"] = self.description
        data["component"] = self.component.to_dict()
        return data

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "Label":
        return cls(data.get("label") or " ", component_from_dict(data.get("component") or {}),
                   description=data.get("description"), id=data.get("id"))


def count_components(components: Sequence[Component]) -> int:
    """Count every component including nested ones. Discord allows 40 per message."""
    return sum(1 for c in components for _ in c.walk())
