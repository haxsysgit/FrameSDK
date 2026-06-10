"""FrameRules model and sub-models — how to work safely in this repo.

Mirrors schemas/json/rules.schema.json exactly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from frame.models.base import FrameBaseModel


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class Policy(FrameBaseModel):
    """Durable project policy (role access, lifecycle, audit, auth).

    Moved from Facts to Rules — policies are behavioral constraints,
    not current project truth.
    """

    id: str
    """Stable identifier for cross-referencing. maxLength: 100."""

    name: str
    """Short policy name. maxLength: 150."""

    rule: str
    """The policy rule text. maxLength: 500."""


@dataclass(slots=True)
class CoreRule(FrameBaseModel):
    """Core behavioral constraint. Has an id for cross-referencing."""

    id: str
    """Stable identifier. maxLength: 100."""

    rule: str
    """The constraint text. maxLength: 500."""


@dataclass(slots=True)
class Command(FrameBaseModel):
    """Named shell command with a fixed schema.

    kind: setup (install deps), verify (validation check), or run (server/interactive).
    The mechanical validator uses kind to decide which commands to execute.
    """

    run: str
    """Shell command to execute. maxLength: 500."""

    kind: str
    """Fixed enum: setup, verify, run."""

    purpose: str
    """Why this command exists. maxLength: 300."""


@dataclass(slots=True)
class Dont(FrameBaseModel):
    """Thing you must never do. severity: critical (blocks) or warning (flags)."""

    id: str
    """Stable identifier. maxLength: 100."""

    rule: str
    """The forbidden action. maxLength: 300."""

    severity: str = "critical"
    """Enum: critical, warning. critical blocks the agent; warning flags it."""


@dataclass(slots=True)
class AskFirst(FrameBaseModel):
    """Trigger needing human approval before the agent proceeds.

    trigger_type: file_pattern (matches against files the agent will touch)
    or task_pattern (matches against the agent's stated task description).
    """

    id: str
    """Stable identifier. maxLength: 100."""

    trigger_type: str
    """Fixed enum: file_pattern, task_pattern."""

    trigger: str
    """The pattern to match against. maxLength: 300."""

    reason: str
    """Why approval is needed. maxLength: 300."""


@dataclass(slots=True)
class Hint(FrameBaseModel):
    """Skill reference, known gotcha, or task-specific guidance.

    Hints are not enforced — they help the agent work faster.
    """

    id: str
    """Stable identifier. maxLength: 100."""

    hint: str
    """The guidance text. maxLength: 300."""


# ---------------------------------------------------------------------------
# Main model
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class FrameRules(FrameBaseModel):
    """How to work safely in this repo. Populated from rules.yaml.

    governance_level controls enforcement strictness:
    relaxed → agents proceed freely, ask_first is advisory
    normal   → ask_first warns but doesn't block
    strict   → ask_first blocks, donts enforced, validator must pass
    """

    governance_level: str = "normal"
    """Enum: relaxed, normal, strict. Controls Haxaml enforcement strictness."""

    rules: list[CoreRule] = field(default_factory=list)
    """Core behavioral constraints."""

    policies: list[Policy] = field(default_factory=list)
    """Durable project policies (role access, lifecycle, audit)."""

    commands: dict[str, Command] = field(default_factory=dict)
    """Named shell commands. Key is the command name used by expect.checks.command_ref."""

    donts: list[Dont] = field(default_factory=list)
    """Things you must never do. severity determines enforcement."""

    ask_first: list[AskFirst] = field(default_factory=list)
    """Triggers needing human approval. Enforcement depends on governance_level."""

    hints: list[Hint] = field(default_factory=list)
    """Skill references, gotchas, task-specific guidance."""

    code_style: dict | None = None
    """Formatting, naming, conventions. Free-form — varies per language. Advisory limit 1000 chars."""

    git: dict | None = None
    """Branch strategy, commit style, PR rules. Free-form — varies per team. Advisory limit 1000 chars."""
