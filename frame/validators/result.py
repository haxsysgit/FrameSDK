"""Validation result objects — returned by all validators.

Validators never raise exceptions for validation failures. They return
ValidationResult objects. The caller decides: abort, fix and retry,
or continue with warnings.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ValidationError:
    """A blocking validation failure. Must be fixed before loading."""

    path: str
    """Dotted path to the failing field, e.g. 'facts.profile.name'."""

    message: str
    """Human-readable explanation of what went wrong."""

    code: str
    """Machine-readable code: 'missing_required', 'type_error', 'enum_error', 'limit_exceeded'."""

    expected: str | None = None
    """What was expected, e.g. 'string', 'maxLength: 100'."""

    actual: str | None = None
    """What was found, e.g. 'int', 'length: 245'."""


@dataclass(slots=True)
class ValidationWarning:
    """A non-blocking issue. Load continues but the caller should know."""

    path: str
    """Dotted path to the field with the warning."""

    message: str
    """Human-readable explanation."""

    code: str
    """Machine-readable code: 'missing_optional', 'limit_advisory', 'unknown_field'."""


@dataclass(slots=True)
class ValidationResult:
    """Aggregate result from all validators in the pipeline.

    is_valid() returns True if there are zero blocking errors.
    is_clean() returns True if there are no errors AND no warnings.
    merge() combines results from multiple validators into one.
    """

    errors: list[ValidationError] = field(default_factory=list)
    """Blocking errors. The load cannot proceed until these are fixed."""

    warnings: list[ValidationWarning] = field(default_factory=list)
    """Non-blocking warnings. The load proceeds but the caller sees these."""

    def is_valid(self) -> bool:
        """True if no blocking errors. Warnings don't block."""
        return len(self.errors) == 0

    def is_clean(self) -> bool:
        """True if no errors AND no warnings."""
        return len(self.errors) == 0 and len(self.warnings) == 0

    def merge(self, other: ValidationResult) -> ValidationResult:
        """Combine results from multiple validators."""
        return ValidationResult(
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
        )

    def add_error(self, path: str, message: str, code: str,
                  expected: str | None = None, actual: str | None = None) -> None:
        """Convenience: add a blocking error."""
        self.errors.append(ValidationError(
            path=path, message=message, code=code,
            expected=expected, actual=actual,
        ))

    def add_warning(self, path: str, message: str, code: str) -> None:
        """Convenience: add a non-blocking warning."""
        self.warnings.append(ValidationWarning(
            path=path, message=message, code=code,
        ))

    def summary(self) -> str:
        """One-line summary for logging."""
        parts = []
        if self.errors:
            parts.append(f"{len(self.errors)} error(s)")
        if self.warnings:
            parts.append(f"{len(self.warnings)} warning(s)")
        if not parts:
            return "valid"
        return ", ".join(parts)
