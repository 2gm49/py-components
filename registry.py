class Registry:
    def __init__(self):
        self.routes = {}

    def register(self, custom_id, func):
        self.routes[custom_id] = func

    async def dispatch(self, custom_id, ctx):
        if custom_id in self.routes:
            await self.routes[custom_id](ctx)
