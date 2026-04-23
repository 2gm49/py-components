from .http import send_message
from .components import Button


class UI:
    def __init__(self, *components):
        self.components = list(components)

    def add(self, component):
        self.components.append(component)

    def to_payload(self):
        top_level = []
        button_buffer = []

        for c in self.components:
            if isinstance(c, Button):
                button_buffer.append(c.to_dict())
                if len(button_buffer) == 5:
                    top_level.append({"type": 1, "components": button_buffer})
                    button_buffer = []
            else:
                if button_buffer:
                    top_level.append({"type": 1, "components": button_buffer})
                    button_buffer = []
                top_level.append(c.to_dict())

        if button_buffer:
            top_level.append({"type": 1, "components": button_buffer})

        return {
            "flags": 1 << 15,
            "components": [
                {
                    "type": 17,
                    "components": top_level
                }
            ]
        }

    async def send(self, ctx):
        token = ctx.bot.http.token
        return await send_message(ctx.channel.id, token, self.to_payload())


async def send_ui(ctx, ui):
    token = ctx.bot.http.token
    return await send_message(ctx.channel.id, token, ui.to_payload())