"""Assembler — builds a typed FRAME object from 5 validated and normalized dicts.

Runs cross-file consistency checks, then constructs the five typed models
and composes them into one FRAME object.
"""

from __future__ import annotations

from framesdkpy.models.frame_model import FRAME
from framesdkpy.models.facts_model import FrameFacts, Profile, Architecture, Technology, Source, Quirk, OpenQuestion
from framesdkpy.models.rules_model import FrameRules, Policy, CoreRule, Command, Dont, AskFirst, Hint
from framesdkpy.models.map_model import FrameMap, Group, PathEntry, Entrypoint, ManagedPath, UnmappedPath
from framesdkpy.models.expect_model import FrameExpect, MustHold, Check, Proof
from framesdkpy.models.acts_model import FrameActs, Run, RunCheck, Blocker

from framesdkpy.validators.cross_file_validator import validate_cross_file


class FrameLoadError(ValueError):
    """Raised when a validated FRAME directory cannot be assembled.

    Contains the validation result with all errors that prevented assembly.
    """

    def __init__(self, message: str, errors: list, warnings: list):
        self.errors = errors
        self.warnings = warnings
        super().__init__(message)


# ---------------------------------------------------------------------------
# Sub-model constructors — each converts a normalized dict to a typed model
# ---------------------------------------------------------------------------


from dataclasses import fields as dc_fields

def _strip_extra(data: dict, model_class) -> dict:
    """Keep only keys that match the model's field names."""
    field_names = {f.name for f in dc_fields(model_class)}
    return {k: v for k, v in data.items() if k in field_names}


def _build_facts(data: dict) -> FrameFacts:
    prof = data.get("profile", {})
    arch = data.get("architecture", {})
    tech = data.get("technology")

    return FrameFacts(
        profile=Profile(
            name=prof["name"],
            summary=prof["summary"],
            repo_shape=prof.get("repo_shape"),
            delivery_family=prof.get("delivery_family"),
        ),
        architecture=Architecture(
            summary=arch["summary"],
            backend_layers=arch.get("backend_layers"),
            frontend_layers=arch.get("frontend_layers"),
            data_flow=arch.get("data_flow"),
            deployment_topology=arch.get("deployment_topology"),
        ),
        technology=Technology(
            language=tech.get("language") if tech else None,
            framework=tech.get("framework") if tech else None,
            database=tech.get("database") if tech else None,
            extensions=tech.get("extensions") if tech else None,
        ) if tech else None,
        sources=[Source(**_strip_extra(s, Source)) for s in data.get("sources", [])],
        quirks=[Quirk(**_strip_extra(q, Quirk)) for q in data.get("quirks", [])],
        open_questions=[OpenQuestion(**_strip_extra(o, OpenQuestion)) for o in data.get("open_questions", [])],
        classification=data.get("classification"),
        environments=data.get("environments"),
        persistence=data.get("persistence"),
    )


def _build_rules(data: dict) -> FrameRules:
    commands_dict: dict[str, Command] = {}

    for name, cmd_data in data.get("commands", {}).items():
        commands_dict[name] = Command(**_strip_extra(cmd_data, Command))

    return FrameRules(
        governance_level=data.get("governance_level", "normal"),
        rules=[CoreRule(**_strip_extra(r, CoreRule)) for r in data.get("rules", [])],
        policies=[Policy(**_strip_extra(p, Policy)) for p in data.get("policies", [])],
        commands=commands_dict,
        donts=[Dont(**_strip_extra(d, Dont)) for d in data.get("donts", [])],
        ask_first=[AskFirst(**_strip_extra(a, AskFirst)) for a in data.get("ask_first", [])],
        hints=[Hint(**_strip_extra(h, Hint)) for h in data.get("hints", [])],
        code_style=data.get("code_style"),
        git=data.get("git"),
    )


def _build_map(data: dict) -> FrameMap:
    """Build FrameMap from a normalized map dict."""
    return FrameMap(
        structure=data.get("structure"),
        roots=data.get("roots"),
        groups=[Group(**_strip_extra(g, Group)) for g in data.get("groups", [])],
        paths=[PathEntry(**_strip_extra(p, PathEntry)) for p in data.get("paths", [])],
        entrypoints=[Entrypoint(**_strip_extra(e, Entrypoint)) for e in data.get("entrypoints", [])],
        managed_paths=[ManagedPath(**_strip_extra(m, ManagedPath)) for m in data.get("managed_paths", [])],
        unmapped_paths=[UnmappedPath(**_strip_extra(u, UnmappedPath)) for u in data.get("unmapped_paths", [])],
    )


def _build_expect(data: dict) -> FrameExpect:
    """Build FrameExpect from a normalized expect dict."""
    checks_dict: dict[str, Check] = {}
    for name, chk_data in data.get("checks", {}).items():
        checks_dict[name] = Check(**_strip_extra(chk_data, Check))

    return FrameExpect(
        outcomes=data.get("outcomes"),
        must_hold=[MustHold(**_strip_extra(m, MustHold)) for m in data.get("must_hold", [])],
        checks=checks_dict,
        done_when=data.get("done_when"),
        proof=[Proof(**_strip_extra(p, Proof)) for p in data.get("proof", [])],
        handoff=data.get("handoff"),
    )


def _build_acts(data: dict) -> FrameActs:
    """Build FrameActs from a normalized acts dict."""
    runs: list[Run] = []
    for run_data in data.get("runs", []):
        # Build nested RunCheck objects
        checks_list: list[RunCheck] = []
        for rc_data in run_data.get("checks", []) or []:
            checks_list.append(RunCheck(**_strip_extra(rc_data, RunCheck)))

        run_data_copy = {k: v for k, v in run_data.items() if k != "checks"}
        runs.append(Run(checks=checks_list if checks_list else None, **_strip_extra(run_data_copy, Run)))

    return FrameActs(
        summary=data.get("summary"),
        runs=runs,
        blockers=[Blocker(**_strip_extra(b, Blocker)) for b in data.get("blockers", [])],
        handoff=data.get("handoff"),
    )


# ---------------------------------------------------------------------------
# Main assembly function
# ---------------------------------------------------------------------------


_BUILDERS = {
    "facts": _build_facts,
    "rules": _build_rules,
    "map": _build_map,
    "expect": _build_expect,
    "acts": _build_acts,
}


def assemble_frame(parts: dict[str, dict]) -> FRAME:
    """Build a typed FRAME object from 5 validated and normalized dicts.

    Runs cross-file consistency check first. Raises FrameLoadError if
    schema versions don't match or file/role fields are inconsistent.

    Args:
        parts: Dict mapping file stem to normalized dict.
               e.g., {"facts": {...}, "rules": {...}, ...}

    Returns:
        FRAME object with all five typed parts.
    """
    # Cross-file consistency must pass before assembly
    cross_result = validate_cross_file(parts)
    if not cross_result.is_valid():
        raise FrameLoadError(
            f"Cross-file validation failed: {cross_result.summary()}",
            errors=cross_result.errors,
            warnings=cross_result.warnings,
        )

    built = {}
    for stem in ["facts", "rules", "map", "expect", "acts"]:
        if stem in parts:
            builder = _BUILDERS[stem]
            built[stem] = builder(parts[stem])
        else:
            built[stem] = None

    return FRAME(
        facts=built["facts"],
        rules=built["rules"],
        map=built["map"],
        expect=built["expect"],
        acts=built["acts"],
    )
