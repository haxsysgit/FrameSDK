"""Character limit validator -- enforces maxLength on FRAME fields.

Core governance fields (ids, names, rules, checks, command_refs, pass_conditions)
are enforced -- exceeding their maxLength blocks the load.

Advisory/descriptive fields (code_style, git, architecture notes, environment
descriptions) are warned -- the load continues but the caller sees the warning.

Character limits are defined in the finalized schema. This validator checks them.
"""

from __future__ import annotations

from framesdkpy.validators.result import ValidationResult


# ---------------------------------------------------------------------------
# Field limit registry
# ---------------------------------------------------------------------------
# Each entry: (dotted_path, max_chars, enforced_or_advisory)
# Core governance fields: enforced (error if exceeded)
# Descriptive blocks: advisory (warning if exceeded)

_FIELD_LIMITS: list[tuple[str, int, str]] = [
    # Core governance fields -- enforced
    ("*.id", 100, "enforced"),
    ("*.name", 100, "enforced"),
    ("facts.profile.name", 100, "enforced"),
    ("facts.profile.summary", 300, "enforced"),
    ("facts.sources[].id", 100, "enforced"),
    ("facts.sources[].path", 200, "enforced"),
    ("facts.quirks[].id", 100, "enforced"),
    ("facts.open_questions[].id", 100, "enforced"),
    ("rules.rules[].id", 100, "enforced"),
    ("rules.policies[].id", 100, "enforced"),
    ("rules.donts[].id", 100, "enforced"),
    ("rules.ask_first[].id", 100, "enforced"),
    ("rules.hints[].id", 100, "enforced"),
    ("rules.commands.*.run", 500, "enforced"),
    ("rules.commands.*.purpose", 300, "enforced"),
    ("map.groups[].id", 100, "enforced"),
    ("map.groups[].label", 150, "enforced"),
    ("map.groups[].paths[]", 300, "enforced"),
    ("map.entrypoints[].id", 100, "enforced"),
    ("expect.must_hold[].id", 100, "enforced"),
    ("expect.checks.*.name", 100, "enforced"),
    ("expect.checks.*.command_ref", 200, "enforced"),
    ("expect.checks.*.pass_condition", 200, "enforced"),
    ("expect.proof[].id", 100, "enforced"),
    ("acts.runs[].id", 100, "enforced"),
    ("acts.runs[].actor", 100, "enforced"),
    ("acts.blockers[].id", 100, "enforced"),

    # Advisory blocks -- warned
    ("facts.architecture.summary", 500, "advisory"),
    ("facts.architecture.*", 500, "advisory"),
    ("facts.technology.*", 100, "advisory"),
    ("facts.sources[].purpose", 300, "advisory"),
    ("facts.quirks[].description", 200, "advisory"),
    ("facts.quirks[].why", 300, "advisory"),
    ("facts.open_questions[].question", 300, "advisory"),
    ("facts.open_questions[].context", 300, "advisory"),
    ("rules.rules[].rule", 500, "advisory"),
    ("rules.policies[].name", 150, "advisory"),
    ("rules.policies[].rule", 500, "advisory"),
    ("rules.donts[].rule", 300, "advisory"),
    ("rules.ask_first[].trigger", 300, "advisory"),
    ("rules.ask_first[].reason", 300, "advisory"),
    ("rules.hints[].hint", 300, "advisory"),
    ("rules.code_style", 1000, "advisory"),
    ("rules.git", 1000, "advisory"),
    ("map.structure", 800, "advisory"),
    ("map.paths[].path", 200, "advisory"),
    ("map.paths[].purpose", 300, "advisory"),
    ("map.entrypoints[].path", 200, "advisory"),
    ("map.managed_paths[].path", 200, "advisory"),
    ("expect.outcomes.*.summary", 300, "advisory"),
    ("expect.must_hold[].statement", 300, "advisory"),
    ("expect.checks.*.what", 300, "advisory"),
    ("expect.checks.*.how", 200, "advisory"),
    ("expect.proof[].description", 300, "advisory"),
    ("acts.summary", 500, "advisory"),
    ("acts.runs[].goal", 300, "advisory"),
    ("acts.runs[].input_summary", 300, "advisory"),
    ("acts.runs[].output_summary", 300, "advisory"),
    ("acts.runs[].checks[].reason", 200, "advisory"),
    ("acts.blockers[].description", 300, "advisory"),
]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_limits(data: dict, file_stem: str) -> ValidationResult:
    """Check character limits on all fields in a FRAME data dict.

    Walks the dict tree, matches each value against the field limit registry,
    and reports any violations.
    """
    result = ValidationResult()
    _walk_and_check(data, file_stem, result)
    return result


def _walk_and_check(data, path: str, result: ValidationResult):
    """Recursively walk a dict and check field limits."""
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}"
            _check_value(value, current_path, result)
            _walk_and_check(value, current_path, result)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            current_path = f"{path}[{i}]"
            _check_value(item, current_path, result)
            _walk_and_check(item, current_path, result)


def _check_value(value, path: str, result: ValidationResult):
    """Check a single value against the limit registry."""
    if not isinstance(value, str):
        return

    # Find matching limit rules for this path
    for pattern, max_chars, severity in _FIELD_LIMITS:
        if not _path_matches(path, pattern):
            continue

        if len(value) > max_chars:
            msg = f"Field exceeds maxLength of {max_chars} chars (got {len(value)})"
            if severity == "enforced":
                result.add_error(
                    path=path, message=msg, code="limit_exceeded",
                    expected=f"maxLength: {max_chars}", actual=f"length: {len(value)}",
                )
            else:
                result.add_warning(path=path, message=msg, code="limit_advisory")
            break  # First match wins -- don't report the same field twice


def _path_matches(actual_path: str, pattern: str) -> bool:
    """Check if a dot-separated path matches a pattern with * and [] wildcards.

    Pattern: 'facts.profile.name' matches exactly.
    Pattern: 'facts.sources[].id' matches any index: 'facts.sources[0].id'.
    Pattern: 'rules.commands.*.run' matches any command name.
    Pattern: 'facts.architecture.*' matches any architecture sub-field.
    Pattern: '*.id' matches any top-level field ending in '.id'.
    """
    # Normalize array indices: replace [0], [1], etc. with []
    import re
    actual_normalized = re.sub(r'\[\d+\]', '[]', actual_path)

    # Split both paths into segments
    actual_segs = actual_normalized.split(".")
    pattern_segs = pattern.split(".")

    if len(actual_segs) != len(pattern_segs):
        return False

    for a, p in zip(actual_segs, pattern_segs):
        if p == "*":
            continue  # Wildcard matches any segment
        if a != p:
            return False

    return True
