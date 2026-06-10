"""FRAME translators — YAML/JSON conversion with normalization.

Public API:
    translate_file("facts.yaml")    → dict
    translate_directory(".haxaml/") → {"facts": {...}, "rules": {...}, ...}
    translate_to_dict(yaml_string)  → dict
    translate_to_json_string(yaml)  → str
"""

from framesdkpy.translators.yaml_to_json import (
    translate_file,
    translate_directory,
    translate_to_dict,
    translate_to_json_string,
)
from framesdkpy.translators.normalizer import TranslationError

__all__ = [
    "translate_file",
    "translate_directory",
    "translate_to_dict",
    "translate_to_json_string",
    "TranslationError",
]
