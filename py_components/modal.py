from __future__ import annotations

from typing import Any

from .components import ActionRow, Component, Label, TextDisplay, TextInput, UnknownComponent, component_from_dict
from .enums import MAX_MODAL_COMPONENTS
from .http import open_modal
from .ids import assign_ids


class Modal:
    def __init__(self, custom_id: str, title: str, *components: Component):
        if not 1 <= len(custom_id) <= 100:
            raise ValueError("custom_id must be 1-100 characters")
        if not title or len(title) > 45:
            raise ValueError("title must be 1-45 characters")
        self.custom_id = custom_id
        self.title = title
        self.components: list[Component] = []
        self.add(*components)

    def add(self, *components: Component) -> "Modal":
        if len(self.components) + len(components) > MAX_MODAL_COMPONENTS:
            raise ValueError(f"max {MAX_MODAL_COMPONENTS} top-level components")
        for c in components:
            self._check(c)
        self.components.extend(components)
        return self

    @staticmethod
    def _check(component: Component) -> None:
        if isinstance(component, ActionRow):
            if not all(isinstance(c, TextInput) for c in component.components):
                raise ValueError("modal ActionRows can only hold a TextInput (better: use a Label)")
        elif not isinstance(component, (Label, TextDisplay, UnknownComponent)):
            raise ValueError("modal top-level components must be Label or TextDisplay")
        for c in component.walk():
            if getattr(c, "disabled", False):
                raise ValueError("components in a modal can't be disabled")

    def to_dict(self, *, assign_ids_: bool = True) -> dict[str, Any]:
        comps = [c.to_dict() for c in self.components]
        if assign_ids_:
            assign_ids(comps)
        return {
            "custom_id": self.custom_id,
            "title": self.title,
            "components": comps,
        }

    def to_response(self) -> dict[str, Any]:
        return {"type": 9, "data": self.to_dict()}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Modal":
        modal = cls(data["custom_id"], data.get("title") or " ")
        modal.components = [component_from_dict(c) for c in data.get("components", [])]
        return modal

    async def open(self, interaction: Any) -> Any:
        response = getattr(interaction, "response", None)
        is_done = getattr(response, "is_done", None)
        if callable(is_done) and is_done():
            raise RuntimeError("this interaction was already responded to, a modal must be the first response")
        interaction_id = getattr(interaction, "id", None)
        token = getattr(interaction, "token", None)
        if interaction_id is None or token is None:
            raise ValueError("interaction needs .id and .token")
        result = await open_modal(str(interaction_id), token, self.to_dict())
        if response is not None and hasattr(response, "_response_type"):
            try:
                from discord import InteractionResponseType as _RT
                response._response_type = _RT.modal
            except Exception:
                pass
        return result
