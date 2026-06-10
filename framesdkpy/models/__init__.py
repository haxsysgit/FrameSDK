"""FRAME models — typed data carriers for all five FRAME parts.

Primary import for downstream tools:
    from framesdkpy.models import FRAME, FrameFacts, FrameRules, FrameMap, FrameExpect, FrameActs

Sub-models for deeper access:
    from framesdkpy.models import Profile, Command, Check, Run, Blocker, etc.
"""

from framesdkpy.models.frame_model import FRAME

from framesdkpy.models.facts_model import (
    FrameFacts,
    Profile,
    Architecture,
    Technology,
    Source,
    Quirk,
    OpenQuestion,
)

from framesdkpy.models.rules_model import (
    FrameRules,
    Policy,
    CoreRule,
    Command,
    Dont,
    AskFirst,
    Hint,
)

from framesdkpy.models.map_model import (
    FrameMap,
    Group,
    PathEntry,
    Entrypoint,
    ManagedPath,
    UnmappedPath,
)

from framesdkpy.models.expect_model import (
    FrameExpect,
    MustHold,
    Check,
    Proof,
)

from framesdkpy.models.acts_model import (
    FrameActs,
    Run,
    RunCheck,
    Blocker,
)

from framesdkpy.models.base import FrameBaseModel

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
