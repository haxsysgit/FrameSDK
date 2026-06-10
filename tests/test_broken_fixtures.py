"""Broken fixture tests — simulate real agent mistakes and verify the validator catches them.

These tests intentionally corrupt FRAME files the way a real agent might:
- Wrong types (string where int expected)
- Missing required fields
- Extra unknown properties (agent invents a field)
- Wrong enum values
- Character limit violations
- Cross-file inconsistencies
"""

import tempfile
import shutil
from pathlib import Path

import pytest

from frame.loaders import load_frame, FrameLoadError
from frame.validators import validate_frame, validate_file
from frame.translators import translate_directory

# Path to the valid fixture
FIXTURE_DIR = Path(__file__).parent / "fixtures"


class TestAgentTypos:
    """Agent introduces simple type errors."""

    def test_string_in_int_field(self):
        """Agent puts a string where an integer belongs."""
        with tempfile.TemporaryDirectory() as tmp:
            for name in ["facts", "rules", "map", "expect", "acts"]:
                shutil.copy(FIXTURE_DIR / f"{name}.yaml", Path(tmp) / f"{name}.yaml")
            facts = Path(tmp) / "facts.yaml"
            content = facts.read_text()
            # classification.surface_count should be int, agent puts string
            content = content.replace("surface_count: 2", "surface_count: two")
            facts.write_text(content)
            result = validate_file(str(facts))
            assert not result.is_valid()
            assert any(e.code == "type_error" for e in result.errors)

    def test_bool_in_string_field(self):
        """Agent puts a boolean where a string belongs."""
        with tempfile.TemporaryDirectory() as tmp:
            for name in ["facts", "rules", "map", "expect", "acts"]:
                shutil.copy(FIXTURE_DIR / f"{name}.yaml", Path(tmp) / f"{name}.yaml")
            facts = Path(tmp) / "facts.yaml"
            content = facts.read_text()
            content = content.replace("name: Pharmax", "name: true")
            facts.write_text(content)
            result = validate_file(str(facts))
            assert not result.is_valid()
            assert any(e.code == "type_error" for e in result.errors)


class TestAgentInventions:
    """Agent invents fields that don't exist in the schema."""

    def test_invented_field(self):
        """Agent adds a field that isn't in the schema."""
        with tempfile.TemporaryDirectory() as tmp:
            for name in ["facts", "rules", "map", "expect", "acts"]:
                shutil.copy(FIXTURE_DIR / f"{name}.yaml", Path(tmp) / f"{name}.yaml")
            facts = Path(tmp) / "facts.yaml"
            content = facts.read_text()
            # Agent invents a "coverage_score" field
            content += "\ncoverage_score: 95\n"
            facts.write_text(content)
            result = validate_file(str(facts))
            # Should flag as unknown property (warning, not error — we allow forward compat)
            assert any(w.code == "schema_error" for w in result.warnings)

    def test_invented_section(self):
        """Agent creates an entirely new section outside FRAME."""
        with tempfile.TemporaryDirectory() as tmp:
            for name in ["facts", "rules", "map", "expect", "acts"]:
                shutil.copy(FIXTURE_DIR / f"{name}.yaml", Path(tmp) / f"{name}.yaml")
            facts = Path(tmp) / "facts.yaml"
            content = facts.read_text()
            content += "\nagent_notes:\n  mood: confident\n  model: claude-4\n"
            facts.write_text(content)
            result = validate_file(str(facts))
            assert any(w.code == "schema_error" for w in result.warnings)


class TestAgentForgetting:
    """Agent removes required fields."""

    def test_removes_required_field(self):
        """Agent removes profile.name."""
        with tempfile.TemporaryDirectory() as tmp:
            for name in ["facts", "rules", "map", "expect", "acts"]:
                shutil.copy(FIXTURE_DIR / f"{name}.yaml", Path(tmp) / f"{name}.yaml")
            facts = Path(tmp) / "facts.yaml"
            content = facts.read_text()
            # Replace name with nothing
            import re
            content = re.sub(r'\n  name: "Pharmax"\n', '\n', content)
            facts.write_text(content)
            result = validate_file(str(facts))
            assert not result.is_valid()
            assert any(e.code == "missing_required" for e in result.errors)

    def test_removes_frame_header(self):
        """Agent removes the entire frame header."""
        with tempfile.TemporaryDirectory() as tmp:
            for name in ["facts", "rules", "map", "expect", "acts"]:
                shutil.copy(FIXTURE_DIR / f"{name}.yaml", Path(tmp) / f"{name}.yaml")
            facts = Path(tmp) / "facts.yaml"
            content = facts.read_text()
            content = content.replace(
                "frame:\n  file: facts\n  schema_version: \"0.3.0\"\n  role: current_project_truth\n  scope: baseline_project\n  status: active\n  last_reviewed: \"2026-06-08\"\n  updated_by: ground-truth-audit\n",
                ""
            )
            facts.write_text(content)
            result = validate_file(str(facts))
            assert not result.is_valid()
            assert any(e.code == "missing_required" for e in result.errors)


class TestAgentConfusion:
    """Agent mixes up files or values across files."""

    def test_wrong_file_field_in_rules(self):
        """Agent writes file: facts in rules.yaml."""
        with tempfile.TemporaryDirectory() as tmp:
            for name in ["facts", "rules", "map", "expect", "acts"]:
                shutil.copy(FIXTURE_DIR / f"{name}.yaml", Path(tmp) / f"{name}.yaml")
            rules = Path(tmp) / "rules.yaml"
            content = rules.read_text()
            content = content.replace("file: rules", "file: facts")
            rules.write_text(content)
            result = validate_frame(tmp)
            assert not result.is_valid()
            assert any(e.code == "file_role_mismatch" for e in result.errors)

    def test_wrong_enum_value(self):
        """Agent uses a value not in the enum."""
        with tempfile.TemporaryDirectory() as tmp:
            for name in ["facts", "rules", "map", "expect", "acts"]:
                shutil.copy(FIXTURE_DIR / f"{name}.yaml", Path(tmp) / f"{name}.yaml")
            rules = Path(tmp) / "rules.yaml"
            content = rules.read_text()
            content = content.replace(
                "governance_level: normal",
                "governance_level: maximum"
            )
            rules.write_text(content)
            result = validate_file(str(rules))
            assert not result.is_valid()

    def test_copies_facts_content_into_rules(self):
        """Agent copies Facts fields into rules.yaml by mistake."""
        with tempfile.TemporaryDirectory() as tmp:
            for name in ["facts", "rules", "map", "expect", "acts"]:
                shutil.copy(FIXTURE_DIR / f"{name}.yaml", Path(tmp) / f"{name}.yaml")
            rules = Path(tmp) / "rules.yaml"
            content = rules.read_text()
            # Add a profile block that belongs in facts
            content += "\nprofile:\n  name: accidentally_copied\n  summary: wrong file\n"
            rules.write_text(content)
            result = validate_file(str(rules))
            # profile is not in rules schema — should warn about unknown properties
            assert any(w.code == "schema_error" for w in result.warnings)


class TestAgentVerbosity:
    """Agent writes overly long fields."""

    def test_name_exceeds_max_length(self):
        """Agent writes a very long project name."""
        with tempfile.TemporaryDirectory() as tmp:
            for name in ["facts", "rules", "map", "expect", "acts"]:
                shutil.copy(FIXTURE_DIR / f"{name}.yaml", Path(tmp) / f"{name}.yaml")
            facts = Path(tmp) / "facts.yaml"
            content = facts.read_text()
            content = content.replace(
                'name: "Pharmax"',
                'name: "' + "x" * 150 + '"'
            )
            facts.write_text(content)
            result = validate_file(str(facts))
            assert not result.is_valid()
            assert any(e.code == "limit_exceeded" for e in result.errors)

    def test_giant_architecture_summary(self):
        """Agent writes a book in architecture.summary."""
        with tempfile.TemporaryDirectory() as tmp:
            for name in ["facts", "rules", "map", "expect", "acts"]:
                shutil.copy(FIXTURE_DIR / f"{name}.yaml", Path(tmp) / f"{name}.yaml")
            facts = Path(tmp) / "facts.yaml"
            content = facts.read_text()
            content = content.replace(
                'summary: "Backend API (FastAPI) + Frontend SPA (Vue 3) with role-based access"',
                'summary: "' + "A" * 600 + '"'
            )
            facts.write_text(content)
            result = validate_file(str(facts))
            # Advisory limit — should warn, not error
            assert any(w.code == "limit_advisory" for w in result.warnings)


class TestAgentRushes:
    """Agent skips schema_version consistency."""

    def test_missing_schema_version_entirely(self):
        """Agent creates rules.yaml without schema_version."""
        with tempfile.TemporaryDirectory() as tmp:
            for name in ["facts", "rules", "map", "expect", "acts"]:
                shutil.copy(FIXTURE_DIR / f"{name}.yaml", Path(tmp) / f"{name}.yaml")
            rules = Path(tmp) / "rules.yaml"
            content = rules.read_text()
            content = content.replace('schema_version: "0.3.0"\n', '')
            rules.write_text(content)
            result = validate_file(str(rules))
            assert not result.is_valid()

    def test_all_files_mismatched_versions(self):
        """Agent updates one file's schema_version but forgets the others."""
        with tempfile.TemporaryDirectory() as tmp:
            for name in ["facts", "rules", "map", "expect", "acts"]:
                shutil.copy(FIXTURE_DIR / f"{name}.yaml", Path(tmp) / f"{name}.yaml")
            # Bump all but one
            for name in ["facts", "map", "expect", "acts"]:
                p = Path(tmp) / f"{name}.yaml"
                content = p.read_text()
                content = content.replace('schema_version: "0.3.0"', 'schema_version: "0.4.0"')
                p.write_text(content)
            # rules stays at 0.3.0
            result = validate_frame(tmp)
            assert not result.is_valid()
            assert any(e.code == "schema_version_mismatch" for e in result.errors)
