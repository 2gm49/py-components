import aiohttp

API = "https://discord.com/api/v10"

async def send_message(channel_id, token, payload):
    url = f"{API}/channels/{channel_id}/messages"

    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            return await resp.text()
