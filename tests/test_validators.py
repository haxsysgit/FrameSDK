"""Tests for FRAME validators — schema, limits, cross-file consistency."""

import tempfile
from pathlib import Path

import pytest

from frame.validators import (
    ValidationResult, ValidationError, ValidationWarning,
    validate_file, validate_frame,
    validate_against_schema, validate_limits, validate_cross_file,
)


# ---------------------------------------------------------------------------
# ValidationResult tests
# ---------------------------------------------------------------------------


class TestValidationResult:
    """ValidationResult — construction, merging, summary."""

    def test_empty_result_is_valid(self):
        result = ValidationResult()
        assert result.is_valid()
        assert result.is_clean()

    def test_result_with_warnings_is_valid(self):
        result = ValidationResult()
        result.add_warning("test.path", "just a warning", "limit_advisory")
        assert result.is_valid()
        assert not result.is_clean()

    def test_result_with_errors_is_invalid(self):
        result = ValidationResult()
        result.add_error("test.path", "something broke", "type_error")
        assert not result.is_valid()
        assert not result.is_clean()

    def test_merge_combines_errors_and_warnings(self):
        r1 = ValidationResult()
        r1.add_error("a", "err1", "type_error")
        r1.add_warning("b", "warn1", "limit_advisory")

        r2 = ValidationResult()
        r2.add_error("c", "err2", "missing_required")
        r2.add_warning("d", "warn2", "unknown_field")

        merged = r1.merge(r2)
        assert len(merged.errors) == 2
        assert len(merged.warnings) == 2
        assert not merged.is_valid()

    def test_add_error_convenience(self):
        result = ValidationResult()
        result.add_error("a.b.c", "type mismatch", "type_error",
                         expected="string", actual="int")
        assert len(result.errors) == 1
        assert result.errors[0].expected == "string"
        assert result.errors[0].actual == "int"

    def test_summary_method(self):
        result = ValidationResult()
        assert result.summary() == "valid"

        result.add_error("a", "e", "type_error")
        assert "1 error(s)" in result.summary()
        assert "warning" not in result.summary()

        result.add_warning("b", "w", "limit_advisory")
        assert "error" in result.summary()
        assert "warning" in result.summary()


# ---------------------------------------------------------------------------
# Schema validator tests
# ---------------------------------------------------------------------------


class TestSchemaValidator:
    """validate_against_schema() — JSON Schema enforcement."""

    def test_valid_facts_passes_schema(self):
        """A mininal valid Facts dict passes schema validation."""
        data = {
            "frame": {"file": "facts", "schema_version": "0.3.0", "role": "current_project_truth", "status": "active"},
            "profile": {"name": "test", "summary": "A test project"},
            "architecture": {"summary": "single process"},
        }
        result = validate_against_schema(data, "facts")
        assert result.is_valid()

    def test_missing_required_field(self):
        """Missing profile should be caught."""
        data = {
            "frame": {"file": "facts", "schema_version": "0.3.0", "role": "current_project_truth", "status": "active"},
            # profile missing
        }
        result = validate_against_schema(data, "facts")
        assert not result.is_valid()
        assert any(e.code == "missing_required" for e in result.errors)

    def test_any_valid_rules_passes(self):
        """Minimal valid Rules passes."""
        data = {
            "frame": {"file": "rules", "schema_version": "0.3.0", "role": "project_instruction_blueprint", "status": "active"},
        }
        result = validate_against_schema(data, "rules")
        assert result.is_valid()

    def test_all_file_types_pass_minimally(self):
        """All 5 FRAME file types pass with minimal valid data."""
        tests = [
            ("facts", {"frame": {"file": "facts", "schema_version": "0.3.0", "role": "current_project_truth", "status": "active"}, "profile": {"name": "t", "summary": "t"}, "architecture": {"summary": "t"}}),
            ("rules", {"frame": {"file": "rules", "schema_version": "0.3.0", "role": "project_instruction_blueprint", "status": "active"}}),
            ("map", {"frame": {"file": "map", "schema_version": "0.3.0", "role": "repo_context_map", "status": "active"}}),
            ("expect", {"frame": {"file": "expect", "schema_version": "0.3.0", "role": "project_correctness_contract", "status": "active"}}),
            ("acts", {"frame": {"file": "acts", "schema_version": "0.3.0", "role": "checked_activity_record", "status": "active"}}),
        ]
        for stem, data in tests:
            result = validate_against_schema(data, stem)
            assert result.is_valid(), f"{stem} should pass: {result.errors}"


# ---------------------------------------------------------------------------
# Limits validator tests
# ---------------------------------------------------------------------------


class TestLimitsValidator:
    """validate_limits() — character limit enforcement."""

    def test_value_within_limit_passes(self):
        data = {"frame": {"file": "facts"}}
        result = validate_limits(data, "facts")
        assert result.is_valid()

    def test_id_too_long_enforced(self):
        """Core field (id) exceeding limit should error."""
        data = {"frame": {"file": "facts", "schema_version": "0.3.0",
                          "role": "current_project_truth", "status": "active"},
                "profile": {"name": "x" * 150, "summary": "t"},
                "architecture": {"summary": "t"}}
        result = validate_limits(data, "facts")
        # profile.name maxLength is 100, so 150 chars should error
        assert not result.is_valid()
        assert any(e.code == "limit_exceeded" for e in result.errors)

    def test_summary_within_limit_passes(self):
        """Advisory field within limit should pass clean."""
        data = {"frame": {"file": "facts"},
                "profile": {"name": "test", "summary": "short"},
                "architecture": {"summary": "short"}}
        result = validate_limits(data, "facts")
        assert result.is_valid()

    def test_advisory_limit_warns_not_errors(self):
        """Advisory field exceeding limit warns but doesn't error."""
        data = {
            "frame": {"file": "map", "schema_version": "0.3.0", "role": "repo_context_map", "status": "active"},
            "structure": "x" * 900,  # maxLength is 800 — advisory
        }
        result = validate_limits(data, "map")
        # Should warn but still be valid (only warnings, no errors)
        assert result.is_valid()
        assert any(w.code == "limit_advisory" for w in result.warnings)


# ---------------------------------------------------------------------------
# Cross-file validator tests
# ---------------------------------------------------------------------------


class TestCrossFileValidator:
    """validate_cross_file() — cross-file consistency."""

    def test_all_matching_passes(self):
        parts = {
            "facts": {"frame": {"file": "facts", "schema_version": "0.3.0", "role": "current_project_truth"}},
            "rules": {"frame": {"file": "rules", "schema_version": "0.3.0", "role": "project_instruction_blueprint"}},
        }
        result = validate_cross_file(parts)
        assert result.is_valid()

    def test_version_mismatch_errors(self):
        parts = {
            "facts": {"frame": {"file": "facts", "schema_version": "0.2.0"}},
            "rules": {"frame": {"file": "rules", "schema_version": "0.3.0"}},
        }
        result = validate_cross_file(parts)
        assert not result.is_valid()
        assert any(e.code == "schema_version_mismatch" for e in result.errors)

    def test_file_field_mismatch_errors(self):
        """If facts.yaml has file: rules, it errors."""
        parts = {
            "facts": {"frame": {"file": "rules", "schema_version": "0.3.0"}},
        }
        result = validate_cross_file(parts)
        assert not result.is_valid()
        assert any(e.code == "file_role_mismatch" for e in result.errors)

    def test_role_field_mismatch_errors(self):
        """If facts.yaml has wrong role, it errors."""
        parts = {
            "facts": {"frame": {"file": "facts", "schema_version": "0.3.0", "role": "wrong_role"}},
        }
        result = validate_cross_file(parts)
        assert not result.is_valid()
        assert any(e.code == "file_role_mismatch" for e in result.errors)


# ---------------------------------------------------------------------------
# End-to-end validate_frame tests
# ---------------------------------------------------------------------------


class TestValidateFrame:
    """validate_frame() — complete 5-file validation."""

    def _write_fixture(self, tmpdir: str, files: dict[str, str]):
        """Write FRAME files to a temp directory."""
        for name, content in files.items():
            Path(tmpdir, name).write_text(content)

    def test_valid_full_frame_passes(self):
        """All 5 files with correct headers passes validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_fixture(tmpdir, {
                "facts.yaml": "frame:\n  file: facts\n  schema_version: '0.3.0'\n  role: current_project_truth\n  status: active\nprofile:\n  name: test\n  summary: test\narchitecture:\n  summary: test\n",
                "rules.yaml": "frame:\n  file: rules\n  schema_version: '0.3.0'\n  role: project_instruction_blueprint\n  status: active\n",
                "map.yaml": "frame:\n  file: map\n  schema_version: '0.3.0'\n  role: repo_context_map\n  status: active\n",
                "expect.yaml": "frame:\n  file: expect\n  schema_version: '0.3.0'\n  role: project_correctness_contract\n  status: active\n",
                "acts.yaml": "frame:\n  file: acts\n  schema_version: '0.3.0'\n  role: checked_activity_record\n  status: active\n",
            })
            result = validate_frame(tmpdir)
            assert result.is_valid(), f"Expected valid, got errors: {result.errors}"

    def test_missing_file_raises(self):
        """Missing one of the 5 files raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Only write 4 files
            self._write_fixture(tmpdir, {
                "facts.yaml": "frame:\n  file: facts\n  schema_version: '0.3.0'\n  role: current_project_truth\n  status: active\nprofile:\n  name: test\n  summary: test\narchitecture:\n  summary: test\n",
                "rules.yaml": "frame:\n  file: rules\n  schema_version: '0.3.0'\n  role: project_instruction_blueprint\n  status: active\n",
                "map.yaml": "frame:\n  file: map\n  schema_version: '0.3.0'\n  role: repo_context_map\n  status: active\n",
                "expect.yaml": "frame:\n  file: expect\n  schema_version: '0.3.0'\n  role: project_correctness_contract\n  status: active\n",
                # acts.yaml missing
            })
            with pytest.raises(FileNotFoundError, match="acts.yaml"):
                validate_frame(tmpdir)

    def test_version_mismatch_detected(self):
        """Schema version mismatch across files is caught."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_fixture(tmpdir, {
                "facts.yaml": "frame:\n  file: facts\n  schema_version: '0.2.0'\n  role: current_project_truth\n  status: active\nprofile:\n  name: test\n  summary: test\narchitecture:\n  summary: test\n",
                "rules.yaml": "frame:\n  file: rules\n  schema_version: '0.3.0'\n  role: project_instruction_blueprint\n  status: active\n",
                "map.yaml": "frame:\n  file: map\n  schema_version: '0.3.0'\n  role: repo_context_map\n  status: active\n",
                "expect.yaml": "frame:\n  file: expect\n  schema_version: '0.3.0'\n  role: project_correctness_contract\n  status: active\n",
                "acts.yaml": "frame:\n  file: acts\n  schema_version: '0.3.0'\n  role: checked_activity_record\n  status: active\n",
            })
            result = validate_frame(tmpdir)
            assert not result.is_valid()
            assert any(e.code == "schema_version_mismatch" for e in result.errors)

    def test_file_role_mismatch_detected(self):
        """Wrong file/role field is caught."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_fixture(tmpdir, {
                "facts.yaml": "frame:\n  file: rules\n  schema_version: '0.3.0'\n  role: current_project_truth\n  status: active\nprofile:\n  name: test\n  summary: test\narchitecture:\n  summary: test\n",
                "rules.yaml": "frame:\n  file: rules\n  schema_version: '0.3.0'\n  role: project_instruction_blueprint\n  status: active\n",
                "map.yaml": "frame:\n  file: map\n  schema_version: '0.3.0'\n  role: repo_context_map\n  status: active\n",
                "expect.yaml": "frame:\n  file: expect\n  schema_version: '0.3.0'\n  role: project_correctness_contract\n  status: active\n",
                "acts.yaml": "frame:\n  file: acts\n  schema_version: '0.3.0'\n  role: checked_activity_record\n  status: active\n",
            })
            result = validate_frame(tmpdir)
            assert not result.is_valid()
            assert any(e.code == "file_role_mismatch" for e in result.errors)
