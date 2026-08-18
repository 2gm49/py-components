"""Simple global custom_id → callback registry."""

from __future__ import annotations

from typing import Any, Callable, Coroutine, Optional


Callback = Callable[..., Coroutine[Any, Any, Any]]


class Registry:
    """Maps custom_ids to async callables.

    Useful when you want a single place to route all component interactions
    instead of attaching callbacks to individual View instances.
    """

    def __init__(self) -> None:
        self.routes: dict[str, Callback] = {}

    def register(self, custom_id: str, func: Callback) -> Callback:
        self.routes[custom_id] = func
        return func

    def route(self, custom_id: str) -> Callable[[Callback], Callback]:
        """Decorator form of register."""

        def decorator(func: Callback) -> Callback:
            self.routes[custom_id] = func
            return func

        return decorator

    async def dispatch(self, custom_id: str, *args: Any, **kwargs: Any) -> Optional[Any]:
        if custom_id in self.routes:
            return await self.routes[custom_id](*args, **kwargs)
        return None

    def clear(self) -> None:
        self.routes.clear()


default_registry = Registry()
