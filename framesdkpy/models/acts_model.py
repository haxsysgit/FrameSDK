"""FrameActs model and sub-models — checked activity record.

Mirrors schemas/json/acts.schema.json exactly.
Acts is run history — what went in, what came out, what changed, what checks ran.
Size cap: 50KB. Exceeded → oldest runs auto-rotated to acts_archive/.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from framesdkpy.models.base import FrameBaseModel


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class RunCheck(FrameBaseModel):
    """A check considered or executed during a single run.

    Collapsed from the old checks_seen/checks_ran split into one field with status.
    status: ran (check was executed) or skipped (considered but not applicable).
    result: only present when status=ran. pass or fail.
    reason: only present when status=skipped. Why it was skipped.
    """

    id: str
    """Ref to expect.checks.<name>. This is the check that was considered or executed."""

    status: str
    """Enum: ran, skipped. ran = executed, skipped = considered but not applicable."""

    result: str | None = None
    """Enum: pass, fail. Only set when status=ran."""

    reason: str | None = None
    """Why skipped. Only set when status=skipped. maxLength: 200."""


@dataclass(slots=True)
class Run(FrameBaseModel):
    """A single agent session run. Has an id for cross-referencing.

    work_kind: tags for what kind of work was done (code, test, review, docs, deploy).
    status: the overall run outcome. Pass means all checks passed.
    Pass_with_risks means passed but with warnings. Fail means something broke.
    Needs_clarification means the agent couldn't determine the outcome.
    """

    id: str
    """Stable identifier. Used for cross-referencing from other Acts entries. maxLength: 100."""

    actor: str
    """Who or what did the work (agent name, model, or human). maxLength: 100."""

    goal: str
    """What the run was trying to accomplish. maxLength: 300."""

    status: str
    """Enum: pass, pass_with_risks, fail, needs_clarification."""

    work_kind: list[str] | None = None
    """Tags: code, test, review, docs, deploy."""

    keywords: list[str] | None = None
    """Topic tags for searchable retrieval."""

    input_summary: str | None = None
    """What went into the run. maxLength: 300."""

    output_summary: str | None = None
    """What came out. maxLength: 300."""

    touched: list[str] | None = None
    """Files, paths, or surfaces touched during the run."""

    changed_facts: list[str] | None = None
    """Facts that were modified during the run."""

    rules_followed: list[str] | None = None
    """Rule or policy ids that were applied."""

    checks: list[RunCheck] | None = None
    """Checks considered or executed this run. Each has status and optional result/reason."""

    links: list[dict] = field(default_factory=list)
    """Typed links from this entry to other FRAME refs."""


@dataclass(slots=True)
class Blocker(FrameBaseModel):
    """Something preventing progress. Has an id for cross-referencing."""

    id: str
    """Stable identifier. maxLength: 100."""

    description: str
    """What is blocking progress. maxLength: 300."""

    links: list[dict] = field(default_factory=list)
    """Typed links from this entry to other FRAME refs."""


# ---------------------------------------------------------------------------
# Main model
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class FrameActs(FrameBaseModel):
    """Run history — what happened across agent sessions.

    Populated from acts.yaml. Grows over time as agents work on the project.
    Older runs auto-rotate to acts_archive/ when the file exceeds 50KB.
    """

    frame: dict = field(default_factory=dict)
    """Shared FRAME header block. Required by every FRAME file."""

    summary: str | None = None
    """Quick overview of recent activity. maxLength: 500."""

    runs: list[Run] = field(default_factory=list)
    """Per-session run records. Each has a stable id for cross-referencing."""

    blockers: list[Blocker] = field(default_factory=list)
    """Things preventing progress. Each has a stable id."""

    handoff: dict | None = None
    """What the next agent needs to know. Free-form."""

    evidence: list[dict] = field(default_factory=list)
    """Evidence entries supporting Acts claims."""

    links: list[dict] = field(default_factory=list)
    """Typed links from this file to other FRAME refs."""
