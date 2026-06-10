# frame-py Validators — Specification

**Status:** Agreed. Code follows this spec.
**Date:** 2026-06-10

---

## Job

Validators verify that FRAME data is structurally correct. They check types, required fields, enums, character limits, and cross-file consistency. They are called by the loader during ingestion, and callable independently for ad-hoc validation.

Validators do NOT:
- Execute commands (Haxaml's job)
- Evaluate `pass_condition` against agent output (Haxaml's job)
- Verify agent behavior (Haxaml's job)
- Record run history (Haxaml's job)

Validators DO:
- Validate YAML data against the JSON Schema
- Enforce type constraints, required fields, enums
- Enforce character limits (core fields)
- Check cross-file consistency (schema_version, file/role alignment)
- Return structured result objects with errors and warnings

---

## Architecture

```
frame/validators/
├── __init__.py           ← Public API: validate_frame(), validate_file(), ValidationResult
├── schema_validator.py   ← JSON Schema validation against schemas/json/
├── limits_validator.py   ← Character limit enforcement (core + advisory)
├── cross_file_validator.py ← Cross-file consistency checks
└── result.py             ← ValidationResult, ValidationError, ValidationWarning
```

Flow:

```
Directory path or file path
  ↓
schema_validator checks each YAML against its JSON Schema:
  -- Type errors: FAIL (blocks load)
  -- Missing required fields: FAIL (blocks load)
  -- Wrong enum values: FAIL (blocks load)
  -- Missing optional fields: WARN (load continues)
  ↓
limits_validator checks character limits:
  -- Core field exceeds maxLength: FAIL (blocks load)
  -- Advisory field exceeds maxLength: WARN (load continues)
  ↓
cross_file_validator checks across all 5 files:
  -- All schema_version fields match: FAIL if not
  -- file/role fields match expected values: FAIL if not
  ↓
Returns ValidationResult
  -- errors: list[ValidationError]   (blocking)
  -- warnings: list[ValidationWarning] (non-blocking)
  -- is_valid(): bool                (True if no errors)
```

---

## Decisions

### D12: Fail on type errors, warn on missing optional fields

Schema validation is strict where it matters:
- Wrong type (string where int expected) → error, load fails
- Missing required field → error, load fails
- Wrong enum value → error, load fails
- Missing optional field → warning, load continues
- Extra unknown field → warning, load continues (not an error — allows future schema extensions)

### D13: Support both per-file and whole-FRAME validation

```python
# Per-file: quick check during development
result = validate_file("facts.yaml")

# Whole-FRAME: complete check including cross-file consistency
result = validate_frame(".haxaml/")
```

Per-file validation skips cross-file checks. Whole-FRAME validation includes everything.

### D14: Return result objects, not exceptions

```python
result = validate_frame(".haxaml/")

if not result.is_valid():
    for err in result.errors:
        print(f"FAIL: {err.path} — {err.message}")
    for warn in result.warnings:
        print(f"WARN: {warn.path} — {warn.message}")
    # Caller decides: abort, fix and retry, or continue with warnings
else:
    print("All checks passed")
```

The caller owns the decision. The validator reports. No exceptions for validation failures.

---

## Data model

### result.py

```python
@dataclass(slots=True)
class ValidationError:
    """A blocking validation failure. Must be fixed before load."""
    path: str                    # Dotted path to the failing field, e.g. "facts.profile.name"
    message: str                 # Human-readable explanation
    code: str                    # Machine-readable code: "missing_required", "type_error", "enum_error", "limit_exceeded"
    expected: str | None         # What was expected, e.g. "string", "maxLength: 100"
    actual: str | None           # What was found, e.g. "int", "length: 245"

@dataclass(slots=True)
class ValidationWarning:
    """A non-blocking issue. Load continues."""
    path: str
    message: str
    code: str                    # "missing_optional", "limit_advisory", "unknown_field"

@dataclass(slots=True)
class ValidationResult:
    """Aggregate result from all validators."""
    errors: list[ValidationError]
    warnings: list[ValidationWarning]

    def is_valid(self) -> bool:
        """True if no blocking errors. Warnings don't block."""
        return len(self.errors) == 0

    def is_clean(self) -> bool:
        """True if no errors AND no warnings."""
        return len(self.errors) == 0 and len(self.warnings) == 0

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """Combine results from multiple validators."""
        return ValidationResult(
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
        )
```

---

## Public API

```python
from frame.validators import validate_frame, validate_file, ValidationResult

# Whole-FRAME validation (all files + cross-file checks)
result: ValidationResult = validate_frame("/path/to/.haxaml")

# Per-file validation (single file only, no cross-file checks)
result: ValidationResult = validate_file("/path/to/facts.yaml")

# Check result
if result.is_valid():
    # Load is safe — no blocking errors
    ...
else:
    # Fix errors before loading
    for err in result.errors:
        print(f"{err.path}: {err.message} (expected {err.expected}, got {err.actual})")
```

---

## Validation codes

| code | severity | meaning |
|---|---|---|
| `missing_required` | error | Required field is absent |
| `type_error` | error | Field has wrong type |
| `enum_error` | error | Value not in allowed enum |
| `limit_exceeded` | error | Core field exceeds maxLength |
| `schema_version_mismatch` | error | Cross-file schema_version mismatch |
| `file_role_mismatch` | error | file/role fields don't match expected |
| `missing_optional` | warning | Optional field missing |
| `limit_advisory` | warning | Advisory field exceeds maxLength |
| `unknown_field` | warning | Field not in schema (allows forward compat) |
