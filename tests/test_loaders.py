"""Tests for FRAME loader -- end-to-end pipeline from directory to FRAME object."""

import tempfile
from pathlib import Path

import pytest

from framesdkpy.loaders import load_frame, FrameLoadError
from framesdkpy.models import FRAME, FrameFacts


def _write_minimal_frame(tmpdir: str) -> None:
    """Write all 5 minimal valid FRAME YAML files to a directory."""
    files = {
        "facts.yaml": (
            "frame:\n  file: facts\n  schema_version: '0.3.0'\n"
            "  role: current_project_truth\n  status: active\n"
            "profile:\n  name: test\n  summary: a test project\n"
            "architecture:\n  summary: single process\n"
        ),
        "rules.yaml": (
            "frame:\n  file: rules\n  schema_version: '0.3.0'\n"
            "  role: project_instruction_blueprint\n  status: active\n"
            "governance_level: normal\n"
        ),
        "map.yaml": (
            "frame:\n  file: map\n  schema_version: '0.3.0'\n"
            "  role: repo_context_map\n  status: active\n"
        ),
        "expect.yaml": (
            "frame:\n  file: expect\n  schema_version: '0.3.0'\n"
            "  role: project_correctness_contract\n  status: active\n"
        ),
        "acts.yaml": (
            "frame:\n  file: acts\n  schema_version: '0.3.0'\n"
            "  role: checked_activity_record\n  status: active\n"
        ),
    }
    for name, content in files.items():
        Path(tmpdir, name).write_text(content)


class TestLoadFrame:
    """End-to-end loader tests."""

    def test_load_minimal_frame(self):
        """Load all 5 files from a directory and get a typed FRAME object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_minimal_frame(tmpdir)
            frame = load_frame(tmpdir)

            assert isinstance(frame, FRAME)
            assert isinstance(frame.facts, FrameFacts)
            assert frame.facts is not None
            assert frame.facts.profile.name == "test"
            assert frame.facts.architecture.summary == "single process"
            assert frame.rules is not None
            assert frame.rules.governance_level == "normal"
            assert frame.map is not None
            assert frame.expect is not None
            assert frame.acts is not None

    def test_load_frame_serializes(self):
        """Loaded FRAME object serializes to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_minimal_frame(tmpdir)
            frame = load_frame(tmpdir)
            d = frame.to_dict()
            assert d["facts"]["profile"]["name"] == "test"
            j = frame.to_json()
            assert "test" in j

    def test_missing_file_raises(self):
        """Missing one of the 5 files raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Only write 4 files
            Path(tmpdir, "facts.yaml").write_text(
                "frame:\n  file: facts\n  schema_version: '0.3.0'\n"
                "  role: current_project_truth\n  status: active\n"
                "profile:\n  name: test\n  summary: test\n"
                "architecture:\n  summary: test\n"
            )
            Path(tmpdir, "rules.yaml").write_text(
                "frame:\n  file: rules\n  schema_version: '0.3.0'\n"
                "  role: project_instruction_blueprint\n  status: active\n"
            )
            # map, expect, acts missing
            with pytest.raises(FileNotFoundError, match="map.yaml"):
                load_frame(tmpdir)

    def test_schema_version_mismatch_raises(self):
        """Mismatched schema_versions raise FrameLoadError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_minimal_frame(tmpdir)
            # Override facts.yaml with wrong schema_version
            Path(tmpdir, "facts.yaml").write_text(
                "frame:\n  file: facts\n  schema_version: '0.1.0'\n"
                "  role: current_project_truth\n  status: active\n"
                "profile:\n  name: test\n  summary: test\n"
                "architecture:\n  summary: test\n"
            )
            with pytest.raises(FrameLoadError):
                load_frame(tmpdir)

    def test_missing_profile_raises(self):
        """Missing required Facts fields raises FrameLoadError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _write_minimal_frame(tmpdir)
            # Override facts.yaml -- no profile
            Path(tmpdir, "facts.yaml").write_text(
                "frame:\n  file: facts\n  schema_version: '0.3.0'\n"
                "  role: current_project_truth\n  status: active\n"
            )
            with pytest.raises(FrameLoadError):
                load_frame(tmpdir)

    def test_nonexistent_directory_raises(self):
        """Nonexistent directory raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_frame("/nonexistent/dir")
