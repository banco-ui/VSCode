"""Snapshot Diff Engine (Phase 7).

Recursive, deterministic diff between two ServerInventory snapshots.
"""
from __future__ import annotations

from typing import Any

from ..models.inventory import ServerInventory
from .models import FieldDiff, SnapshotDiff


def compute_snapshot_diff(
    snapshot_a_id: str,
    snapshot_b_id: str,
    inventory_a: ServerInventory,
    inventory_b: ServerInventory,
) -> SnapshotDiff:
    """Compute a deterministic diff between two inventory snapshots.

    Args:
        snapshot_a_id: ID of the older snapshot.
        snapshot_b_id: ID of the newer snapshot.
        inventory_a: Older inventory.
        inventory_b: Newer inventory.

    Returns:
        SnapshotDiff with changed, added, and removed fields.
    """
    dict_a = inventory_a.model_dump(by_alias=True)
    dict_b = inventory_b.model_dump(by_alias=True)

    changed_fields: list[FieldDiff] = []
    added_fields: list[str] = []
    removed_fields: list[str] = []

    all_paths = _get_all_paths(dict_a, dict_b)

    for path in sorted(all_paths):
        val_a = _get_by_path(dict_a, path)
        val_b = _get_by_path(dict_b, path)

        if val_a is _MISSING and val_b is not _MISSING:
            added_fields.append(path)
        elif val_a is not _MISSING and val_b is _MISSING:
            removed_fields.append(path)
        elif val_a is not _MISSING and val_b is not _MISSING:
            if not _values_equal(val_a, val_b):
                changed_fields.append(FieldDiff(
                    field_path=path,
                    old_value=val_a,
                    new_value=val_b,
                    change_type="CHANGED",
                ))

    return SnapshotDiff(
        snapshot_a_id=snapshot_a_id,
        snapshot_b_id=snapshot_b_id,
        changed_fields=changed_fields,
        added_fields=added_fields,
        removed_fields=removed_fields,
    )


# Sentinel for missing values
_MISSING = object()


def _get_all_paths(dict_a: dict, dict_b: dict, prefix: str = "") -> set[str]:
    """Get all unique paths from both dicts."""
    paths: set[str] = set()

    def _collect_paths(d: dict, prefix: str = "") -> None:
        for key, value in d.items():
            path = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                _collect_paths(value, path)
            elif isinstance(value, list):
                # For lists, we compare length and items by index
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        _collect_paths(item, f"{path}[{i}]")
                    else:
                        paths.add(f"{path}[{i}]")
                paths.add(f"{path}._count")
            else:
                paths.add(path)

    _collect_paths(dict_a)
    _collect_paths(dict_b)
    return paths


def _get_by_path(d: dict, path: str) -> Any:
    """Get a value by dotted path, supporting list indexing."""
    parts = _parse_path(path)
    current: Any = d
    for part in parts:
        if isinstance(part, int):
            if not isinstance(current, list) or part >= len(current):
                return _MISSING
            current = current[part]
        else:
            if not isinstance(current, dict) or part not in current:
                return _MISSING
            current = current[part]
    return current


def _parse_path(path: str) -> list:
    """Parse a dotted path with list indices into parts."""
    parts: list = []
    current = ""
    i = 0
    while i < len(path):
        c = path[i]
        if c == ".":
            if current:
                parts.append(current)
                current = ""
        elif c == "[":
            if current:
                parts.append(current)
                current = ""
            j = path.index("]", i)
            parts.append(int(path[i + 1:j]))
            i = j
        else:
            current += c
        i += 1
    if current:
        parts.append(current)
    return parts


def _values_equal(a: Any, b: Any) -> bool:
    """Compare values for equality with type coercion."""
    if a == b:
        return True
    # Numeric comparison with tolerance
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) < 0.01
    # String comparison (case-insensitive)
    if isinstance(a, str) and isinstance(b, str):
        return a.strip().lower() == b.strip().lower()
    return False
