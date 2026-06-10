"""FRAME loader -- reads YAML from a directory and returns a typed FRAME object.

The full pipeline: discover → parse → normalize → validate → assemble → return.

Public API:
    load_frame(".haxaml/") → FRAME
"""

from __future__ import annotations

from pathlib import Path

from framesdkpy.loaders.yaml_reader import discover_frame_dir, read_raw_yaml
from framesdkpy.loaders.assembler import assemble_frame, FrameLoadError
from framesdkpy.translators.normalizer import normalize_dict
from framesdkpy.validators import validate_against_schema, validate_limits


def load_frame(dir_path: str | Path) -> "FRAME":
    """Load all 5 FRAME YAML files from a directory and return a typed FRAME object.

    Pipeline:
    1. Discover 5 files in the directory (strict -- all must be present)
    2. Parse raw YAML into dicts
    3. Normalize each dict (YAML quirks → clean types)
    4. Validate each dict against JSON Schema + character limits
    5. Assemble into a typed FRAME object (cross-file checks, model construction)

    Raises:
        FileNotFoundError: Directory doesn't exist or a file is missing.
        FrameLoadError: Validation failed (schema, limits, or cross-file).

    Returns:
        FRAME with facts populated and optional other parts.
    """
    from framesdkpy.models.frame_model import FRAME

    # 1. Discover
    files = discover_frame_dir(dir_path)

    # 2. Parse raw YAML
    raw = read_raw_yaml(files)

    # 3-4. Normalize + validate each file
    validated: dict[str, dict] = {}
    all_errors: list = []
    all_warnings: list = []

    for stem, raw_dict in raw.items():
        clean = normalize_dict(raw_dict)

        # Schema validation
        schema_result = validate_against_schema(clean, stem)
        if not schema_result.is_valid():
            all_errors.extend(schema_result.errors)
        all_warnings.extend(schema_result.warnings)

        # Character limit validation
        limits_result = validate_limits(clean, stem)
        if not limits_result.is_valid():
            all_errors.extend(limits_result.errors)
        all_warnings.extend(limits_result.warnings)

        validated[stem] = clean

    # Block on any validation errors
    if all_errors:
        raise FrameLoadError(
            f"Validation failed with {len(all_errors)} error(s): "
            + "; ".join(e.message for e in all_errors[:5]),
            errors=all_errors,
            warnings=all_warnings,
        )

    # 5. Assemble (includes cross-file check)
    return assemble_frame(validated)


__all__ = ["load_frame", "FrameLoadError"]
