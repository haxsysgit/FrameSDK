"""Shared base class for all FRAME models.

Provides serialization (to_dict, to_json) and developer-friendly repr.
Every FRAME model inherits from FrameBaseModel. This ensures uniform
output format across all five parts regardless of which tool consumes them.

Null preservation: to_dict() keeps nulls in the output so the JSON shape
is always complete. Cross-language tools (frame-js, frame-cpp) can rely
on every key existing even if its value is null.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, fields, is_dataclass
from typing import Any


@dataclass(slots=True)
class FrameBaseModel:
    """All FRAME models inherit this for uniform serialization.

    Serialization preserves nulls -- if a field is None, the key appears in
    the dict with a null value. This keeps the JSON shape consistent across
    tools and languages.
    """

    def to_dict(self) -> dict[str, Any]:
        """Recursive serialization to a JSON-compatible dict. Preserves nulls.

        Nested FrameBaseModel instances and lists of models are handled
        recursively. Regular dicts, lists, strings, and primitives pass through.
        """
        result: dict[str, Any] = {}
        for field in fields(self):
            value = getattr(self, field.name)
            result[field.name] = self._serialize_value(value)
        return result

    def to_json(self, indent: int = 2) -> str:
        """Serialize to a JSON string. Passes through to_dict() first."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Recursively convert a value to a JSON-safe representation.

        - FrameBaseModel → call to_dict()
        - list of models → list of dicts
        - dict → recurse into values
        - None, str, int, float, bool → pass through
        """
        if isinstance(value, FrameBaseModel):
            return value.to_dict()
        if isinstance(value, list):
            return [FrameBaseModel._serialize_value(item) for item in value]
        if isinstance(value, dict):
            return {k: FrameBaseModel._serialize_value(v) for k, v in value.items()}
        return value  # Primitive: str, int, float, bool, None

    def __repr__(self) -> str:
        """Developer-friendly display showing class name and field count."""
        field_names = [f.name for f in fields(self)]
        return f"{type(self).__name__}({', '.join(field_names)})"
