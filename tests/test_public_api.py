"""Public package API contract tests.

These tests protect the import surface promised to tool authors.
If a downstream FRAME tool imports framesdkpy directly, the package root should expose
only the stable core API.
"""


def test_package_root_exports_core_api():
    """The top-level framesdkpy package exposes the stable SDK surface."""
    import framesdkpy

    expected_names = {
        "FRAME",
        "FrameFacts",
        "FrameRules",
        "FrameMap",
        "FrameExpect",
        "FrameActs",
        "load_frame",
        "FrameLoadError",
        "validate_frame",
        "validate_file",
        "ValidationResult",
        "translate_file",
        "translate_directory",
        "translate_to_dict",
        "translate_to_json_string",
    }

    for name in expected_names:
        assert hasattr(framesdkpy, name), f"missing public export: {name}"
        assert name in framesdkpy.__all__, f"missing __all__ entry: {name}"


def test_readme_uses_current_import_name():
    """README examples should not point users at the old frame package name."""
    from pathlib import Path

    readme = Path("README.md").read_text()

    assert "from framesdkpy import load_frame" in readme
    assert "from framesdkpy import load_frame, translate_directory, validate_file" in readme
    assert "from frame import" not in readme
