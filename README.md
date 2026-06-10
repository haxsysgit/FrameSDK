# framesdk

The Python SDK for [FRAME](https://github.com/haxsysgit/FRAME) — a typed project-context architecture for AI-assisted development.

When you switch coding agents, the project forgets itself. Not its code — the code is fine. But the *understanding*. The rules you agreed on. The decisions you made and why. The checks that matter. Things previous agents touched or broke.

FRAME gives the project a typed shape that agents and tools read consistently. framesdk is how Python tools read that shape.

## What it does

Takes a `.haxaml/` directory with 5 YAML files and returns a typed `FRAME` object:

```python
from frame import load_frame

frame = load_frame(".haxaml/")
frame.facts.profile.name          # "Pharmax"
frame.rules.governance_level      # "strict"
frame.map.entrypoints[0].path     # "Backend/main.py"
frame.expect.checks["backend_tests"].pass_condition  # "exit_code == 0"
```

Every downstream tool — Haxaml, a CLI, a CI pipeline — gets the same shaped answer. Cross-language SDKs return the same JSON shape.

## Install

```bash
uv add framesdk
# or
pip install framesdk
```

Requires Python 3.11+. Three dependencies: PyYAML, jsonschema, referencing. That's it. No Pydantic, no heavy framework.

## What's in the box

- **loaders** — `load_frame()` builds a typed FRAME from 5 YAML files. Strict single-directory discovery. Schema and character limit validation at load time.
- **models** — 27 typed dataclasses across 7 files. One import: `from frame.models import FRAME`.
- **validators** — Schema, character limits, cross-file consistency. Callable independently or through the loader.
- **translators** — YAML→JSON with full normalization. Handles yes/True, ~/None, on/off rejection.

## Usage patterns

```python
from frame import load_frame, translate_directory, validate_file

# Full pipeline — load all 5 files, validate, assemble
frame = load_frame(".haxaml/")

# Translate YAML to clean dict (normalized, but no validation)
data = translate_directory(".haxaml/")

# Validate a single file without loading the full model
result = validate_file(".haxaml/facts.yaml")
print(result.summary())  # "valid" or "2 error(s), 1 warning(s)"

# Serialize for cross-language use
json_string = frame.to_json()
```

## How it's built

Spec-first. Every module has a design doc (`docs/models.md`, `docs/loaders.md`, etc.) with locked decisions before any code was written. 106 tests cover construction, serialization, YAML normalization, schema enforcement, character limits, cross-file checks, and integration against a real Pharmax fixture.

No graph building, no cross-referencing, no governance. That's Haxaml's job. framesdk is pure ingestion — load, validate, assemble, return.
