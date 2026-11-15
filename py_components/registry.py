from __future__ import annotations

from typing import Any, Callable, Coroutine, Optional

Callback = Callable[..., Coroutine[Any, Any, Any]]


class Registry:
    def __init__(self) -> None:
        self.routes: dict[str, Callback] = {}

    def register(self, custom_id: str, func: Callback) -> Callback:
        self.routes[custom_id] = func
        return func

    def route(self, custom_id: str) -> Callable[[Callback], Callback]:
        def decorator(func: Callback) -> Callback:
            self.routes[custom_id] = func
            return func
        return decorator

    async def dispatch(self, custom_id: str, *args: Any, **kwargs: Any) -> Optional[Any]:
        if custom_id in self.routes:
            return await self.routes[custom_id](*args, **kwargs)
        return None

    async def dispatch_interaction(self, interaction: Any, *args: Any, **kwargs: Any) -> bool:
        """Run the callback for a component or modal interaction's custom_id. Returns False if none matched."""
        data = getattr(interaction, "data", None)
        if data is None and isinstance(interaction, dict):
            data = interaction.get("data")
        custom_id = (data or {}).get("custom_id")
        if custom_id not in self.routes:
            return False
        await self.routes[custom_id](interaction, *args, **kwargs)
        return True

    def clear(self) -> None:
        self.routes.clear()


default_registry = Registry()
