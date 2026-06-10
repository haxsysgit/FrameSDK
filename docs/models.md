# frame-py Models — Specification

**Status:** Agreed. Code follows this spec.
**Date:** 2026-06-10

---

## Job

Models are pure typed data carriers. They hold validated data from the loader. They expose typed dot access. They serialize to clean JSON. They do NOT validate, load files, or enforce rules — the loader already did that.

---

## Architecture

```
frame/models/
├── __init__.py           ← Re-exports: FRAME, FrameFacts, FrameRules, etc.
├── base.py               ← Shared base classes (to_dict, to_json, __repr__)
├── facts.py              ← FrameFacts, Profile, Architecture, Quirk, Source, OpenQuestion
├── rules.py              ← FrameRules, Command, Dont, AskFirst, Policy, Hint
├── map.py                ← FrameMap, Group, Path, Entrypoint, ManagedPath
├── expect.py             ← FrameExpect, Outcome, MustHold, Check, Proof
├── acts.py               ← FrameActs, Run, RunCheck, Blocker
└── frame.py              ← FRAME — collates all five parts into one model
```

One file per FRAME part. One collation file (`frame.py`) that composes the five. Every downstream tool imports from `frame.models` and gets everything.

---

## Decisions

### D7: Nested models for frequent blocks, flat dicts for free-form

Blocks used frequently and queried by tools get nested typed models:

| Block | Model class | Reason |
|---|---|---|
| facts.profile | `Profile` | Frequent access, known shape |
| facts.architecture | `Architecture` | Structured, known sub-fields |
| facts.technology | `Technology` | Structured, known keys |
| rules.commands | `Command` per key | Fixed schema (run, kind, purpose) |
| rules.donts[] | `Dont` per entry | Fixed schema (id, rule, severity) |
| rules.ask_first[] | `AskFirst` per entry | Fixed schema (id, trigger_type, trigger, reason) |
| rules.policies[] | `Policy` per entry | Fixed schema (id, name, rule) |
| expect.checks | `Check` per key | Fixed schema, feeds validator |
| acts.runs[] | `Run` per entry | Fixed schema, queryable |
| acts.runs[].checks[] | `RunCheck` per entry | Fixed schema |

Blocks that are free-form and vary per project stay as dicts:

| Block | Reason |
|---|---|
| facts.environments | Per-env keys vary |
| facts.persistence | Varies by ORM/storage |
| rules.code_style | Free-form, per-language |
| rules.git | Free-form, per-team |
| facts.classification | Loose structure |

### D8: to_dict() preserves nulls

If `repo_shape` is `None`, `to_dict()` outputs `{"repo_shape": null}`. The JSON shape is always complete. Cross-language tools can rely on every key existing — even if its value is null.

### D9: Required fields are non-nullable at the model level

The model IS the type contract. If `Profile.name` is required by the schema, it's typed as `str` (not `str | None`). Downstream code never checks `if frame.facts.profile.name is None` — the loader guaranteed it's populated or load failed.

### D10: Separation of concerns

Five model files (facts.py, rules.py, map.py, expect.py, acts.py) + one collation file (frame.py). Each file owns one FRAME part. Each file is readable and debuggable independently. A collaborator fixing a Facts model issue knows to open `facts.py`.

### D11: Comments and annotations

All generated code will include inline comments explaining non-obvious logic, parameter purposes, and design intent. Docstrings on every public class and method. The code should be skimmable by a developer who's never read the spec.

---

## Data model

### frame/models/facts.py

```python
@dataclass(slots=True)
class Profile:
    """Project identity. Required fields are non-nullable."""
    name: str                    # maxLength: 100
    summary: str                 # maxLength: 300
    repo_shape: str | None       # enum: split-backend-frontend, monorepo, etc.
    delivery_family: str | None  # enum: cli, web-app, mobile-app, etc.

@dataclass(slots=True)
class Architecture:
    """System layout. summary is required."""
    summary: str                 # maxLength: 500
    backend_layers: list[str] | None
    frontend_layers: list[str] | None
    data_flow: str | None        # maxLength: 500
    deployment_topology: str | None  # maxLength: 500

@dataclass(slots=True)
class Technology:
    """Structured technology stack."""
    language: str | None
    framework: str | None
    database: str | None
    extensions: dict | None      # Optional free-form keys

@dataclass(slots=True)
class Source:
    """Trusted source-of-truth file."""
    id: str                      # maxLength: 100
    path: str                    # maxLength: 200
    purpose: str                 # maxLength: 300

@dataclass(slots=True)
class Quirk:
    """Weird project-specific thing agents must understand."""
    id: str                      # maxLength: 100
    description: str             # maxLength: 200
    why: str                     # maxLength: 300

@dataclass(slots=True)
class OpenQuestion:
    """Thing nobody has decided yet."""
    id: str                      # maxLength: 100
    question: str                # maxLength: 300
    context: str                 # maxLength: 300

@dataclass(slots=True)
class FrameFacts:
    """Stable project truth. Populated by the loader from facts.yaml."""
    profile: Profile
    classification: dict | None
    technology: Technology | None
    architecture: Architecture
    environments: dict | None
    persistence: dict | None
    sources: list[Source]
    quirks: list[Quirk]
    open_questions: list[OpenQuestion]
```

### frame/models/rules.py

```python
@dataclass(slots=True)
class Policy:
    """Durable project policy (role access, lifecycle, audit)."""
    id: str                      # maxLength: 100
    name: str                    # maxLength: 150
    rule: str                    # maxLength: 500

@dataclass(slots=True)
class CoreRule:
    """Core behavioral constraint."""
    id: str                      # maxLength: 100
    rule: str                    # maxLength: 500

@dataclass(slots=True)
class Command:
    """Named shell command. kind: setup, verify, or run."""
    run: str                     # maxLength: 500
    kind: str                    # enum: setup, verify, run
    purpose: str                 # maxLength: 300

@dataclass(slots=True)
class Dont:
    """Thing you must never do. severity: critical or warning."""
    id: str                      # maxLength: 100
    rule: str                    # maxLength: 300
    severity: str                # enum: critical, warning; default: critical

@dataclass(slots=True)
class AskFirst:
    """Trigger that needs human approval before agent proceeds."""
    id: str                      # maxLength: 100
    trigger_type: str            # enum: file_pattern, task_pattern
    trigger: str                 # maxLength: 300
    reason: str                  # maxLength: 300

@dataclass(slots=True)
class Hint:
    """Skill reference, known gotcha, task-specific guidance."""
    id: str                      # maxLength: 100
    hint: str                    # maxLength: 300

@dataclass(slots=True)
class FrameRules:
    """How to work safely in this repo. Populated from rules.yaml."""
    governance_level: str        # enum: relaxed, normal, strict
    rules: list[CoreRule]
    policies: list[Policy]
    commands: dict[str, Command]  # Key is command name
    code_style: dict | None
    git: dict | None
    donts: list[Dont]
    ask_first: list[AskFirst]
    hints: list[Hint]
```

### frame/models/map.py

```python
@dataclass(slots=True)
class Group:
    """Logical grouping of paths. Supports wildcards."""
    id: str                      # maxLength: 100
    label: str                   # maxLength: 150
    paths: list[str]             # Wildcards allowed

@dataclass(slots=True)
class PathEntry:
    """Critical individual file. Explicit path only."""
    id: str | None               # maxLength: 100 (optional for cross-referencing)
    path: str                    # maxLength: 200
    purpose: str                 # maxLength: 300

@dataclass(slots=True)
class Entrypoint:
    """CLI/API/web entry point."""
    id: str                      # maxLength: 100
    path: str                    # maxLength: 200
    kind: str                    # enum: cli, api, web, script
    description: str | None      # maxLength: 300

@dataclass(slots=True)
class ManagedPath:
    """Path under special rule. Supports wildcards."""
    id: str | None               # maxLength: 100 (optional for cross-referencing)
    path: str                    # maxLength: 200
    rule: str                    # enum: generated, config, immutable

@dataclass(slots=True)
class UnmappedPath:
    """Path not yet placed in the map."""
    path: str                    # maxLength: 200
    reason: str                  # maxLength: 200

@dataclass(slots=True)
class FrameMap:
    """Where things live. Populated from map.yaml."""
    structure: str | None        # maxLength: 800
    roots: dict | None
    groups: list[Group]
    paths: list[PathEntry]
    entrypoints: list[Entrypoint]
    managed_paths: list[ManagedPath]
    unmapped_paths: list[UnmappedPath]
```

### frame/models/expect.py

```python
# Definitions follow schema: outcomes (dict of summary strings), must_hold (list),
# checks (dict of Check objects), done_when (dict), proof (list), handoff (dict).

@dataclass(slots=True)
class MustHold:
    """Invariant that must stay true."""
    id: str
    statement: str

@dataclass(slots=True)
class Check:
    """Verification check. Feeds mechanical validator."""
    name: str
    what: str                    # What is being checked
    how: str | None              # How to check: test, build, lint, grep, manual
    command_ref: str | None      # Ref to rules.commands.<name>
    pass_condition: str | None   # Machine-parseable: exit_code, stdout, file_exists

@dataclass(slots=True)
class Proof:
    """Required evidence type."""
    id: str
    type: str                    # enum: review, smoke_test, static_check, unavailable
    description: str

@dataclass(slots=True)
class FrameExpect:
    """What must pass. Feeds mechanical validator."""
    outcomes: dict | None
    must_hold: list[MustHold]
    checks: dict[str, Check]    # Key is check name
    done_when: dict | None
    proof: list[Proof]
    handoff: dict | None
```

### frame/models/acts.py

```python
@dataclass(slots=True)
class RunCheck:
    """Check considered or executed during a run."""
    id: str                      # Ref to expect.checks.<name>
    status: str                  # enum: ran, skipped
    result: str | None           # pass, fail (only when status=ran)
    reason: str | None           # Why skipped (only when status=skipped)

@dataclass(slots=True)
class Run:
    """Per-session run record."""
    id: str
    actor: str
    goal: str
    work_kind: list[str] | None  # code, test, review, docs, deploy
    keywords: list[str] | None
    input_summary: str | None
    output_summary: str | None
    status: str                  # pass, pass_with_risks, fail, needs_clarification
    touched: list[str] | None
    changed_facts: list[str] | None
    rules_followed: list[str] | None
    checks: list[RunCheck] | None

@dataclass(slots=True)
class Blocker:
    """Thing preventing progress."""
    id: str
    description: str

@dataclass(slots=True)
class FrameActs:
    """Run history. Populated from acts.yaml."""
    summary: str | None
    runs: list[Run]
    blockers: list[Blocker]
    handoff: dict | None
```

### frame/models/frame.py

```python
@dataclass(slots=True)
class FRAME:
    """The assembled whole. Produced by the loader, consumed by all tools."""
    facts: FrameFacts           # Required — every project has facts
    rules: FrameRules | None    # Optional at first, required for governance
    map: FrameMap | None        # Optional at first
    expect: FrameExpect | None  # Optional at first, required for mechanical validation
    acts: FrameActs | None      # Optional at first, grows over time

    def to_dict(self) -> dict:
        """Serialize to clean JSON-compatible dict. Preserves nulls."""
        ...

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        ...
```

### frame/models/base.py

```python
@dataclass(slots=True)
class FrameBaseModel:
    """Shared serialization logic for all FRAME models."""

    def to_dict(self) -> dict:
        """Recursive dict conversion. Preserves nulls. Handles nested models."""
        ...

    def to_json(self, indent: int = 2) -> str:
        """JSON string from to_dict()."""
        ...
```

---

## Imports

Every downstream tool imports once:

```python
from framesdkpy.models import FRAME, FrameFacts, FrameRules, FrameMap, FrameExpect, FrameActs
```

All sub-models (Profile, Check, Run, etc.) are re-exported from the package `__init__.py`.
