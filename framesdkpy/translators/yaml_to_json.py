"""YAML → JSON translator — reads FRAME YAML files and produces clean JSON.

Uses the normalizer to resolve YAML quirks, then validates the output against
the JSON Schema shape. Returns a clean dict ready for the validator or assembler.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from framesdkpy.translators.normalizer import normalize_dict


# Use YAML 1.2 safe loader — doesn't parse dates, octal, or sexagesimal.
# This prevents YAML quirks from reaching the normalizer.
_YAML_LOADER = yaml.SafeLoader


def translate_to_dict(yaml_string: str) -> dict:
    """Parse a YAML string into a clean JSON-compatible dict.

    Handles all YAML → JSON normalization per the translators spec.
    Raises TranslationError on ambiguous input.
    """
    raw = yaml.load(yaml_string, Loader=_YAML_LOADER)
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError(f"Expected YAML object, got {type(raw).__name__}")
    return normalize_dict(raw)


def translate_file(file_path: str | Path) -> dict:
    """Read a YAML file and translate to a clean JSON-compatible dict.

    Args:
        file_path: Path to a .yaml FRAME file (facts.yaml, rules.yaml, etc.)

    Returns:
        Clean dict with all YAML quirks resolved.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"FRAME file not found: {path}")
    if path.suffix not in (".yaml", ".yml"):
        raise ValueError(f"Expected .yaml file, got {path.suffix}: {path}")

    yaml_string = path.read_text()
    return translate_to_dict(yaml_string)


def translate_directory(dir_path: str | Path) -> dict[str, dict]:
    """Read all 5 FRAME YAML files from a directory.

    Args:
        dir_path: Directory containing facts.yaml, rules.yaml, map.yaml,
                  expect.yaml, acts.yaml.

    Returns:
        Dict mapping file stem to translated dict, e.g.:
        {"facts": {...}, "rules": {...}, "map": {...}, "expect": {...}, "acts": {...}}
    """
    directory = Path(dir_path)
    if not directory.is_dir():
        raise FileNotFoundError(f"FRAME directory not found: {directory}")

    expected_files = ["facts", "rules", "map", "expect", "acts"]
    result: dict[str, dict] = {}

    for stem in expected_files:
        yaml_file = directory / f"{stem}.yaml"
        if not yaml_file.exists():
            raise FileNotFoundError(
                f"Missing FRAME file: {stem}.yaml in {directory}. "
                f"All 5 files must be in the same directory."
            )
        result[stem] = translate_file(yaml_file)

    return result


def translate_to_json_string(yaml_string: str, indent: int = 2) -> str:
    """Parse YAML and return a JSON string directly."""
    data = translate_to_dict(yaml_string)
    return json.dumps(data, indent=indent, ensure_ascii=False)
