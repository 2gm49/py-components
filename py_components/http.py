"""Low-level Discord REST helpers for Components V2."""

from __future__ import annotations

import json
from typing import Any, Optional

import aiohttp

API = "https://discord.com/api/v10"


async def send_message(
    channel_id: Any,
    token: str,
    payload: dict[str, Any],
    *,
    files: Optional[list] = None,
) -> str:
    """POST /channels/{channel_id}/messages"""
    url = f"{API}/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {token}" if not token.startswith("Bot ") else token,
    }

    async with aiohttp.ClientSession() as session:
        if files:
            form = aiohttp.FormData()
            form.add_field("payload_json", json.dumps(payload))
            for i, f in enumerate(files):
                form.add_field(
                    f"files[{i}]",
                    f["fp"],
                    filename=f["filename"],
                    content_type=f.get("content_type", "application/octet-stream"),
                )
            async with session.post(url, data=form, headers=headers) as resp:
                return await resp.text()
        else:
            headers["Content-Type"] = "application/json"
            async with session.post(url, json=payload, headers=headers) as resp:
                return await resp.text()


async def edit_message(
    channel_id: Any,
    message_id: Any,
    token: str,
    payload: dict[str, Any],
) -> str:
    """PATCH /channels/{channel_id}/messages/{message_id}"""
    url = f"{API}/channels/{channel_id}/messages/{message_id}"
    headers = {
        "Authorization": f"Bot {token}" if not token.startswith("Bot ") else token,
        "Content-Type": "application/json",
    }
    async with aiohttp.ClientSession() as session:
        async with session.patch(url, json=payload, headers=headers) as resp:
            return await resp.text()


async def respond_interaction(
    application_id: str,
    interaction_token: str,
    bot_token: str,
    payload: dict[str, Any],
    *,
    type: int = 4,
) -> str:
    """Respond to an interaction (callback or follow-up)."""
    headers = {
        "Authorization": f"Bot {bot_token}" if not bot_token.startswith("Bot ") else bot_token,
        "Content-Type": "application/json",
    }
    callback_url = f"{API}/interactions/{application_id}/{interaction_token}/callback"
    followup_url = f"{API}/webhooks/{application_id}/{interaction_token}"

    async with aiohttp.ClientSession() as session:
        async with session.post(
            callback_url,
            json={"type": type, "data": payload},
            headers=headers,
        ) as resp:
            text = await resp.text()
            if resp.status < 400:
                return text
        async with session.post(followup_url, json=payload, headers=headers) as resp:
            return await resp.text()
