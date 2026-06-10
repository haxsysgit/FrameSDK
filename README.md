# frame-py

Python SDK for [FRAME](https://github.com/haxsysgit/FRAME) — typed project-context for AI-assisted development.

Loads, validates, translates, and assembles all 5 FRAME files from a `.haxaml/` directory into a typed Python object.

```python
from frame import load_frame

frame = load_frame(".haxaml/")
print(frame.facts.profile.name)      # "Pharmax"
print(frame.rules.governance_level)  # "strict"
print(frame.map.entrypoints[0].path) # "Backend/main.py"
```

## Install

```bash
pip install frame-py
```

## What it does

Reads 5 YAML files (facts, rules, map, expect, acts) from a directory and returns a typed FRAME object. Validates against JSON Schema, enforces character limits, checks cross-file consistency. Empty files are valid — the SDK validates structure, Haxaml enforces content depth.

## Usage

```python
from frame import load_frame, translate_file, validate_file

# Full pipeline
frame = load_frame(".haxaml/")

# Individual operations
data = translate_file("facts.yaml")      # YAML → clean dict
result = validate_file("rules.yaml")      # schema + limits check
```

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```
