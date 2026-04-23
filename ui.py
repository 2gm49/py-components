from .http import send_message

class UI:
    def __init__(self, *components):
        self.components = list(components)

    def add(self, component):
        self.components.append(component)

    def to_payload(self):
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
        return await send_message(ctx.channel.id, token, self.to_payload())


async def send_ui(ctx, ui):
    token = ctx.bot.http.token
    return await send_message(ctx.channel.id, token, ui.to_payload())
