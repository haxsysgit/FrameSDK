"""Schema validator — validates FRAME YAML data against JSON Schema definitions.

Uses jsonschema library. Fails on type errors, missing required fields, and enum
violations. Warns on missing optional fields and unknown fields.

Cross-file $ref links (./frame.schema.json) are resolved locally from the
schemas/json/ directory — no network requests.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as JsonschemaError
from referencing import Registry, Resource

from frame.validators.result import ValidationResult


# ---------------------------------------------------------------------------
# Schema loading with local $ref resolution
# ---------------------------------------------------------------------------

def _schemas_dir() -> Path:
    """Locate the schemas directory bundled with the package."""
    this_file = Path(__file__).resolve()
    # frame/validators/schema_validator.py → frame/validators → frame/
    package_root = this_file.parent.parent
    schemas = package_root / "schemas"
    if not schemas.is_dir():
        raise FileNotFoundError(
            f"FRAME schemas directory not found at {schemas}. "
            f"Expected frame/schemas/ in the frame-py package."
        )
    return schemas


# Pre-load all schemas into a local registry so cross-file $ref links resolve
# without network requests. Each schema gets registered under its $id URI.
def _build_registry() -> Registry:
    """Load all 6 JSON schemas into a referencing.Registry for local $ref resolution."""
    resources: list[tuple[str, Resource]] = []
    schemas_dir = _schemas_dir()
    for schema_file in sorted(schemas_dir.glob("*.schema.json")):
        schema = json.loads(schema_file.read_text())
        schema_uri = schema.get("$id", "")
        if schema_uri:
            resources.append((schema_uri, Resource.from_contents(schema)))
    return Registry().with_resources(resources)


# Build once at module load time
_SCHEMA_REGISTRY = _build_registry()


def _load_validator(file_stem: str) -> Draft202012Validator:
    """Load a FRAME JSON Schema and return a validator with local $ref resolution."""
    schema_path = _schemas_dir() / f"{file_stem}.schema.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    schema = json.loads(schema_path.read_text())
    return Draft202012Validator(schema, registry=_SCHEMA_REGISTRY)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_against_schema(data: dict, file_stem: str) -> ValidationResult:
    """Validate FRAME data against its JSON Schema.

    Args:
        data: Clean dict from the translator (YAML quirks already resolved).
        file_stem: One of 'facts', 'rules', 'map', 'expect', 'acts'.

    Returns:
        ValidationResult with errors for type/enum/required violations,
        warnings for missing optional fields.
    """
    result = ValidationResult()
    validator = _load_validator(file_stem)

    # Collect errors manually so we can classify by code
    for e in validator.iter_errors(data):
        path = ".".join(str(p) for p in e.absolute_path) if e.absolute_path else "$"
        code = _map_error_code(e)

        if code in ("missing_required", "type_error", "enum_error", "const_error"):
            result.add_error(
                path=path or file_stem,
                message=e.message,
                code=code,
                expected=str(e.validator_value) if e.validator_value else None,
                actual=str(e.instance)[:200] if e.instance is not None else None,
            )
        else:
            result.add_warning(path=path or file_stem, message=e.message, code=code)

    return result


def _map_error_code(error: JsonschemaError) -> str:
    """Map a jsonschema error to our validation code system."""
    validator = error.validator
    if validator == "required":
        return "missing_required"
    if validator in ("type", "pattern", "format"):
        return "type_error"
    if validator == "enum":
        return "enum_error"
    if validator == "const":
        return "const_error"
    if validator == "maxLength":
        return "limit_exceeded"
    return "schema_error"  # Catch-all for unexpected validation failures


# ---------------------------------------------------------------------------
# Convenience: validate a YAML file directly
# ---------------------------------------------------------------------------


def validate_yaml_file(file_path: str | Path) -> ValidationResult:
    """Validate a single YAML FRAME file against its schema.

    Parses YAML, normalizes quirks, then validates.
    """
    path = Path(file_path)
    yaml_data = yaml.safe_load(path.read_text())
    if not yaml_data or not isinstance(yaml_data, dict):
        result = ValidationResult()
        result.add_error(str(path), "File is empty or not a YAML object", "type_error")
        return result

    stem = path.stem  # 'facts' from 'facts.yaml'
    from frame.translators.normalizer import normalize_dict
    clean = normalize_dict(yaml_data)
    return validate_against_schema(clean, stem)
