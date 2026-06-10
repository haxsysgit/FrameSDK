"""FRAME models — typed data carriers for all five FRAME parts.

Primary import for downstream tools:
    from frame.models import FRAME, FrameFacts, FrameRules, FrameMap, FrameExpect, FrameActs

Sub-models for deeper access:
    from frame.models import Profile, Command, Check, Run, Blocker, etc.
"""

from frame.models.frame_model import FRAME

from frame.models.facts_model import (
    FrameFacts,
    Profile,
    Architecture,
    Technology,
    Source,
    Quirk,
    OpenQuestion,
)

from frame.models.rules_model import (
    FrameRules,
    Policy,
    CoreRule,
    Command,
    Dont,
    AskFirst,
    Hint,
)

from frame.models.map_model import (
    FrameMap,
    Group,
    PathEntry,
    Entrypoint,
    ManagedPath,
    UnmappedPath,
)

from frame.models.expect_model import (
    FrameExpect,
    MustHold,
    Check,
    Proof,
)

from frame.models.acts_model import (
    FrameActs,
    Run,
    RunCheck,
    Blocker,
)

from frame.models.base import FrameBaseModel

# Everything a downstream tool needs, one import away
__all__ = [
    # Top-level
    "FRAME",
    "FrameBaseModel",
    # Facts
    "FrameFacts",
    "Profile",
    "Architecture",
    "Technology",
    "Source",
    "Quirk",
    "OpenQuestion",
    # Rules
    "FrameRules",
    "Policy",
    "CoreRule",
    "Command",
    "Dont",
    "AskFirst",
    "Hint",
    # Map
    "FrameMap",
    "Group",
    "PathEntry",
    "Entrypoint",
    "ManagedPath",
    "UnmappedPath",
    # Expect
    "FrameExpect",
    "MustHold",
    "Check",
    "Proof",
    # Acts
    "FrameActs",
    "Run",
    "RunCheck",
    "Blocker",
]
