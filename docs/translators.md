# FrameSDK Translators -- Specification

**Status:** Agreed. Code follows this spec.
**Date:** 2026-06-10

---

## Job

Translators convert between YAML and JSON representations of FRAME data. The primary path is YAML to JSON (what FRAME files become after ingestion). The secondary path is JSON → YAML (regenerating human-readable files from validated data). Future paths may include JSON → Markdown or JSON → plain text for display purposes.

Translators also handle YAML-to-JSON normalization -- resolving YAML quirks into clean JSON types that match the JSON Schema.

---

## Architecture

```
frame/translators/
├── __init__.py           ← Public API: translate_file(), translate_directory()
├── yaml_to_json.py       ← YAML to JSON with normalization rules
├── json_to_yaml.py       ← JSON → YAML preserving structure and readability
├── normalizer.py         ← YAML type resolution (yes→true, ~→null, etc.)
└── formatters.py         ← Future: JSON → Markdown, JSON → plain text
```

Flow (YAML to JSON):

```
YAML file path or directory path
  ↓
normalizer resolves YAML types:
  -- yes → true, no → false
  -- ~ → null
  -- YAML 1.1 octal like 0o755 → string or number (context-dependent)
  -- Multi-line strings preserved as-is
  -- Empty scalars → null
  ↓
yaml_to_json maps structure to JSON Schema shape:
  -- Object keys match schema property names
  -- Array items match schema item types
  -- Enum values validated against schema
  ↓
Output: clean JSON file or dict matching the json/ schema
```

---

## Decisions

### D15: YAML to JSON is priority; JSON → YAML is secondary

The critical path is reading FRAME YAML files and producing clean JSON for validators and cross-language tools. JSON → YAML is a convenience for regenerating human-readable FRAME files from validated JSON. Future formatters (JSON → Markdown, JSON → text) are tertiary -- not part of the initial build.

### D16: Support both per-file and per-directory translation

```python
# Per-file
translate_file("facts.yaml", to_format="json")

# Per-directory (all 5 files)
translate_directory(".haxaml/", to_format="json")
```

Same pattern as validators. Per-file for quick conversion. Per-directory for bulk operations.

### D17: Handle YAML quirks with explicit rules; fail on ambiguity

| YAML input | JSON output | Rule |
|---|---|---|
| `yes` | `true` | YAML 1.2 bool |
| `no` | `false` | YAML 1.2 bool |
| `on` / `off` | FAIL | Ambiguous -- YAML spec allows bool interpretation. Translator requires explicit `true`/`false`. |
| `~` | `null` | YAML null |
| `null` / `Null` / `NULL` | `null` | YAML null |
| Empty string `""` | `""` | Preserved as empty string, NOT coerced to null |
| Empty field (no value) | `null` | Missing value → null |
| `|` (literal block) | String with newlines | Preserved |
| `>` (folded block) | String with spaces | Folded to single line |
| Bare number `123` | `123` (int) or `123.0` (float) | Type preserved |
| Bare date `2026-06-10` | `"2026-06-10"` (string) | Dates are strings in FRAME, not native YAML timestamps |
| Quoted string `"yes"` | `"yes"` (string) | Quotes preserve string type -- never coerced to bool |

The translator is strict. If YAML is ambiguous, it fails with a clear error. It never guesses.

---

## Public API

```python
from framesdkpy.translators import translate_file, translate_directory, translate_to_dict

# Convert single file: facts.yaml → facts.json
translate_file("facts.yaml", to_format="json")
# Output saved as "facts.json" alongside the original

# Convert entire directory
translate_directory(".haxaml/", to_format="json")
# Output: .haxaml/facts.json, .haxaml/rules.json, etc.

# Programmatic: YAML string → Python dict (in-memory)
data: dict = translate_to_dict(yaml_string)

# Programmatic: Python dict → YAML string (in-memory)
yaml_string: str = translate_to_yaml(data_dict)

# Future (not in initial build)
translate_file("facts.yaml", to_format="markdown")  # Display-friendly table
translate_file("facts.yaml", to_format="text")       # Plain text representation
```

---

## Schema alignment

Translators use the JSON schemas (`schemas/json/`) as the canonical shape reference. When converting YAML to JSON, the output must match the JSON Schema's expected structure. When YAML has extra fields not in the schema, they are preserved (not stripped) but flagged as `unknown_field` errors -- preserving the stable schema shape.
