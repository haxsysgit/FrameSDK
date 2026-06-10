# FrameSDK Loaders -- Specification

**Status:** Agreed. Code follows this spec.
**Date:** 2026-06-10

---

## Job

A loader takes a directory path and returns a typed, validated, normalized FRAME object composed of five parts: FrameFacts, FrameRules, FrameMap, FrameExpect, FrameActs.

No graph building. No cross-referencing. No governance. Pure ingestion.

---

## Architecture

```
frame/loaders/
├── __init__.py           ← Public API: load_frame(dir_path)
├── yaml_reader.py        ← Raw YAML parsing, file discovery
├── normalizer.py         ← Type cleanup, default injection, character trimming
└── assembler.py          ← Combines 5 parts into one FRAME
```

Flow:

```
Directory path
  ↓
yaml_reader verifies exactly 5 files exist: facts.yaml, rules.yaml, map.yaml, expect.yaml, acts.yaml
  ↓
yaml_reader parses each into raw Python dicts
  ↓
normalizer cleans each dict:
  -- Trims strings to maxLength (core fields error, advisory fields warn)
  -- Replaces YAML weirdness (null → None, yes → True, 123 → 123)
  -- Injects defaults for optional fields
  -- Flags missing required core fields
  ↓
assembler validates cross-file consistency:
  -- All schema_version fields match
  -- All file/role fields match their expected values
  ↓
assembler builds FRAME:
  -- FRAME.facts: FrameFacts
  -- FRAME.rules: FrameRules
  -- etc.
  ↓
Returns FRAME
```

---

## Decisions

### D1: Validation at load time (split enforcement)

Core governance fields (ids, names, rules, checks, command_refs, pass_conditions) are validated and enforced at load time. Load fails if they're missing or invalid.

Descriptive/advisory fields (code_style, git, architecture notes, environment descriptions) are validated and warned at load time. Load succeeds but logs warnings.

### D2: Character limits -- error for core, warn for advisory

Core fields exceeding maxLength → load fails with clear error.
Advisory fields exceeding maxLength → load succeeds, warning emitted.

### D3: Strict single-directory discovery

The loader receives exactly ONE directory path. It looks inside that directory for exactly 5 files: facts.yaml, rules.yaml, map.yaml, expect.yaml, acts.yaml.

It NEVER:
- Searches parent directories
- Searches sibling directories
- Picks up individual scattered files
- Does fuzzy matching on filenames

If any file is missing → load fails.
If the directory doesn't exist → load fails.
If extra YAML files exist in the directory → they are ignored (not an error).

The caller controls where FRAME lives. The loader doesn't guess.

### D4: Dataclasses, not Pydantic

The returned models use Python dataclasses. Validation happens at load time, not at model instantiation. Dataclasses are pure typed carriers -- fast, zero-dependency, readable.

### D5: Five distinct typed parts

```
FRAME
├── facts: FrameFacts
├── rules: FrameRules
├── map: FrameMap
├── expect: FrameExpect
└── acts: FrameActs
```

Not a generic "FrameDocument" with optional nullable parts. Each part is a distinct model class with its own fields.

### D6: Return typed dataclasses that serialize to clean JSON

Internal: Python tools (Haxaml, CLIs) use typed dot access (`frame.facts.profile.name`).

External: Cross-language tools consume JSON (`frame.to_dict()`, `frame.to_json()`).

The JSON shape is the cross-language contract. The dataclasses are the Python binding. frame-js returns the same JSON shape. Any tool can switch SDKs without changing how it reads data.

---

## Data model

```python
@dataclass(slots=True)
class FrameFacts:
    profile: dict
    classification: dict | None
    technology: dict | None
    architecture: dict | None
    environments: dict | None
    persistence: dict | None
    sources: list[dict]
    quirks: list[dict]
    open_questions: list[dict]

@dataclass(slots=True)
class FrameRules:
    governance_level: str
    rules: list[dict]
    policies: list[dict]
    commands: dict
    code_style: dict | None
    git: dict | None
    donts: list[dict]
    ask_first: list[dict]
    hints: list[dict]

@dataclass(slots=True)
class FrameMap:
    structure: str | None
    roots: dict | None
    groups: list[dict]
    paths: list[dict]
    entrypoints: list[dict]
    managed_paths: list[dict]
    unmapped_paths: list[dict]

@dataclass(slots=True)
class FrameExpect:
    outcomes: dict | None
    must_hold: list[dict]
    checks: dict | None
    done_when: dict | None
    proof: list[dict]
    handoff: dict | None

@dataclass(slots=True)
class FrameActs:
    summary: str | None
    runs: list[dict]
    blockers: list[dict]
    handoff: dict | None

@dataclass(slots=True)
class FRAME:
    facts: FrameFacts
    rules: FrameRules | None
    map: FrameMap | None
    expect: FrameExpect | None
    acts: FrameActs | None
```

---

## Public API

```python
from framesdkpy.loaders import load_frame

# Returns FRAME or raises FrameLoadError
frame: FRAME = load_frame("/path/to/.haxaml")

# Each part is a typed model
print(frame.facts.profile["name"])
print(frame.rules.commands["backend_tests"]["run"])
print(frame.expect.checks["workflow_smoke"]["pass_condition"])
```

---

### Decision D6.5: Assembler lives inside loaders, not a separate package

The assembler builds the FRAME object from 5 validated dicts. It is tightly coupled to the loader's pipeline -- it only runs after loading and validation. Spinning it into its own package creates an abstraction nobody needs. Tools call `load_frame()`, not `assemble_frame()`. The pipeline is one cohesive flow: load -> validate -> normalize -> assemble -> return.
