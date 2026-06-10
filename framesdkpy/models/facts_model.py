"""FrameFacts model and sub-models — stable project truth.

Mirrors schemas/json/facts.schema.json exactly. Required fields are
non-nullable (str, not str | None). The loader guarantees these are
populated before model construction. Optional fields use | None.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from framesdkpy.models.base import FrameBaseModel


# ---------------------------------------------------------------------------
# Sub-models — typed representations of Facts blocks
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class Profile(FrameBaseModel):
    """Project identity. name and summary are always present."""

    name: str
    """Project name. maxLength: 100."""

    summary: str
    """One-paragraph project description. maxLength: 300."""

    repo_shape: str | None = None
    """Enum: split-backend-frontend, monorepo, single-package, monolith, microservices."""

    delivery_family: str | None = None
    """Enum: cli, web-app, mobile-app, sdk, infra-tooling, data-pipeline, etc."""


@dataclass(slots=True)
class Architecture(FrameBaseModel):
    """System layout. summary is always present."""

    summary: str
    """Human-readable system layout overview. maxLength: 500."""

    backend_layers: list[str] | None = None
    """Ordered list of backend architectural layers, e.g. ['routes', 'services', 'models']."""

    frontend_layers: list[str] | None = None
    """Ordered list of frontend layers, e.g. ['views', 'stores', 'services']."""

    data_flow: str | None = None
    """Description of how data moves through the system. maxLength: 500."""

    deployment_topology: str | None = None
    """Where and how the system is deployed. maxLength: 500."""


@dataclass(slots=True)
class Technology(FrameBaseModel):
    """Structured technology stack. All fields optional."""

    language: str | None = None
    """Primary programming language."""

    framework: str | None = None
    """Primary framework (FastAPI, Next.js, etc.)."""

    database: str | None = None
    """Primary database (PostgreSQL, SQLite, etc.)."""

    extensions: dict | None = None
    """Optional free-form extensions for additional tech details."""


@dataclass(slots=True)
class Source(FrameBaseModel):
    """Trusted source-of-truth file. Has an id for cross-referencing."""

    id: str
    """Stable identifier — other files reference this via 'facts.sources.<id>'. maxLength: 100."""

    path: str
    """Filesystem path to the source file. maxLength: 200."""

    purpose: str
    """Why this file is a source of truth. maxLength: 300."""


@dataclass(slots=True)
class Quirk(FrameBaseModel):
    """Weird project-specific thing agents must understand. Has an id for cross-referencing."""

    id: str
    """Stable identifier. maxLength: 100."""

    description: str
    """What the quirk is. maxLength: 200."""

    why: str
    """Why this quirk exists — prevents agents from 'fixing' it. maxLength: 300."""


@dataclass(slots=True)
class OpenQuestion(FrameBaseModel):
    """Thing nobody has decided yet. Has an id for cross-referencing."""

    id: str
    """Stable identifier. maxLength: 100."""

    question: str
    """The unresolved question. maxLength: 300."""

    context: str
    """Background needed to understand the question. maxLength: 300."""


# ---------------------------------------------------------------------------
# Main model
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class FrameFacts(FrameBaseModel):
    """Stable project truth — what the project is, how it's built, its quirks.

    Populated by the loader from facts.yaml. Required fields are non-nullable.
    Optional blocks (environments, persistence, classification) use | None.
    """

    profile: Profile
    """Required. Every project has a name and summary."""

    architecture: Architecture
    """Required. Every project has a system layout."""

    sources: list[Source] = field(default_factory=list)
    """Trusted source-of-truth files. Each has a stable id for cross-referencing."""

    quirks: list[Quirk] = field(default_factory=list)
    """Project-specific oddities agents must understand. Each has a stable id."""

    open_questions: list[OpenQuestion] = field(default_factory=list)
    """Unresolved questions. Each has a stable id."""

    classification: dict | None = None
    """Project classification details. Free-form — varies per project."""

    technology: Technology | None = None
    """Structured technology stack. Optional at first."""

    environments: dict | None = None
    """Per-environment configuration. Free-form keys (local, production, staging)."""

    persistence: dict | None = None
    """Database, ORM, migration, and storage details. Free-form — varies by ORM/storage."""
