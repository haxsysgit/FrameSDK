"""YAML reader -- discovers and parses FRAME YAML files from a directory.

Strict single-directory discovery: exactly 5 files must be present.
No fuzzy matching, no parent/sibling search, no scattered file pickup.
"""

from __future__ import annotations

from pathlib import Path

import yaml


# All 5 are discovered. Facts and Rules are required for any project.
# Map is required if the repo has structure; empty repos can omit it.
# Expect and Acts grow over time.
_EXPECTED_FILES = ["facts", "rules", "map", "expect", "acts"]


def discover_frame_dir(dir_path: str | Path) -> dict[str, Path]:
    """Verify exactly 5 FRAME YAML files exist in a directory.

    Returns a dict mapping file stem to resolved Path. Raises FileNotFoundError
    if the directory doesn't exist or any expected file is missing.
    """
    directory = Path(dir_path).resolve()
    if not directory.is_dir():
        raise FileNotFoundError(f"FRAME directory not found: {directory}")

    found: dict[str, Path] = {}
    for stem in _EXPECTED_FILES:
        yaml_path = directory / f"{stem}.yaml"
        if not yaml_path.is_file():
            raise FileNotFoundError(
                f"Missing FRAME file: {stem}.yaml in {directory}. "
                f"All 5 files (facts, rules, map, expect, acts) must be in the same directory."
            )
        found[stem] = yaml_path

    return found


def read_raw_yaml(file_stems: dict[str, Path]) -> dict[str, dict]:
    """Parse YAML files into raw Python dicts.

    Returns a dict mapping file stem to raw parsed dict. YAML quirks (yes→True,
    ~→None) are handled by the normalizer downstream -- this is raw parsing only.
    """
    raw: dict[str, dict] = {}
    for stem, path in file_stems.items():
        data = yaml.safe_load(path.read_text())
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise ValueError(f"Expected YAML object in {stem}.yaml, got {type(data).__name__}")
        raw[stem] = data
    return raw
