from __future__ import annotations

from typing import Any

from .components import Component
from .http import open_modal
from .ids import assign_ids


class Modal:
    def __init__(self, custom_id: str, title: str, *components: Component):
        if not 1 <= len(custom_id) <= 100:
            raise ValueError("custom_id must be 1-100 characters")
        if not title or len(title) > 45:
            raise ValueError("title must be 1-45 characters")
        if len(components) > 5:
            raise ValueError("max 5 top-level components")
        self.custom_id = custom_id
        self.title = title
        self.components: list[Component] = list(components)

    def add(self, *components: Component) -> "Modal":
        if len(self.components) + len(components) > 5:
            raise ValueError("max 5 top-level components")
        self.components.extend(components)
        return self

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

    async def open(self, interaction: Any) -> Any:
        interaction_id = getattr(interaction, "id", None)
        token = getattr(interaction, "token", None)
        if interaction_id is None or token is None:
            raise ValueError("interaction needs .id and .token")
        return await open_modal(str(interaction_id), token, self.to_dict())
