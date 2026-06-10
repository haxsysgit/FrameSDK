"""FrameExpect model and sub-models — what must pass.

Mirrors schemas/json/expect.schema.json exactly.
The expect block feeds directly into the mechanical validator.
checks connect to rules.commands via command_ref.
pass_condition defines machine-parseable success criteria.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from framesdkpy.models.base import FrameBaseModel


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class MustHold(FrameBaseModel):
    """Invariant that must remain true. Has an id for cross-referencing."""

    id: str
    """Stable identifier. maxLength: 100."""

    statement: str
    """The invariant statement. maxLength: 300."""


@dataclass(slots=True)
class Check(FrameBaseModel):
    """Verification check that feeds the mechanical validator.

    command_ref points to rules.commands.<name> — the shell command to execute.
    pass_condition is machine-parseable: 'exit_code == 0', 'stdout contains X',
    'stdout matches REGEX', or 'file_exists PATH'.
    """

    name: str
    """Short check name displayed in reports. maxLength: 100."""

    what: str
    """What is being checked — human-readable explanation. maxLength: 300."""

    how: str | None = None
    """How the check works: test, build, lint, grep, manual. maxLength: 200."""

    command_ref: str | None = None
    """Ref to rules.commands.<name> for executable verification. maxLength: 200."""

    pass_condition: str | None = None
    """Machine-parseable success criteria. Examples:
    'exit_code == 0'
    'stdout contains BUILD SUCCESS'
    'stdout matches ^[a-f0-9]{12}_'
    'file_exists dist/index.html'
    """


@dataclass(slots=True)
class Proof(FrameBaseModel):
    """Required evidence type. Has an id for cross-referencing.

    type: review (human review needed), smoke_test (quick sanity check),
    static_check (linter/type checker), unavailable (can't verify yet).
    """

    id: str
    """Stable identifier. maxLength: 100."""

    type: str
    """Fixed enum: review, smoke_test, static_check, unavailable."""

    description: str
    """What evidence is needed. maxLength: 300."""


# ---------------------------------------------------------------------------
# Main model
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class FrameExpect(FrameBaseModel):
    """What must pass — outcomes, invariants, checks, proof requirements.

    Populated from expect.yaml. This is the contract the mechanical validator
    enforces. checks connect to rules.commands via command_ref.
    """

    outcomes: dict | None = None
    """Named expected results of work. Keys are outcome names."""

    must_hold: list[MustHold] = field(default_factory=list)
    """Invariants that must stay true. Each has a stable id."""

    checks: dict[str, Check] = field(default_factory=dict)
    """Verification checks. Key is the check name — used as command_ref target."""

    done_when: dict | None = None
    """Completion conditions. Free-form keys."""

    proof: list[Proof] = field(default_factory=list)
    """Required evidence types. Each has a stable id."""

    handoff: dict | None = None
    """State to pass to the next session. Free-form."""
