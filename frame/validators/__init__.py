"""FRAME validators — schema, character limits, and cross-file consistency.

Public API:
    validate_file("facts.yaml")        → ValidationResult (single file)
    validate_frame(".haxaml/")         → ValidationResult (all 5 + cross-file)
    validate_against_schema(data, "facts") → ValidationResult (in-memory)
    validate_limits(data, "facts")         → ValidationResult (in-memory)
"""

from frame.validators.result import ValidationResult, ValidationError, ValidationWarning
from frame.validators.schema_validator import validate_against_schema, validate_yaml_file
from frame.validators.limits_validator import validate_limits
from frame.validators.cross_file_validator import validate_cross_file


def validate_file(file_path: str) -> ValidationResult:
    """Validate a single FRAME YAML file against schema + limits.

    Does NOT run cross-file checks (only one file).
    """
    result = validate_yaml_file(file_path)

    # Also run limits validation
    import yaml
    from pathlib import Path
    from frame.translators.normalizer import normalize_dict

    path = Path(file_path)
    raw = yaml.safe_load(path.read_text())
    if raw and isinstance(raw, dict):
        clean = normalize_dict(raw)
        limits_result = validate_limits(clean, path.stem)
        result = result.merge(limits_result)

    return result


def validate_frame(dir_path: str) -> ValidationResult:
    """Validate all 5 FRAME files in a directory + cross-file consistency.

    Steps:
    1. Schema validation for each file
    2. Character limit validation for each file
    3. Cross-file consistency (versions, file/role matching)
    """
    from pathlib import Path
    from frame.translators.yaml_to_json import translate_directory

    # Translate all 5 files to clean dicts
    parts = translate_directory(dir_path)

    result = ValidationResult()

    # Schema + limits for each file
    for stem, data in parts.items():
        result = result.merge(validate_against_schema(data, stem))
        result = result.merge(validate_limits(data, stem))

    # Cross-file consistency
    result = result.merge(validate_cross_file(parts))

    return result


__all__ = [
    "ValidationResult",
    "ValidationError",
    "ValidationWarning",
    "validate_file",
    "validate_frame",
    "validate_against_schema",
    "validate_limits",
    "validate_cross_file",
]
