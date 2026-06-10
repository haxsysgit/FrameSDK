"""Cross-file validator -- checks consistency across all 5 FRAME files.

Verifies:
- All schema_version fields match
- All file/role fields match expected values (facts file must have file: facts)
"""

from __future__ import annotations

from framesdkpy.validators.result import ValidationResult


_EXPECTED_FILE_MAP = {
    "facts": "facts",
    "rules": "rules",
    "map": "map",
    "expect": "expect",
    "acts": "acts",
}

_EXPECTED_ROLE_MAP = {
    "facts": "current_project_truth",
    "rules": "project_instruction_blueprint",
    "map": "repo_context_map",
    "expect": "project_correctness_contract",
    "acts": "checked_activity_record",
}


def validate_cross_file(parts: dict[str, dict]) -> ValidationResult:
    """Check cross-file consistency across all 5 translated FRAME parts.

    Args:
        parts: Dict mapping file stem to translated dict.
               e.g., {"facts": {...}, "rules": {...}, ...}

    Returns:
        ValidationResult with errors for mismatched versions or file/role fields.
    """
    result = ValidationResult()

    # Gather schema_version from every file that has a frame header
    versions: dict[str, str] = {}
    for stem, data in parts.items():
        header = data.get("frame", {})
        version = header.get("schema_version")
        if version:
            versions[stem] = version

    # All present schema_versions must match
    if len(set(versions.values())) > 1:
        details = ", ".join(f"{s}={v}" for s, v in versions.items())
        result.add_error(
            path="frame.schema_version",
            message=f"Schema version mismatch across files: {details}",
            code="schema_version_mismatch",
        )

    # Each file's 'file' and 'role' fields must match expected values
    for stem, data in parts.items():
        header = data.get("frame", {})

        expected_file = _EXPECTED_FILE_MAP.get(stem)
        actual_file = header.get("file")
        if expected_file and actual_file and actual_file != expected_file:
            result.add_error(
                path=f"{stem}.frame.file",
                message=f"File field mismatch in {stem}.yaml",
                code="file_role_mismatch",
                expected=expected_file,
                actual=actual_file,
            )

        expected_role = _EXPECTED_ROLE_MAP.get(stem)
        actual_role = header.get("role")
        if expected_role and actual_role and actual_role != expected_role:
            result.add_error(
                path=f"{stem}.frame.role",
                message=f"Role field mismatch in {stem}.yaml",
                code="file_role_mismatch",
                expected=expected_role,
                actual=actual_role,
            )

    return result
