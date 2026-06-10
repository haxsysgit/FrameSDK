"""Schema-shape preservation tests.

The SDK exists to give every tool the same output shape. If the schema accepts
frame/evidence/links, the model layer must preserve them during assembly and
serialization.
"""

from framesdkpy.loaders.assembler import assemble_frame


def _header(file_name: str, role: str) -> dict:
    return {
        "file": file_name,
        "schema_version": "0.3.0",
        "role": role,
        "scope": "baseline_project",
        "status": "active",
        "last_reviewed": "2026-06-10",
        "updated_by": "test",
        "update_reason": "contract test",
    }


def _parts_with_schema_metadata() -> dict[str, dict]:
    link = {"rel": "explains", "ref": "facts.quirks.runtime_env"}
    evidence = {
        "id": "evidence.runtime",
        "source": "README.md",
        "confidence": "high",
        "refs": ["facts.profile.name"],
    }

    return {
        "facts": {
            "frame": _header("facts", "current_project_truth"),
            "profile": {"name": "Demo", "summary": "Demo project"},
            "architecture": {"summary": "Small demo app"},
            "sources": [
                {
                    "id": "readme",
                    "path": "README.md",
                    "purpose": "Project overview",
                }
            ],
            "evidence": [evidence],
            "links": [link],
        },
        "rules": {
            "frame": _header("rules", "project_instruction_blueprint"),
            "governance_level": "normal",
            "rules": [
                {
                    "id": "keep_tests_green",
                    "rule": "Run tests before release",
                    "links": [link],
                }
            ],
            "evidence": [evidence],
            "links": [link],
        },
        "map": {
            "frame": _header("map", "repo_context_map"),
            "groups": [
                {
                    "id": "src",
                    "label": "source",
                    "paths": ["framesdkpy/**/*.py"],
                    "links": [link],
                }
            ],
            "evidence": [evidence],
            "links": [link],
        },
        "expect": {
            "frame": _header("expect", "project_correctness_contract"),
            "must_hold": [
                {
                    "id": "all_parts",
                    "statement": "All five FRAME parts load",
                    "links": [link],
                }
            ],
            "evidence": [evidence],
            "links": [link],
        },
        "acts": {
            "frame": _header("acts", "checked_activity_record"),
            "runs": [
                {
                    "id": "run.audit",
                    "actor": "test",
                    "goal": "verify preservation",
                    "status": "pass",
                    "links": [link],
                }
            ],
            "evidence": [evidence],
            "links": [link],
        },
    }


def test_assembly_preserves_frame_evidence_and_links():
    """Top-level schema metadata survives typed assembly and JSON serialization."""
    frame = assemble_frame(_parts_with_schema_metadata())
    data = frame.to_dict()

    for part in ["facts", "rules", "map", "expect", "acts"]:
        assert data[part]["frame"]["schema_version"] == "0.3.0"
        assert data[part]["evidence"][0]["id"] == "evidence.runtime"
        assert data[part]["links"][0]["rel"] == "explains"


def test_assembly_preserves_item_level_links():
    """Schema-supported item links are not stripped by dataclass assembly."""
    frame = assemble_frame(_parts_with_schema_metadata())
    data = frame.to_dict()

    assert data["rules"]["rules"][0]["links"][0]["ref"] == "facts.quirks.runtime_env"
    assert data["map"]["groups"][0]["links"][0]["rel"] == "explains"
    assert data["expect"]["must_hold"][0]["links"][0]["rel"] == "explains"
    assert data["acts"]["runs"][0]["links"][0]["rel"] == "explains"
