"""Read what users picked or typed from component and modal interactions."""

from __future__ import annotations

from typing import Any, Iterator, Optional

from .enums import ComponentType


def _data_of(source: Any) -> dict[str, Any]:
    if isinstance(source, dict):
        return source["data"] if isinstance(source.get("data"), dict) else source
    data = getattr(source, "data", None)
    if isinstance(data, dict):
        return data
    raise ValueError("pass an Interaction or its data dict")


def _parse_value(node: dict[str, Any]) -> Any:
    t = node.get("type")
    if t in (ComponentType.TEXT_INPUT, ComponentType.RADIO_GROUP, ComponentType.CHECKBOX):
        return node.get("value")
    if "values" in node:
        return list(node.get("values") or [])
    return node.get("value")


class SubmittedField:
    """One filled-in control from a modal."""

    def __init__(self, node: dict[str, Any], label_id: Optional[int] = None):
        self.raw = node
        self.type = node.get("type")
        self.id = node.get("id")
        self.label_id = label_id
        self.custom_id: str = node.get("custom_id", "")
        self.value = _parse_value(node)

    def __repr__(self) -> str:
        return f"SubmittedField(custom_id={self.custom_id!r}, value={self.value!r})"


class ModalSubmit:
    """Values from a modal submit interaction, keyed by custom_id.

    Text inputs give a str, radio groups a str or None, checkboxes a bool,
    checkbox groups and selects a list of str, file uploads a list of attachment ids.
    """

    def __init__(self, source: Any):
        self.data = _data_of(source)
        self.custom_id: str = self.data.get("custom_id", "")
        self.resolved: dict[str, Any] = self.data.get("resolved") or {}
        self.fields: dict[str, SubmittedField] = {}
        self._walk(self.data.get("components") or [])

    def _walk(self, nodes: list[dict[str, Any]], label_id: Optional[int] = None) -> None:
        for node in nodes:
            t = node.get("type")
            if t == ComponentType.LABEL and isinstance(node.get("component"), dict):
                self._walk([node["component"]], node.get("id"))
            elif t == ComponentType.ACTION_ROW:
                self._walk(node.get("components") or [], label_id)
            elif node.get("custom_id"):
                field = SubmittedField(node, label_id)
                self.fields[field.custom_id] = field

    def __getitem__(self, custom_id: str) -> Any:
        return self.fields[custom_id].value

    def __contains__(self, custom_id: str) -> bool:
        return custom_id in self.fields

    def __iter__(self) -> Iterator[str]:
        return iter(self.fields)

    def get(self, custom_id: str, default: Any = None) -> Any:
        field = self.fields.get(custom_id)
        if field is None:
            return default
        value = field.value
        if value is None or value == "" or value == []:
            return default
        return value

    def values(self) -> dict[str, Any]:
        return {k: f.value for k, f in self.fields.items()}

    def text(self, custom_id: str, default: str = "") -> str:
        value = self.get(custom_id)
        return value if isinstance(value, str) else default

    def checked(self, custom_id: str) -> bool:
        return bool(self.get(custom_id, False))

    def selected(self, custom_id: str) -> list[str]:
        value = self.get(custom_id, [])
        return value if isinstance(value, list) else [value]

    def attachments(self, custom_id: str) -> list[dict[str, Any]]:
        """Attachment objects uploaded through a FileUpload."""
        found = self.resolved.get("attachments") or {}
        return [found[i] for i in self.selected(custom_id) if i in found]

    def users(self, custom_id: str) -> list[dict[str, Any]]:
        found = self.resolved.get("users") or {}
        return [found[i] for i in self.selected(custom_id) if i in found]

    def members(self, custom_id: str) -> list[dict[str, Any]]:
        found = self.resolved.get("members") or {}
        return [found[i] for i in self.selected(custom_id) if i in found]

    def roles(self, custom_id: str) -> list[dict[str, Any]]:
        found = self.resolved.get("roles") or {}
        return [found[i] for i in self.selected(custom_id) if i in found]

    def channels(self, custom_id: str) -> list[dict[str, Any]]:
        found = self.resolved.get("channels") or {}
        return [found[i] for i in self.selected(custom_id) if i in found]

    def __repr__(self) -> str:
        return f"ModalSubmit(custom_id={self.custom_id!r}, values={self.values()!r})"


class ComponentClick:
    """What a user did with a message component: button click or select choice."""

    def __init__(self, source: Any):
        self.data = _data_of(source)
        self.custom_id: str = self.data.get("custom_id", "")
        self.component_type = self.data.get("component_type")
        self.id = self.data.get("id")
        self.values: list[str] = list(self.data.get("values") or [])
        self.resolved: dict[str, Any] = self.data.get("resolved") or {}

    @property
    def is_button(self) -> bool:
        return self.component_type == ComponentType.BUTTON

    @property
    def is_select(self) -> bool:
        return self.component_type in (
            ComponentType.STRING_SELECT, ComponentType.USER_SELECT, ComponentType.ROLE_SELECT,
            ComponentType.MENTIONABLE_SELECT, ComponentType.CHANNEL_SELECT,
        )

    @property
    def value(self) -> Optional[str]:
        return self.values[0] if self.values else None

    def __repr__(self) -> str:
        return f"ComponentClick(custom_id={self.custom_id!r}, values={self.values!r})"


def parse_modal(source: Any) -> ModalSubmit:
    return ModalSubmit(source)


def parse_component(source: Any) -> ComponentClick:
    return ComponentClick(source)


def interaction_kind(interaction: Any) -> Optional[str]:
    """'component', 'modal_submit', 'application_command', 'autocomplete', 'ping' or None."""
    t = interaction.get("type") if isinstance(interaction, dict) else getattr(interaction, "type", None)
    value = getattr(t, "value", t)
    return {1: "ping", 2: "application_command", 3: "component", 4: "autocomplete", 5: "modal_submit"}.get(value)
