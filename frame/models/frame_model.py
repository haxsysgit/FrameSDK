"""FRAME — the assembled whole.

Composes all five typed parts into one model. All 5 files must be present
in the .haxaml/ directory at all times (D3: strict single-directory discovery).
Empty files are valid — content depth is Haxaml's concern, not the SDK's.
"""

from __future__ import annotations

from dataclasses import dataclass

from frame.models.base import FrameBaseModel
from frame.models.facts_model import FrameFacts
from frame.models.rules_model import FrameRules
from frame.models.map_model import FrameMap
from frame.models.expect_model import FrameExpect
from frame.models.acts_model import FrameActs


@dataclass(slots=True)
class FRAME(FrameBaseModel):
    """The assembled FRAME object — all five parts in one typed model.

    All 5 files are required by the loader (D3). Content depth varies —
    a new project has empty Expect and Acts. A mature project fills them.
    The SDK validates structure and schema. Haxaml enforces content.
    """

    facts: FrameFacts
    """Required. Stable project truth — identity, stack, architecture, quirks."""

    rules: FrameRules
    """Required. Governance constraints, commands, policies."""

    map: FrameMap
    """Required. Where things live — at minimum structure + roots."""

    expect: FrameExpect
    """Required. What must pass — may be empty in early projects."""

    acts: FrameActs
    """Required. Run history — starts empty, grows over time."""
