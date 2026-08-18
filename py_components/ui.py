"""High-level UI builder for Components V2 messages."""

from __future__ import annotations

from typing import Any

from .components import (
    ActionRow,
    Button,
    Component,
)
from .enums import IS_COMPONENTS_V2
from .http import send_message, respond_interaction


class UI:
    """Builder for a Components V2 message payload.

    Components may be mixed freely. Buttons are automatically wrapped
    into ActionRows (max 5 buttons per row). Select menus should be
    placed inside an ActionRow yourself (one select per row). Other
    components are placed at the top level.

    Example::

        ui = UI(
            TextDisplay("Hello **world**"),
            Button("Yes", custom_id="yes", style=ButtonStyle.SUCCESS),
            Button("No", custom_id="no", style=ButtonStyle.DANGER),
        )
        await ui.send(ctx)
    """

    def __init__(self, *components: Component):
        self.components: list[Component] = list(components)

    def add(self, *components: Component) -> "UI":
        self.components.extend(components)
        return self

    def to_payload(self) -> dict[str, Any]:
        """Build the final message payload with the IS_COMPONENTS_V2 flag."""
        top_level: list[dict[str, Any]] = []
        button_buffer: list[Button] = []

        def flush_buttons() -> None:
            nonlocal button_buffer
            if button_buffer:
                top_level.append(ActionRow(*button_buffer).to_dict())
                button_buffer = []

        for c in self.components:
            if isinstance(c, Button):
                button_buffer.append(c)
                if len(button_buffer) == 5:
                    flush_buttons()
            elif isinstance(c, ActionRow):
                flush_buttons()
                top_level.append(c.to_dict())
            else:
                flush_buttons()
                top_level.append(c.to_dict())

        flush_buttons()

        return {
            "flags": IS_COMPONENTS_V2,
            "components": top_level,
        }

    async def send(self, ctx: Any, **kwargs: Any) -> str:
        """Send the UI as a new channel message.

        ``ctx`` may be a discord.py Context, Interaction, or any object
        that exposes channel id and a bot token via ``.bot.http.token``.
        """
        channel_id, token = _resolve_channel_and_token(ctx)
        return await send_message(channel_id, token, self.to_payload(), **kwargs)

    async def reply(self, interaction: Any, *, ephemeral: bool = False) -> str:
        """Respond to an interaction with this UI (callback type 4)."""
        token = _resolve_token(interaction)
        application_id = _resolve_application_id(interaction)
        interaction_token = interaction.token
        payload = self.to_payload()
        if ephemeral:
            payload["flags"] = payload.get("flags", 0) | (1 << 6)  # EPHEMERAL
        return await respond_interaction(
            application_id, interaction_token, token, payload
        )


async def send_ui(ctx: Any, ui: UI, **kwargs: Any) -> str:
    """Convenience wrapper around ``UI.send``."""
    return await ui.send(ctx, **kwargs)


def _resolve_channel_and_token(ctx: Any) -> tuple[Any, str]:
    channel_id = None
    if hasattr(ctx, "channel") and ctx.channel is not None:
        channel_id = getattr(ctx.channel, "id", None)
    if channel_id is None:
        channel_id = getattr(ctx, "channel_id", None)
    if channel_id is None and hasattr(ctx, "message"):
        channel_id = getattr(getattr(ctx.message, "channel", None), "id", None)
    if channel_id is None:
        raise ValueError("Could not resolve channel id from context")

    token = _resolve_token(ctx)
    return channel_id, token


def _resolve_token(obj: Any) -> str:
    for attr in ("bot", "client", "_state"):
        owner = getattr(obj, attr, None)
        if owner is None:
            continue
        http = getattr(owner, "http", None)
        if http is not None:
            tok = getattr(http, "token", None)
            if tok:
                return tok
    raise ValueError("Could not resolve bot token from context")


def _resolve_application_id(interaction: Any) -> str:
    app_id = getattr(interaction, "application_id", None)
    if app_id is not None:
        return str(app_id)
    if hasattr(interaction, "client"):
        app = getattr(interaction.client, "application_id", None)
        if app:
            return str(app)
    raise ValueError("Could not resolve application_id from interaction")
