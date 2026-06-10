"""FrameMap model and sub-models — where things live in the repo.

Mirrors schemas/json/map.schema.json exactly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from framesdkpy.models.base import FrameBaseModel


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class Group(FrameBaseModel):
    """Logical grouping of paths. Supports wildcards for flexible coverage.

    Groups let the map cover growing repos without requiring every new file
    to be individually registered.
    """

    id: str
    """Stable identifier for cross-referencing. maxLength: 100."""

    label: str
    """Human-readable group name. maxLength: 150."""

    paths: list[str] = field(default_factory=list)
    """File/directory paths in this group. Wildcards allowed (e.g. 'Backend/app/**/*.py')."""

    links: list[dict] = field(default_factory=list)
    """Typed links from this entry to other FRAME refs."""


@dataclass(slots=True)
class PathEntry(FrameBaseModel):
    """Critical individual file. Explicit path only — no wildcards.

    Optional id for cross-referencing from expect.checks or acts.runs.touched.
    """

    path: str
    """Filesystem path. maxLength: 200."""

    purpose: str
    """Why this file is important. maxLength: 300."""

    id: str | None = None
    """Optional stable identifier. Only needed when this path is referenced from another file."""

    links: list[dict] = field(default_factory=list)
    """Typed links from this entry to other FRAME refs."""


@dataclass(slots=True)
class Entrypoint(FrameBaseModel):
    """CLI, API, web, or script entry point. Always has an id for cross-referencing."""

    id: str
    """Stable identifier. maxLength: 100."""

    path: str
    """Filesystem path to the entry point. maxLength: 200."""

    kind: str
    """Fixed enum: cli, api, web, script."""

    description: str | None = None
    """What this entry point does. maxLength: 300."""

    links: list[dict] = field(default_factory=list)
    """Typed links from this entry to other FRAME refs."""


@dataclass(slots=True)
class ManagedPath(FrameBaseModel):
    """Path under special rule. Supports wildcards.

    rule: generated (auto-generated files), config (.env, settings files),
    immutable (migration files, lock files).
    """

    path: str
    """Filesystem path or wildcard pattern. maxLength: 200."""

    rule: str
    """Fixed enum: generated, config, immutable."""

    id: str | None = None
    """Optional stable identifier for cross-referencing from rules.donts or expect.checks."""

    links: list[dict] = field(default_factory=list)
    """Typed links from this entry to other FRAME refs."""


@dataclass(slots=True)
class UnmappedPath(FrameBaseModel):
    """Path not yet placed in the map. Honest about gaps — invites improvement."""

    path: str
    """Filesystem path that needs mapping. maxLength: 200."""

    reason: str
    """Why this path hasn't been mapped yet. maxLength: 200."""


# ---------------------------------------------------------------------------
# Main model
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class FrameMap(FrameBaseModel):
    """Where things live in the repo. Populated from map.yaml.

    structure provides a quick visual overview (top block).
    roots describe top-level directories.
    groups provide logical groupings with wildcard support.
    paths list critical individual files.
    entrypoints show CLI/API/web start points.
    managed_paths declare files under special rules.
    unmapped_paths acknowledge gaps.
    """

    frame: dict = field(default_factory=dict)
    """Shared FRAME header block. Required by every FRAME file."""

    structure: str | None = None
    """Quick visual overview of repo layout. Top block, maxLength: 800."""

    roots: dict | None = None
    """Top-level directory purposes. Free-form keys."""

    groups: list[Group] = field(default_factory=list)
    """Logical groupings of paths. Supports wildcards."""

    paths: list[PathEntry] = field(default_factory=list)
    """Critical individual files. Explicit paths only."""

    entrypoints: list[Entrypoint] = field(default_factory=list)
    """CLI/API/web entry points. Each has a stable id."""

    managed_paths: list[ManagedPath] = field(default_factory=list)
    """Paths under special rules. Supports wildcards."""

    unmapped_paths: list[UnmappedPath] = field(default_factory=list)
    """Paths not yet mapped. Honest about gaps."""

    evidence: list[dict] = field(default_factory=list)
    """Evidence entries supporting Map claims."""

    links: list[dict] = field(default_factory=list)
    """Typed links from this file to other FRAME refs."""
