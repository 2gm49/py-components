"""Assign and look up component ids within a payload tree."""

from __future__ import annotations

from typing import Any, Callable, Optional


def _is_component_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and isinstance(value[0], dict) and "type" in value[0]


def assign_ids(components: list[dict[str, Any]], *, start: int = 1) -> int:
    """Walk a components tree and fill in missing id fields sequentially.

    Returns the next free id. Existing non-zero ids are kept.
    """
    next_id = start
    used = set()

    def collect(nodes: list[dict[str, Any]]) -> None:
        for n in nodes:
            i = n.get("id")
            if i:
                used.add(i)
            for key in ("components", "items"):
                child = n.get(key)
                if _is_component_list(child):
                    collect(child)
            inner = n.get("component")
            if isinstance(inner, dict):
                collect([inner])
            acc = n.get("accessory")
            if isinstance(acc, dict):
                collect([acc])

    collect(components)
    if used:
        next_id = max(max(used) + 1, start)

    def fill(nodes: list[dict[str, Any]]) -> None:
        nonlocal next_id
        for n in nodes:
            if not n.get("id"):
                while next_id in used:
                    next_id += 1
                n["id"] = next_id
                used.add(next_id)
                next_id += 1
            for key in ("components", "items"):
                child = n.get(key)
                if _is_component_list(child):
                    fill(child)
            inner = n.get("component")
            if isinstance(inner, dict):
                fill([inner])
            acc = n.get("accessory")
            if isinstance(acc, dict):
                fill([acc])

    fill(components)
    return next_id


def find_by_id(components: list[dict[str, Any]], target_id: int) -> Optional[dict[str, Any]]:
    """Return the first component dict with the given id, or None."""

    def walk(nodes: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
        for n in nodes:
            if n.get("id") == target_id:
                return n
            for key in ("components", "items"):
                child = n.get(key)
                if _is_component_list(child):
                    found = walk(child)
                    if found is not None:
                        return found
            inner = n.get("component")
            if isinstance(inner, dict):
                found = walk([inner])
                if found is not None:
                    return found
            acc = n.get("accessory")
            if isinstance(acc, dict):
                found = walk([acc])
                if found is not None:
                    return found
        return None

    return walk(components)


def replace_by_id(
    components: list[dict[str, Any]],
    target_id: int,
    new_component: dict[str, Any],
) -> bool:
    """Replace the component with target_id in-place. Keeps the id on the replacement."""

    def walk(nodes: list[dict[str, Any]]) -> bool:
        for i, n in enumerate(nodes):
            if n.get("id") == target_id:
                nodes[i] = {**new_component, "id": target_id}
                return True
            for key in ("components", "items"):
                child = n.get(key)
                if _is_component_list(child):
                    if walk(child):
                        return True
            inner = n.get("component")
            if isinstance(inner, dict) and inner.get("id") == target_id:
                n["component"] = {**new_component, "id": target_id}
                return True
            if isinstance(inner, dict):
                if walk([inner]):
                    return True
            acc = n.get("accessory")
            if isinstance(acc, dict) and acc.get("id") == target_id:
                n["accessory"] = {**new_component, "id": target_id}
                return True
            if isinstance(acc, dict):
                if walk([acc]):
                    return True
        return False

    return walk(components)


def map_ids(
    components: list[dict[str, Any]],
    fn: Callable[[dict[str, Any]], Optional[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Apply fn to every component node. fn may return a replacement or None to keep."""

    def walk(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out = []
        for n in nodes:
            n = dict(n)
            for key in ("components", "items"):
                child = n.get(key)
                if _is_component_list(child):
                    n[key] = walk(child)
            if isinstance(n.get("component"), dict):
                n["component"] = walk([n["component"]])[0]
            if isinstance(n.get("accessory"), dict):
                n["accessory"] = walk([n["accessory"]])[0]
            replaced = fn(n)
            out.append(replaced if replaced is not None else n)
        return out

    return walk(components)


def count_payload_components(components: list[dict[str, Any]]) -> int:
    """Count every component in a raw payload, including nested ones."""
    total = 0

    def walk(nodes: list[dict[str, Any]]) -> None:
        nonlocal total
        for n in nodes:
            total += 1
            for key in ("components", "items"):
                child = n.get(key)
                if _is_component_list(child):
                    walk(child)
            for key in ("component", "accessory"):
                if isinstance(n.get(key), dict):
                    walk([n[key]])

    walk(components)
    return total
