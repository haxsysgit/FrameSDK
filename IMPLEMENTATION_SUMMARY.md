# frame-py Implementation Summary

**Date:** 2026-06-10
**Version:** v0.3.0
**Tests:** 82 passing (29 models + 25 translators + 22 validators + 6 loaders)

## What was built

frame-py is the Python SDK for FRAME. It provides a uniform interface for reading,
validating, and working with FRAME project context files. Every downstream tool
(Haxaml, CLIs, future frame-js) gets the same shaped answer from frame-py.

### Architecture

```
frame/
├── __init__.py                     # Top-level re-exports
├── models/                         # Typed data carriers
│   ├── base.py                     # FrameBaseModel — to_dict, to_json, __repr__
│   ├── facts_model.py              # FrameFacts, Profile, Architecture, Source, Quirk, OpenQuestion
│   ├── rules_model.py              # FrameRules, Policy, CoreRule, Command, Dont, AskFirst, Hint
│   ├── map_model.py                # FrameMap, Group, PathEntry, Entrypoint, ManagedPath, UnmappedPath
│   ├── expect_model.py             # FrameExpect, MustHold, Check, Proof
│   ├── acts_model.py               # FrameActs, Run, RunCheck, Blocker
│   └── frame_model.py              # FRAME — collates all five parts
│
├── loaders/                        # File discovery, parsing, assembly
│   ├── yaml_reader.py              # Strict 5-file discovery + raw YAML parsing
│   ├── assembler.py                # Dict → typed FRAME model construction
│   └── __init__.py                 # load_frame() — full pipeline orchestrator
│
├── validators/                     # Schema, limit, and cross-file validation
│   ├── result.py                   # ValidationResult, ValidationError, ValidationWarning
│   ├── schema_validator.py         # JSON Schema validation with local $ref resolution
│   ├── limits_validator.py         # Character limit enforcement
│   ├── cross_file_validator.py     # Cross-file schema_version and file/role checks
│   └── __init__.py                 # validate_frame(), validate_file()
│
├── translators/                    # YAML ↔ JSON conversion
│   ├── normalizer.py               # YAML quirk resolution (yes→True, ~→None, etc.)
│   ├── yaml_to_json.py             # YAML file → clean JSON-compatible dict
│   └── __init__.py                 # translate_file(), translate_directory()
│
├── computations/                   # Future: graph, cross-referencing
└── helpers/                        # Future: shared utilities
```

### Pipeline (load_frame)

```
Directory path
  ↓ yaml_reader.discover_frame_dir()
  │   Verifies exactly 5 files: facts.yaml, rules.yaml, map.yaml, expect.yaml, acts.yaml
  ↓ yaml_reader.read_raw_yaml()
  │   Parses YAML into raw Python dicts (safe_load)
  ↓ normalizer.normalize_dict()
  │   Resolves YAML quirks: yes→True, no→False, ~→None, on/off→error
  ↓ validators.validate_against_schema()
  │   JSON Schema validation: types, required fields, enums
  ↓ validators.validate_limits()
  │   Character limits: enforced on core fields, advisory on descriptive
  ↓ assembler.assemble_frame()
  │   Cross-file check → builds typed FRAME object → returns
```

---

## What each test suite verifies

### test_models.py (29 tests)

**FrameFacts (6 tests):**
- Minimal construction with only required fields (profile, architecture)
- Full construction with all optional sub-models populated
- Required fields are non-nullable (Profile.name is str, not str|None)
- Architecture.summary is required
- to_dict() preserves nulls — optional fields with None appear as keys with null values
- to_json() produces valid parseable JSON

**FrameRules (5 tests):**
- Minimal construction with defaults (governance_level="normal")
- Full construction with policies, commands, donts, ask_first, hints
- Dont defaults to severity="critical"
- Command has exactly three required fields (run, kind, purpose)
- Commands dict serializes correctly

**FrameMap (4 tests):**
- Minimal construction with all empty lists
- Full construction with groups, paths, entrypoints, managed_paths, unmapped_paths
- PathEntry.id is optional (only needed for cross-referencing)
- ManagedPath.id is optional (only needed for cross-referencing)

**FrameExpect (3 tests):**
- Minimal construction with empty checks and proof
- Full construction with outcomes, must_hold, checks, proof
- Various pass_condition formats work (exit_code, stdout contains)

**FrameActs (4 tests):**
- Minimal construction with empty runs and blockers
- Full construction with run records and nested RunCheck objects
- RunCheck with status=ran may have result=None (loader populates this)
- RunCheck with status=skipped may have reason=None (loader populates this)

**FRAME collation (4 tests):**
- Minimal construction with only Facts (rules/map/expect/acts are None)
- Full construction with all five parts populated
- to_json() produces valid JSON with correct structure
- repr() displays meaningful class name

**Null preservation (3 tests):**
- Optional fields with None appear as keys in to_dict()
- Optional fields with None appear as keys in JSON output
- Empty lists are preserved (not converted to null)

### test_translators.py (25 tests)

**Normalizer (13 tests):**
- yes/Yes/YES/true/y → True
- no/No/NO/false/n → False
- ~ → None
- null/Null/NULL → None
- on/off raises TranslationError (ambiguous)
- Empty string "" preserved as empty string (NOT coerced to None)
- Python None stays None
- Bare numbers pass through unchanged
- Boolean values (already parsed by YAML) pass through
- Regular strings pass through unchanged
- Quoted "yes" in YAML (parsed as string by YAML lib) → normalized to True
- Nested dicts normalize recursively
- Nested lists normalize recursively

**translate_to_dict (4 tests):**
- Basic YAML string to dict
- YAML with quirks (yes, no, ~, null)
- Empty YAML returns empty dict
- YAML with nested lists

**translate_file (3 tests):**
- Temp YAML file → translated dict
- Nonexistent file raises FileNotFoundError
- Wrong extension (.txt) raises ValueError

**translate_directory (3 tests):**
- Full directory with all 5 files → dict of dicts
- Missing file raises FileNotFoundError
- Nonexistent directory raises FileNotFoundError

**translate_to_json_string (2 tests):**
- Produces valid parseable JSON
- JSON preserves types (True, 42, null)

### test_validators.py (22 tests)

**ValidationResult (6 tests):**
- Empty result is valid and clean
- Result with only warnings is valid but not clean
- Result with errors is invalid
- Merge combines errors and warnings from multiple results
- add_error() convenience method populates expected/actual
- summary() produces human-readable string

**Schema validator (4 tests):**
- Valid Facts dict passes schema validation
- Missing required field (profile) is caught
- Minimal valid Rules passes
- All 5 file types pass with minimal valid data

**Limits validator (4 tests):**
- Value within limit passes
- Core field (id) exceeding maxLength → error
- Advisory field within limit → passes clean
- Advisory field exceeding maxLength → warns, doesn't error

**Cross-file validator (4 tests):**
- All matching schema_versions pass
- Version mismatch catches mismatched versions
- Wrong file field catches file type mismatch
- Wrong role field catches role mismatch

**validate_frame (4 tests):**
- Full valid directory passes end-to-end
- Missing file raises FileNotFoundError
- Schema version mismatch is caught
- File/role mismatch is caught

### test_loaders.py (6 tests)

- load_frame() returns typed FRAME object with all parts present
- Loaded FRAME serializes to JSON correctly
- Missing file raises FileNotFoundError
- Schema version mismatch raises FrameLoadError
- Missing required Facts fields raises FrameLoadError
- Nonexistent directory raises FileNotFoundError

---

## Audit findings

### Stale files removed
- `frame/loaders/loader.py` — old generic loader, replaced by yaml_reader + assembler
- `frame/models/model.py` — old flat model, replaced by five typed model files
- `frame/computations/report.py` — old ValidationReport, replaced by ValidationResult
- `frame/helpers/provisional.py` — dead code, never referenced
- `frame/validators/mechanical_validator.py` — belongs in Haxaml, not frame-py

### Over-engineering avoided
- No separate assembler package — lives inside loaders (Decision D6.5)
- No Pydantic dependency — pure dataclasses (Decision D4)
- No graph/cross-reference computation yet — deferring to future
- No JSON-to-YAML translator yet — low priority (Decision D15)
- No abstract base class for validators — simple functions returning result objects

### Design consistency
- Every module follows the same pattern: public API in __init__.py, implementation in sub-modules
- All validators return result objects (never raise for validation failures)
- All translators return clean dicts (never typed models)
- All models inherit from FrameBaseModel for uniform serialization
- Character limits enforced by field category (core vs advisory), not by blanket rules
