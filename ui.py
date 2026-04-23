from .components import Text, Button
from .http import send_message


class UI:
    def __init__(self, *components):
        self.components = list(components)

    def add_text(self, content):
        self.components.append(Text(content))

    def add_button(self, label, custom_id, style=1):
        self.components.append(Button(label, custom_id, style))

    def to_dict(self):
        return {
            "flags": 1 << 15,
            "components": [
                {
                    "type": 17,
                    "components": [c.to_dict() for c in self.components]
                }
            ]
        }

    async def send(self, ctx):
        token = ctx.bot.http.token
        channel_id = ctx.channel.id

        return await send_message(channel_id, token, self.to_dict())
