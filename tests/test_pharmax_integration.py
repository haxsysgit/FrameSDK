"""Integration tests against the real Pharmax FRAME fixture.

Tests the full pipeline: discover → parse → normalize → validate → assemble.
These are the ground-truth files from the red room test.
"""

from pathlib import Path

import pytest

from framesdkpy.loaders import load_frame, FrameLoadError
from framesdkpy.translators import translate_directory, translate_file
from framesdkpy.validators import validate_frame, validate_file
from framesdkpy.models import FRAME, FrameFacts, FrameRules, FrameMap, FrameExpect, FrameActs

# Path to the real pharmax FRAME fixture
FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_fixture_dir_exists():
    """The fixture directory exists with all 5 files."""
    assert FIXTURE_DIR.is_dir()
    for name in ["facts", "rules", "map", "expect", "acts"]:
        assert (FIXTURE_DIR / f"{name}.yaml").is_file(), f"Missing {name}.yaml"


class TestPharmaxLoad:
    """Full load_frame pipeline against real Pharmax fixture."""

    def test_load_frame_returns_typed_frAME(self):
        """load_frame returns a FRAME object with all 5 parts populated."""
        frame = load_frame(str(FIXTURE_DIR))
        assert isinstance(frame, FRAME)
        assert isinstance(frame.facts, FrameFacts)
        assert isinstance(frame.rules, FrameRules)
        assert isinstance(frame.map, FrameMap)
        assert isinstance(frame.expect, FrameExpect)
        assert isinstance(frame.acts, FrameActs)

    def test_facts_contains_pharmax_profile(self):
        """Facts has the actual Pharmax project identity."""
        frame = load_frame(str(FIXTURE_DIR))
        assert "pharmax" in frame.facts.profile.name.lower()
        assert len(frame.facts.profile.summary) > 0
        assert frame.facts.profile.repo_shape == "split-backend-frontend"

    def test_facts_has_architecture(self):
        """Architecture block is populated with backend/frontend layers."""
        frame = load_frame(str(FIXTURE_DIR))
        assert len(frame.facts.architecture.summary) > 0
        assert frame.facts.architecture.backend_layers is not None
        assert frame.facts.architecture.frontend_layers is not None

    def test_facts_has_technology(self):
        """Technology block has language, framework, database."""
        frame = load_frame(str(FIXTURE_DIR))
        assert frame.facts.technology is not None
        assert frame.facts.technology.language is not None
        assert frame.facts.technology.database is not None

    def test_facts_has_quirks(self):
        """Quirks are populated."""
        frame = load_frame(str(FIXTURE_DIR))
        assert len(frame.facts.quirks) > 0
        assert frame.facts.quirks[0].id is not None

    def test_facts_has_sources(self):
        """Sources are populated."""
        frame = load_frame(str(FIXTURE_DIR))
        assert len(frame.facts.sources) > 0
        assert frame.facts.sources[0].id is not None

    def test_rules_has_governance_level(self):
        """Rules has governance_level set."""
        frame = load_frame(str(FIXTURE_DIR))
        assert frame.rules.governance_level in ("relaxed", "normal", "strict")

    def test_rules_has_commands(self):
        """Rules has executable commands."""
        frame = load_frame(str(FIXTURE_DIR))
        assert len(frame.rules.commands) > 0
        first_cmd = list(frame.rules.commands.values())[0]
        assert first_cmd.run is not None
        assert first_cmd.kind in ("setup", "verify", "run")

    def test_rules_has_donts(self):
        """Rules has donts."""
        frame = load_frame(str(FIXTURE_DIR))
        assert len(frame.rules.donts) > 0
        assert frame.rules.donts[0].severity in ("critical", "warning")

    def test_map_has_structure(self):
        """Map has a structure overview."""
        frame = load_frame(str(FIXTURE_DIR))
        assert frame.map.structure is not None
        assert len(frame.map.structure) > 0

    def test_map_has_entrypoints(self):
        """Map has entrypoints defined."""
        frame = load_frame(str(FIXTURE_DIR))
        assert len(frame.map.entrypoints) > 0
        assert frame.map.entrypoints[0].kind in ("cli", "api", "web", "script")

    def test_map_has_groups(self):
        """Map has path groups."""
        frame = load_frame(str(FIXTURE_DIR))
        assert len(frame.map.groups) > 0

    def test_map_has_managed_paths(self):
        """Map declares managed paths."""
        frame = load_frame(str(FIXTURE_DIR))
        assert len(frame.map.managed_paths) > 0
        assert frame.map.managed_paths[0].rule in ("generated", "config", "immutable")

    def test_expect_has_checks(self):
        """Expect has verification checks."""
        frame = load_frame(str(FIXTURE_DIR))
        assert len(frame.expect.checks) > 0
        first_check = list(frame.expect.checks.values())[0]
        assert first_check.name is not None

    def test_expect_has_must_hold(self):
        """Expect has invariants."""
        frame = load_frame(str(FIXTURE_DIR))
        assert len(frame.expect.must_hold) > 0

    def test_frame_serializes_to_json(self):
        """Full FRAME serializes to valid JSON."""
        frame = load_frame(str(FIXTURE_DIR))
        json_str = frame.to_json()
        import json
        data = json.loads(json_str)
        assert data["facts"]["profile"]["name"] is not None
        assert data["rules"]["governance_level"] is not None
        assert data["map"]["structure"] is not None

    def test_frame_roundtrips(self):
        """Dict → JSON → re-parse preserves data."""
        frame = load_frame(str(FIXTURE_DIR))
        d = frame.to_dict()
        import json
        j = json.dumps(d)
        d2 = json.loads(j)
        assert d2["facts"]["profile"]["name"] == d["facts"]["profile"]["name"]


class TestPharmaxValidate:
    """Validation against real Pharmax fixture."""

    def test_validate_frame_passes(self):
        """Full validate_frame passes on real fixture."""
        result = validate_frame(str(FIXTURE_DIR))
        assert result.is_valid(), f"Validation failed: {result.errors}"

    def test_validate_individual_files(self):
        """Each individual file passes validation."""
        for name in ["facts", "rules", "map", "expect", "acts"]:
            filepath = FIXTURE_DIR / f"{name}.yaml"
            result = validate_file(str(filepath))
            assert result.is_valid(), f"{name}.yaml failed: {result.errors}"


class TestPharmaxTranslate:
    """Translation against real Pharmax fixture."""

    def test_translate_directory(self):
        """Full directory translates to dict."""
        parts = translate_directory(str(FIXTURE_DIR))
        assert set(parts.keys()) == {"facts", "rules", "map", "expect", "acts"}
        assert parts["facts"]["profile"]["name"] is not None


class TestPharmaxBreaking:
    """Intentionally break the fixture and verify errors are caught."""

    def test_missing_file_fails(self):
        """Missing a file fails discovery."""
        import tempfile, shutil
        with tempfile.TemporaryDirectory() as tmp:
            # Copy 4 of 5 files
            for name in ["facts", "rules", "map", "expect"]:
                shutil.copy(FIXTURE_DIR / f"{name}.yaml", Path(tmp) / f"{name}.yaml")
            with pytest.raises(FileNotFoundError, match="acts"):
                load_frame(tmp)

    def test_wrong_file_field_fails(self):
        """facts.yaml with file: rules fails cross-file check."""
        import tempfile, shutil
        with tempfile.TemporaryDirectory() as tmp:
            for name in ["facts", "rules", "map", "expect", "acts"]:
                shutil.copy(FIXTURE_DIR / f"{name}.yaml", Path(tmp) / f"{name}.yaml")
            # Corrupt facts.yaml
            facts = Path(tmp) / "facts.yaml"
            content = facts.read_text()
            content = content.replace("file: facts", "file: rules")
            facts.write_text(content)
            with pytest.raises(FrameLoadError):
                load_frame(tmp)

    def test_version_mismatch_fails(self):
        """Mismatched schema_version fails cross-file check."""
        import tempfile, shutil
        with tempfile.TemporaryDirectory() as tmp:
            for name in ["facts", "rules", "map", "expect", "acts"]:
                shutil.copy(FIXTURE_DIR / f"{name}.yaml", Path(tmp) / f"{name}.yaml")
            facts = Path(tmp) / "facts.yaml"
            content = facts.read_text()
            content = content.replace('schema_version: "0.3.0"', 'schema_version: "0.1.0"')
            facts.write_text(content)
            with pytest.raises(FrameLoadError):
                load_frame(tmp)
