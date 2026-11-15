from __future__ import annotations

from typing import Any, Optional

from .components import ActionRow, BaseSelect, Button, Component, component_from_dict, count_components
from .enums import EPHEMERAL, IS_COMPONENTS_V2, MAX_MESSAGE_COMPONENTS, SUPPRESS_NOTIFICATIONS
from .http import send_message, respond_interaction
from .ids import assign_ids, find_by_id, replace_by_id


class UI:
    def __init__(self, *components: Component):
        self.components: list[Component] = list(components)
        self._auto_ids = True

    def add(self, *components: Component) -> "UI":
        self.components.extend(components)
        return self

    @classmethod
    def from_payload(cls, payload: Any) -> "UI":
        """Rebuild a UI from a raw payload, a components list, or a message dict."""
        if isinstance(payload, dict):
            payload = payload.get("components", [])
        return cls(*[component_from_dict(c) for c in payload])

    def count(self) -> int:
        """Total components including nested ones, after loose buttons are wrapped."""
        rows = sum(1 for _ in self._rows())
        return count_components(self.components) + rows

    def _rows(self):
        buffer = 0
        for c in self.components:
            if isinstance(c, Button):
                buffer += 1
                if buffer == 5:
                    yield 1
                    buffer = 0
            else:
                if buffer:
                    yield 1
                    buffer = 0
                if isinstance(c, BaseSelect):
                    yield 1
        if buffer:
            yield 1

    def to_payload(self, *, assign_ids_: bool | None = None) -> dict[str, Any]:
        top_level: list[dict[str, Any]] = []
        button_buffer: list[Button] = []

        def flush() -> None:
            nonlocal button_buffer
            if button_buffer:
                top_level.append(ActionRow(*button_buffer).to_dict())
                button_buffer = []

        for c in self.components:
            if isinstance(c, Button):
                button_buffer.append(c)
                if len(button_buffer) == 5:
                    flush()
            elif isinstance(c, ActionRow):
                flush()
                top_level.append(c.to_dict())
            elif isinstance(c, BaseSelect):
                flush()
                top_level.append(ActionRow(c).to_dict())
            else:
                flush()
                top_level.append(c.to_dict())
        flush()

        total = count_components(self.components) + sum(1 for _ in self._rows())
        if total > MAX_MESSAGE_COMPONENTS:
            raise ValueError(f"a message can have at most {MAX_MESSAGE_COMPONENTS} components, this one has {total}")

        do_ids = self._auto_ids if assign_ids_ is None else assign_ids_
        if do_ids:
            assign_ids(top_level)

        return {"flags": IS_COMPONENTS_V2, "components": top_level}

    def to_components(self) -> list[dict[str, Any]]:
        return self.to_payload()["components"]

    def get(self, component_id: int) -> Optional[dict[str, Any]]:
        return find_by_id(self.to_payload()["components"], component_id)

    def replace(self, component_id: int, component: Component) -> dict[str, Any]:
        payload = self.to_payload()
        ok = replace_by_id(payload["components"], component_id, component.to_dict())
        if not ok:
            raise KeyError(f"no component with id={component_id}")
        return payload

    async def send(
        self,
        target: Any,
        *,
        ephemeral: bool = False,
        silent: bool = False,
        files: Optional[list] = None,
        allowed_mentions: Any = None,
        **kwargs: Any,
    ) -> Any:
        payload = self.to_payload()
        if ephemeral:
            payload["flags"] = payload.get("flags", 0) | EPHEMERAL
        if silent:
            payload["flags"] = payload.get("flags", 0) | SUPPRESS_NOTIFICATIONS
            kwargs.setdefault("silent", True)
        if allowed_mentions is not None:
            kwargs["allowed_mentions"] = allowed_mentions
            payload["allowed_mentions"] = (
                allowed_mentions.to_dict() if hasattr(allowed_mentions, "to_dict") else allowed_mentions
            )

        if _is_interaction(target):
            return await self._send_interaction(target, payload, files=files, **kwargs)

        # User/Member → open DM channel so we never POST to /channels/{user.id}
        target = await _ensure_messageable(target)
        return await self._send_channel(target, payload, files=files, **kwargs)

    async def reply(
        self,
        interaction: Any,
        *,
        ephemeral: bool = False,
        files: Optional[list] = None,
        **kwargs: Any,
    ) -> Any:
        return await self.send(interaction, ephemeral=ephemeral, files=files, **kwargs)

    async def update(self, interaction: Any, **kwargs: Any) -> Any:
        """Edit the message a button or select was used on, as the interaction response."""
        return await self.edit(interaction, **kwargs)

    async def edit(
        self,
        target: Any,
        *,
        message: Any = None,
        **kwargs: Any,
    ) -> Any:
        payload = self.to_payload()

        if _is_interaction(target):
            response = getattr(target, "response", None)
            if response is not None and hasattr(response, "edit_message"):
                try:
                    return await response.edit_message(
                        components=payload["components"], **kwargs
                    )
                except Exception:
                    pass
            for name in ("edit_original_response", "edit_original_message"):
                if hasattr(target, name):
                    return await getattr(target, name)(
                        components=payload["components"], **kwargs
                    )

        msg = message or target
        if hasattr(msg, "edit"):
            try:
                return await msg.edit(
                    components=payload["components"],
                    flags=payload.get("flags", IS_COMPONENTS_V2),
                    **kwargs,
                )
            except TypeError:
                return await msg.edit(components=payload["components"], **kwargs)

        raise ValueError("pass an Interaction or Message")

    async def _send_interaction(
        self,
        interaction: Any,
        payload: dict[str, Any],
        *,
        files: Optional[list] = None,
        **kwargs: Any,
    ) -> Any:
        response = getattr(interaction, "response", None)
        components = payload["components"]
        flags = payload.get("flags", IS_COMPONENTS_V2)

        if response is not None:
            is_done = getattr(response, "is_done", lambda: False)()
            if not is_done and hasattr(response, "send_message"):
                for attempt in (
                    dict(components=components, flags=flags, files=files or [], **kwargs),
                    dict(components=components, ephemeral=bool(flags & (1 << 6)), files=files or [], **kwargs),
                ):
                    try:
                        return await response.send_message(**attempt)
                    except TypeError:
                        continue
                    except Exception:
                        break
            followup = getattr(interaction, "followup", None)
            if followup is not None and hasattr(followup, "send"):
                for attempt in (
                    dict(components=components, flags=flags, files=files or [], **kwargs),
                    dict(components=components, ephemeral=bool(flags & (1 << 6)), files=files or [], **kwargs),
                ):
                    try:
                        return await followup.send(**attempt)
                    except TypeError:
                        continue
                    except Exception:
                        break

        token = _resolve_token(interaction)
        application_id = _resolve_application_id(interaction)
        return await respond_interaction(
            application_id, interaction.token, token, payload
        )

    async def _send_channel(
        self,
        target: Any,
        payload: dict[str, Any],
        *,
        files: Optional[list] = None,
        **kwargs: Any,
    ) -> Any:
        send_method = None
        if callable(getattr(target, "send", None)):
            send_method = target.send
        elif hasattr(target, "channel") and callable(getattr(target.channel, "send", None)):
            send_method = target.channel.send

        if send_method is not None:
            attempts = [
                dict(components=payload["components"], flags=payload.get("flags", IS_COMPONENTS_V2), files=files or [], **kwargs),
                dict(components=payload["components"], flags=payload.get("flags", IS_COMPONENTS_V2), **kwargs),
                dict(components=payload["components"], files=files or [], **kwargs),
                dict(components=payload["components"], **kwargs),
            ]
            last_err: Exception | None = None
            for attempt in attempts:
                try:
                    return await send_method(**attempt)
                except TypeError as e:
                    last_err = e
                    continue
                except Exception as e:
                    last_err = e
                    break
            if last_err is not None and not isinstance(last_err, TypeError):
                raise last_err

        channel_id, token = _resolve_channel_and_token(target)
        return await send_message(channel_id, token, payload, files=files)


async def send_ui(target: Any, ui: UI, **kwargs: Any) -> Any:
    return await ui.send(target, **kwargs)


def _is_interaction(obj: Any) -> bool:
    if obj is None:
        return False
    if hasattr(obj, "response") and hasattr(obj, "token"):
        return True
    if getattr(obj, "type", None) is not None and hasattr(obj, "token") and hasattr(obj, "id"):
        return True
    return False


def _is_user_like(obj: Any) -> bool:
    """User/Member — has create_dm, not a guild channel."""
    if obj is None:
        return False
    if callable(getattr(obj, "create_dm", None)):
        return True
    # duck type: no guild attribute path for pure User
    cls_name = type(obj).__name__
    return cls_name in ("User", "Member", "ClientUser")


async def _ensure_messageable(target: Any) -> Any:
    if _is_user_like(target):
        dm = getattr(target, "dm_channel", None)
        if dm is not None:
            return dm
        if callable(getattr(target, "create_dm", None)):
            return await target.create_dm()
    return target


def _resolve_channel_and_token(obj: Any) -> tuple[Any, str]:
    channel_id = None

    # Prefer explicit channel objects (have recipients or guild, or type name)
    name = type(obj).__name__
    if name in ("TextChannel", "Thread", "DMChannel", "GroupChannel", "VoiceChannel", "StageChannel"):
        channel_id = getattr(obj, "id", None)
    elif getattr(obj, "id", None) is not None and callable(getattr(obj, "send", None)) and not _is_user_like(obj):
        channel_id = obj.id

    if channel_id is None and hasattr(obj, "channel") and obj.channel is not None:
        channel_id = getattr(obj.channel, "id", None)
    if channel_id is None:
        channel_id = getattr(obj, "channel_id", None)
    if channel_id is None and hasattr(obj, "message"):
        channel_id = getattr(getattr(obj.message, "channel", None), "id", None)

    if channel_id is None:
        raise ValueError("could not resolve channel id")

    return channel_id, _resolve_token(obj)


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

    state = getattr(obj, "_state", None)
    if state is not None:
        http = getattr(state, "http", None)
        if http is not None:
            tok = getattr(http, "token", None)
            if tok:
                return tok

    if hasattr(obj, "channel") and obj.channel is not None:
        return _resolve_token(obj.channel)

    raise ValueError("could not resolve bot token")


def _resolve_application_id(interaction: Any) -> str:
    app_id = getattr(interaction, "application_id", None)
    if app_id is not None:
        return str(app_id)
    if hasattr(interaction, "client"):
        app = getattr(interaction.client, "application_id", None)
        if app:
            return str(app)
    raise ValueError("could not resolve application_id")
