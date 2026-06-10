"""Tests for FRAME models — construction, serialization, null preservation.

Covers all five FRAME parts and their sub-models.
"""

import json
import pytest
from frame.models import (
    FRAME, FrameFacts, FrameRules, FrameMap, FrameExpect, FrameActs,
    Profile, Architecture, Technology, Source, Quirk, OpenQuestion,
    Policy, CoreRule, Command, Dont, AskFirst, Hint,
    Group, PathEntry, Entrypoint, ManagedPath, UnmappedPath,
    MustHold, Check, Proof,
    Run, RunCheck, Blocker,
    FrameBaseModel,
)


# ---------------------------------------------------------------------------
# Facts tests
# ---------------------------------------------------------------------------


class TestFacts:
    """FrameFacts and sub-models."""

    def test_minimal_facts_construction(self):
        """Facts can be built with only required fields."""
        facts = FrameFacts(
            profile=Profile(name="test", summary="A test project"),
            architecture=Architecture(summary="single process, in-memory"),
        )
        assert facts.profile.name == "test"
        assert facts.architecture.summary == "single process, in-memory"
        assert facts.sources == []
        assert facts.quirks == []
        assert facts.technology is None

    def test_full_facts_construction(self):
        """All optional Facts fields populate correctly."""
        tech = Technology(language="Python", framework="FastAPI", database="PostgreSQL")
        arch = Architecture(
            summary="Backend API + Vue frontend",
            backend_layers=["routes", "services", "models"],
            data_flow="client → API → service → DB",
        )
        facts = FrameFacts(
            profile=Profile(
                name="pharmax",
                summary="Pharmacy management platform",
                repo_shape="split-backend-frontend",
                delivery_family="web-app",
            ),
            architecture=arch,
            technology=tech,
            sources=[Source(id="backend_main", path="Backend/main.py", purpose="Entrypoint")],
            quirks=[Quirk(id="legacy_auth", description="old auth middleware", why="migration in progress")],
            open_questions=[OpenQuestion(id="payment", question="Which payment provider?", context="comparing Paystack vs Flutterwave")],
            environments={"production": {"db_url": "prod-db-url"}},
        )
        assert facts.technology.language == "Python"
        assert len(facts.sources) == 1
        assert facts.sources[0].id == "backend_main"
        assert len(facts.quirks) == 1
        assert facts.open_questions[0].context == "comparing Paystack vs Flutterwave"

    def test_profile_required_fields_non_nullable(self):
        """Profile.name and Profile.summary are str, not str | None."""
        p = Profile(name="test", summary="summary")
        assert isinstance(p.name, str)
        assert p.name is not None
        assert isinstance(p.summary, str)

    def test_architecture_required_fields(self):
        """Architecture.summary is required."""
        a = Architecture(summary="test")
        assert a.summary == "test"
        assert a.backend_layers is None  # optional

    def test_to_dict_preserves_null(self):
        """Null values appear in serialized output as JSON null."""
        facts = FrameFacts(
            profile=Profile(name="test", summary="summary"),
            architecture=Architecture(summary="test"),
        )
        d = facts.to_dict()
        assert d["technology"] is None
        assert d["classification"] is None
        # Verify JSON output has null, not missing key
        j = facts.to_json()
        parsed = json.loads(j)
        assert parsed["technology"] is None
        assert "technology" in parsed

    def test_facts_to_json_is_valid(self):
        """to_json produces parseable JSON."""
        facts = FrameFacts(
            profile=Profile(name="test", summary="summary"),
            architecture=Architecture(summary="test"),
        )
        j = facts.to_json()
        parsed = json.loads(j)
        assert parsed["profile"]["name"] == "test"


# ---------------------------------------------------------------------------
# Rules tests
# ---------------------------------------------------------------------------


class TestRules:
    """FrameRules and sub-models."""

    def test_minimal_rules_construction(self):
        """Rules can be built with only defaults."""
        rules = FrameRules()
        assert rules.governance_level == "normal"
        assert rules.rules == []
        assert rules.commands == {}

    def test_full_rules_construction(self):
        """All Rules fields populate correctly."""
        rules = FrameRules(
            governance_level="strict",
            rules=[CoreRule(id="use_services", rule="thin routes, logic in services")],
            policies=[Policy(id="role_access", name="Role-based access", rule="Admin, Cashier, Staff")],
            commands={
                "backend_tests": Command(
                    run="cd Backend && pytest -q",
                    kind="verify",
                    purpose="run backend test suite",
                )
            },
            donts=[Dont(id="no_manual_migrations", rule="never edit migration files", severity="critical")],
            ask_first=[AskFirst(
                id="invoice_changes",
                trigger_type="file_pattern",
                trigger="invoice_workflow_service.py",
                reason="invoice lifecycle is core business logic",
            )],
            hints=[Hint(id="use_pytest", hint="all tests use pytest fixtures, not unittest")],
            code_style={"python": "black --line-length 120"},
        )
        assert rules.governance_level == "strict"
        assert len(rules.commands) == 1
        assert rules.commands["backend_tests"].kind == "verify"
        assert rules.donts[0].severity == "critical"
        assert rules.ask_first[0].trigger_type == "file_pattern"

    def test_dont_default_severity(self):
        """Dont defaults to critical severity when not specified."""
        d = Dont(id="test", rule="don't do that")
        assert d.severity == "critical"

    def test_command_fixed_schema(self):
        """Command has exactly three required fields: run, kind, purpose."""
        c = Command(run="echo hi", kind="verify", purpose="test")
        assert c.run == "echo hi"
        assert c.kind == "verify"

    def test_rules_to_dict_with_commands(self):
        """Commands dict serializes correctly."""
        rules = FrameRules(
            commands={"test": Command(run="echo hello", kind="verify", purpose="test command")}
        )
        d = rules.to_dict()
        assert d["commands"]["test"]["run"] == "echo hello"
        assert d["commands"]["test"]["kind"] == "verify"


# ---------------------------------------------------------------------------
# Map tests
# ---------------------------------------------------------------------------


class TestMap:
    """FrameMap and sub-models."""

    def test_minimal_map_construction(self):
        """Map can be built with only defaults."""
        m = FrameMap()
        assert m.groups == []
        assert m.paths == []
        assert m.structure is None

    def test_full_map_construction(self):
        """All Map fields populate correctly."""
        m = FrameMap(
            structure="Backend/ (FastAPI) + Frontend/ (Vue 3)",
            roots={"Backend": "FastAPI application", "Frontend": "Vue 3 SPA"},
            groups=[Group(id="backend_app", label="Backend app code", paths=["Backend/app/**/*.py"])],
            paths=[PathEntry(path="Backend/main.py", purpose="API entry point")],
            entrypoints=[Entrypoint(id="api", path="Backend/main.py", kind="api", description="FastAPI server")],
            managed_paths=[ManagedPath(path="node_modules/**", rule="generated")],
            unmapped_paths=[UnmappedPath(path="Backend/legacy/", reason="not yet audited")],
        )
        assert len(m.groups) == 1
        assert m.groups[0].label == "Backend app code"
        assert m.entrypoints[0].kind == "api"
        assert m.managed_paths[0].rule == "generated"

    def test_path_entry_optional_id(self):
        """PathEntry.id is optional — only needed for cross-referencing."""
        p = PathEntry(path="file.py", purpose="test")
        assert p.id is None

    def test_managed_path_optional_id(self):
        """ManagedPath.id is optional — only needed for cross-referencing."""
        mp = ManagedPath(path="*.pyc", rule="generated")
        assert mp.id is None


# ---------------------------------------------------------------------------
# Expect tests
# ---------------------------------------------------------------------------


class TestExpect:
    """FrameExpect and sub-models."""

    def test_minimal_expect_construction(self):
        """Expect can be built with only defaults."""
        e = FrameExpect()
        assert e.must_hold == []
        assert e.checks == {}
        assert e.proof == []

    def test_full_expect_construction(self):
        """All Expect fields populate correctly."""
        e = FrameExpect(
            outcomes={"invoice_finalize": {"summary": "Invoice finalizes with stock deduction"}},
            must_hold=[MustHold(id="stock_deduction", statement="stock deduction always happens on invoice finalize")],
            checks={
                "workflow_smoke": Check(
                    name="Invoice Workflow Smoke",
                    what="invoice workflow functions correctly",
                    how="test",
                    command_ref="rules.commands.invoice_workflow_smoke",
                    pass_condition="exit_code == 0",
                )
            },
            proof=[Proof(id="review", type="review", description="human review of invoice logic changes")],
            done_when={"all_tests_pass": True},
        )
        assert len(e.checks) == 1
        assert e.checks["workflow_smoke"].pass_condition == "exit_code == 0"
        assert e.checks["workflow_smoke"].command_ref == "rules.commands.invoice_workflow_smoke"
        assert e.must_hold[0].statement == "stock deduction always happens on invoice finalize"

    def test_check_pass_condition_formats(self):
        """Various pass_condition formats work."""
        exit_check = Check(
            name="test",
            what="test check",
            how="test",
            pass_condition="exit_code == 0",
        )
        assert exit_check.pass_condition == "exit_code == 0"

        stdout_check = Check(
            name="build",
            what="frontend builds",
            pass_condition='stdout contains BUILD SUCCESS',
        )
        assert stdout_check.pass_condition is not None
        assert "stdout contains" in stdout_check.pass_condition


# ---------------------------------------------------------------------------
# Acts tests
# ---------------------------------------------------------------------------


class TestActs:
    """FrameActs and sub-models."""

    def test_minimal_acts_construction(self):
        """Acts can be built with only defaults."""
        a = FrameActs()
        assert a.runs == []
        assert a.blockers == []

    def test_full_acts_construction(self):
        """All Acts fields populate correctly."""
        run = Run(
            id="discount_feature",
            actor="claude-code",
            goal="add discount field to product model",
            status="pass",
            work_kind=["code", "test"],
            touched=["Backend/app/services/product_service.py"],
            checks=[
                RunCheck(
                    id="expect.checks.backend_tests",
                    status="ran",
                    result="pass",
                ),
                RunCheck(
                    id="expect.checks.role_policy_review",
                    status="skipped",
                    reason="no auth changes in this task",
                ),
            ],
        )
        acts = FrameActs(
            summary="Recent activity: discount feature added",
            runs=[run],
            blockers=[Blocker(id="missing_env", description="production env not configured yet")],
        )
        assert len(acts.runs) == 1
        run = acts.runs[0]
        assert run.status == "pass"
        assert run.checks is not None
        assert len(run.checks) == 2
        assert run.checks[0].status == "ran"
        assert run.checks[0].result == "pass"
        assert run.checks[1].status == "skipped"
        assert run.checks[1].reason == "no auth changes in this task"
        assert acts.blockers[0].description == "production env not configured yet"

    def test_runcheck_ran_without_result(self):
        """RunCheck with status=ran should have result."""
        rc = RunCheck(id="check.1", status="ran")
        assert rc.result is None  # valid but the loader should populate this

    def test_runcheck_skipped_without_reason(self):
        """RunCheck with status=skipped should have reason."""
        rc = RunCheck(id="check.1", status="skipped")
        assert rc.reason is None  # valid but the loader should populate this


# ---------------------------------------------------------------------------
# FRAME collation tests
# ---------------------------------------------------------------------------


class TestFRAME:
    """FRAME composed model — the assembled whole."""

    def test_minimal_frame_construction(self):
        """All 5 parts are required — empty defaults are valid."""
        frame = FRAME(
            facts=FrameFacts(
                profile=Profile(name="test", summary="test"),
                architecture=Architecture(summary="test"),
            ),
            rules=FrameRules(),
            map=FrameMap(),
            expect=FrameExpect(),
            acts=FrameActs(),
        )
        d = frame.to_dict()
        assert "facts" in d
        assert d["rules"] is not None
        assert d["map"] is not None
        assert d["expect"] is not None
        assert d["acts"] is not None

    def test_full_frame_construction(self):
        """FRAME with all five parts."""
        frame = FRAME(
            facts=FrameFacts(
                profile=Profile(name="test", summary="test"),
                architecture=Architecture(summary="test"),
            ),
            rules=FrameRules(),
            map=FrameMap(),
            expect=FrameExpect(),
            acts=FrameActs(),
        )
        d = frame.to_dict()
        assert d["rules"] is not None
        assert d["map"] is not None

    def test_frame_to_json(self):
        """FRAME serializes to valid JSON."""
        frame = FRAME(
            facts=FrameFacts(
                profile=Profile(name="test", summary="test"),
                architecture=Architecture(summary="test"),
            ),
            rules=FrameRules(governance_level="strict"),
            map=FrameMap(),
            expect=FrameExpect(),
            acts=FrameActs(),
        )
        j = frame.to_json()
        parsed = json.loads(j)
        assert parsed["facts"]["profile"]["name"] == "test"
        assert parsed["rules"]["governance_level"] == "strict"
        assert parsed["map"] is not None
        assert parsed["expect"] is not None
        assert parsed["acts"] is not None

    def test_frame_repr(self):
        """FRAME has a useful repr."""
        frame = FRAME(
            facts=FrameFacts(
                profile=Profile(name="test", summary="test"),
                architecture=Architecture(summary="test"),
            ),
            rules=FrameRules(),
            map=FrameMap(),
            expect=FrameExpect(),
            acts=FrameActs(),
        )
        r = repr(frame)
        assert "FRAME(" in r


# ---------------------------------------------------------------------------
# Null preservation tests
# ---------------------------------------------------------------------------


class TestNullPreservation:
    """D8: to_dict() preserves nulls in output."""

    def test_null_fields_present_in_dict(self):
        """Optional fields with None value appear as null keys in dict."""
        a = Architecture(summary="test")
        d = a.to_dict()
        assert "backend_layers" in d
        assert d["backend_layers"] is None
        assert "data_flow" in d
        assert d["data_flow"] is None

    def test_null_fields_present_in_json(self):
        """Optional fields with None value appear as null in JSON."""
        a = Architecture(summary="test")
        j = a.to_json()
        parsed = json.loads(j)
        assert "backend_layers" in parsed
        assert parsed["backend_layers"] is None

    def test_empty_lists_preserved(self):
        """Empty lists are preserved, not converted to null."""
        facts = FrameFacts(
            profile=Profile(name="test", summary="test"),
            architecture=Architecture(summary="test"),
        )
        d = facts.to_dict()
        assert d["sources"] == []
        assert d["quirks"] == []
