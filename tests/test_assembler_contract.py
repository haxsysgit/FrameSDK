"""Assembler invariant tests.

The assembler is reachable from framesdkpy.loaders, so it must protect the
same all-five-parts contract as load_frame().
"""

import pytest

from framesdkpy.loaders.assembler import FrameLoadError, assemble_frame


def _header(file_name: str, role: str) -> dict:
    return {
        "file": file_name,
        "schema_version": "0.3.0",
        "role": role,
        "status": "active",
    }


def _minimal_parts() -> dict[str, dict]:
    return {
        "facts": {
            "frame": _header("facts", "current_project_truth"),
            "profile": {"name": "Demo", "summary": "Demo project"},
            "architecture": {"summary": "Small demo app"},
        },
        "rules": {
            "frame": _header("rules", "project_instruction_blueprint"),
            "governance_level": "normal",
        },
        "map": {
            "frame": _header("map", "repo_context_map"),
        },
        "expect": {
            "frame": _header("expect", "project_correctness_contract"),
        },
        "acts": {
            "frame": _header("acts", "checked_activity_record"),
        },
    }


def test_assemble_frame_requires_all_five_parts():
    """Direct assembly cannot create FRAME objects with missing parts."""
    parts = _minimal_parts()
    del parts["acts"]

    with pytest.raises(FrameLoadError) as raised:
        assemble_frame(parts)

    assert "Missing FRAME part(s): acts" in str(raised.value)


def test_assemble_frame_returns_all_five_parts_when_complete():
    """Complete input assembles a FRAME object with no None parts."""
    frame = assemble_frame(_minimal_parts())

    assert frame.facts is not None
    assert frame.rules is not None
    assert frame.map is not None
    assert frame.expect is not None
    assert frame.acts is not None
