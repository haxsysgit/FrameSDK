"""FRAME Python SDK — v0.3.0

The uniform interface for reading and working with FRAME project context files.

Package layout:
    frame.models        — Typed dataclass models for all five FRAME parts
    frame.loaders       — YAML file loading, normalization, assembly into FRAME
    frame.validators    — Schema validation, character limits, cross-file checks
    frame.translators   — YAML ↔ JSON conversion with normalization
    frame.computations  — Graph, cross-referencing, consistency (future)
    frame.helpers       — Shared utilities (future)

Primary imports for downstream tools:
    from framesdkpy.models import FRAME, FrameFacts, FrameRules, FrameMap, FrameExpect, FrameActs
    from framesdkpy.translators import translate_file, translate_directory, translate_to_dict
    from framesdkpy.loaders import load_frame  # (once implemented)
"""

from framesdkpy.models import FRAME, FrameFacts, FrameRules, FrameMap, FrameExpect, FrameActs
from framesdkpy.translators import translate_file, translate_directory, translate_to_dict, translate_to_json_string

__all__ = [
    "FRAME",
    "FrameFacts",
    "FrameRules",
    "FrameMap",
    "FrameExpect",
    "FrameActs",
    "translate_file",
    "translate_directory",
    "translate_to_dict",
    "translate_to_json_string",
]
