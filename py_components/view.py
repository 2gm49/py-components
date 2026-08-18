"""View / callback registry helpers for interactive components."""

from __future__ import annotations

from typing import Any, Callable, Coroutine, Optional

from .components import ActionRow, Button, Component
from .enums import ButtonStyle, IS_COMPONENTS_V2


Callback = Callable[..., Coroutine[Any, Any, Any]]


def button(label: str, *, custom_id: Optional[str] = None, style: ButtonStyle = ButtonStyle.PRIMARY):
    """Decorator that marks a coroutine as a button callback.

    The decorated function receives the interaction as its first argument.
    """

    def wrapper(func: Callback) -> Callback:
        func._button_label = label  # type: ignore[attr-defined]
        func._button_custom_id = custom_id or func.__name__  # type: ignore[attr-defined]
        func._button_style = style  # type: ignore[attr-defined]
        return func

    return wrapper


class View:
    """Collects interactive components and their callbacks.

    Usage::

        view = View()

        async def on_confirm(interaction):
            await interaction.response.send_message("Confirmed!")

        view.add_button("Confirm", custom_id="confirm", callback=on_confirm)
        payload = view.to_payload()
    """

    def __init__(self):
        self.components: list[Component] = []
        self.registry: dict[str, Callback] = {}

    def add_button(
        self,
        label: str,
        custom_id: str,
        *,
        style: ButtonStyle = ButtonStyle.PRIMARY,
        callback: Optional[Callback] = None,
        emoji: Optional[dict] = None,
        disabled: bool = False,
    ) -> Button:
        btn = Button(
            label,
            custom_id=custom_id,
            style=style,
            emoji=emoji,
            disabled=disabled,
        )
        self.components.append(btn)
        if callback:
            self.registry[custom_id] = callback
        return btn

    def add_component(self, component: Component, *, callback: Optional[Callback] = None) -> Component:
        self.components.append(component)
        if callback and hasattr(component, "custom_id") and component.custom_id:
            self.registry[component.custom_id] = callback
        return component

    def to_payload(self) -> dict[str, Any]:
        """Return a Components V2 payload containing the registered buttons."""
        top_level: list[dict] = []
        buffer: list[Button] = []
        for c in self.components:
            if isinstance(c, Button):
                buffer.append(c)
                if len(buffer) == 5:
                    top_level.append(ActionRow(*buffer).to_dict())
                    buffer = []
            else:
                if buffer:
                    top_level.append(ActionRow(*buffer).to_dict())
                    buffer = []
                top_level.append(c.to_dict())
        if buffer:
            top_level.append(ActionRow(*buffer).to_dict())

        return {
            "flags": IS_COMPONENTS_V2,
            "components": top_level,
        }

    async def dispatch(self, custom_id: str, interaction: Any) -> None:
        """Call the registered callback for ``custom_id`` if present."""
        cb = self.registry.get(custom_id)
        if cb:
            await cb(interaction)
