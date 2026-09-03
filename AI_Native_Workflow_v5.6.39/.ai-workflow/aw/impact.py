"""Declared-dependency impact-cone helpers."""

from __future__ import annotations

from collections import deque
from typing import Any, Mapping, Set


def dependency_impact_cone(
    plan_nodes: Mapping[str, Mapping[str, Any]], changed_keys: set[str] | list[str] | tuple[str, ...]
) -> Set[str]:
    """Return the downstream cone of nodes that directly read ``changed_keys``.

    Each plan node may declare ``reads`` and ``depends_on``.  The helper is
    intentionally structural: sound retention additionally requires complete
    declarations, version-bound evidence, deterministic execution or fresh
    verification, and no undeclared mutable shared state.
    """

    changed = set(changed_keys)
    direct = {
        node_id
        for node_id, node in plan_nodes.items()
        if set(node.get("reads", [])) & changed
    }

    children: dict[str, set[str]] = {node_id: set() for node_id in plan_nodes}
    for node_id, node in plan_nodes.items():
        for parent in node.get("depends_on", []):
            if parent in children:
                children[parent].add(node_id)

    impacted = set(direct)
    queue: deque[str] = deque(sorted(direct))
    while queue:
        current = queue.popleft()
        for child in sorted(children.get(current, ())):
            if child not in impacted:
                impacted.add(child)
                queue.append(child)
    return impacted
