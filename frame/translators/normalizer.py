"""YAML type normalizer — resolves YAML quirks into clean JSON-compatible types.

Handles the full YAML 1.2 quirk table defined in the translators spec:
  yes/no → True/False
  ~/null → None
  Date-like strings preserved as strings
  Empty strings and empty fields handled correctly

Raises TranslationError on ambiguous input (on/off).
"""

from __future__ import annotations

from typing import Any


class TranslationError(ValueError):
    """Raised when YAML input is ambiguous and cannot be safely translated."""

    def __init__(self, path: str, value: Any, reason: str):
        self.path = path
        self.value = value
        self.reason = reason
        super().__init__(f"{path}: {reason} (got {value!r})")


def normalize_yaml_value(value: Any, path: str = "$") -> Any:
    """Resolve a single YAML value to a JSON-compatible type.

    Recursively handles dicts and lists. The path argument tracks position
    for error messages — use normalize_dict() for top-level entry.
    """
    # Dict: recurse into values, tracking keys for error paths
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for k, v in value.items():
            result[k] = normalize_yaml_value(v, f"{path}.{k}")
        return result

    # List: recurse into items
    if isinstance(value, list):
        return [normalize_yaml_value(item, f"{path}[{i}]") for i, item in enumerate(value)]

    # None / null
    if value is None:
        return None

    # String: check for YAML quirks
    if isinstance(value, str):
        return _normalize_string(value, path)

    # Numbers and booleans pass through as-is (YAML already parsed them correctly)
    return value


def _normalize_string(value: str, path: str) -> Any:
    """Normalize a YAML string — handle yes/no, null, empty, date-like."""

    # Empty string: preserve as-is (not coerced to null)
    if value == "":
        return ""

    # Explicit null values
    if value.lower() in ("null", "~"):
        return None

    # YAML 1.2 booleans (only yes/no — on/off are ambiguous and rejected)
    if value.lower() in ("yes", "true", "y"):
        return True
    if value.lower() in ("no", "false", "n"):
        return False

    # Ambiguous: on/off are YAML 1.1 booleans. YAML 1.2 doesn't treat them as
    # booleans, but some parsers do. We fail loudly rather than guessing.
    if value.lower() in ("on", "off"):
        raise TranslationError(
            path, value,
            "'on'/'off' is ambiguous in YAML. Use explicit 'true' or 'false' or quote as string.",
        )

    # Date-like strings (YYYY-MM-DD, YYYY/MM/DD): YAML parsers may convert these
    # to datetime objects. We preserve them as strings for FRAME consistency.
    # The caller's YAML loader should use a loader that doesn't auto-parse dates.
    # If a datetime slips through (parsed by the YAML lib), we catch it above in
    # the type check — datetimes are not strings and pass through as-is.

    return value


def normalize_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize an entire YAML dict. Entry point for the translator."""
    return normalize_yaml_value(data, "$")


def normalize_list(data: list[Any]) -> list[Any]:
    """Normalize a YAML list. Convenience for array-only files."""
    return normalize_yaml_value(data, "$")
