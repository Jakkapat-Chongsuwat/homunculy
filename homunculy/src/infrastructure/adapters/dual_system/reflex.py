"""
Reflex Adapter - Fast response layer (<300ms).

Uses lightweight processing for quick social responses:
- Pattern matching for greetings
- Simple intent classification
- Filler responses during cognition
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from domain.interfaces.dual_system import (
    DualSystemInput,
    ReflexOutput,
    ReflexPort,
)

if TYPE_CHECKING:
    from domain.interfaces import LLMPort


# Patterns for fast matching (no LLM needed)
_GREETING_PATTERNS = [
    r"\b(hi|hello|hey|good\s*(morning|afternoon|evening))\b",
    r"\bhow\s+are\s+you\b",
    r"\bwhat'?s\s+up\b",
]

_ACKNOWLEDGMENT_PATTERNS = [
    r"^(ok|okay|sure|yes|no|yep|nope|got\s*it|i\s*see)$",
    r"^(thanks|thank\s*you|thx)$",
]

_SIMPLE_QUESTIONS = {
    r"what\s+time\s+is\s+it": "time_query",
    r"what'?s\s+the\s+time": "time_query",
    r"what\s+day\s+is\s+it": "date_query",
}


class ReflexAdapter(ReflexPort):
    """Fast response adapter - targets <300ms."""

    def __init__(self, llm: "LLMPort | None" = None) -> None:
        """Initialize with optional lightweight LLM for edge cases."""
        self._llm = llm
        self._greeting_re = _compile_patterns(_GREETING_PATTERNS)
        self._ack_re = _compile_patterns(_ACKNOWLEDGMENT_PATTERNS)

    async def respond(self, input_: DualSystemInput) -> ReflexOutput:
        """Generate fast response."""
        text = input_.text.lower().strip()

        # 1. Check greetings
        if self._greeting_re.search(text):
            return _greeting_response(input_)

        # 2. Check acknowledgments
        if self._ack_re.match(text):
            return ReflexOutput(text="", is_filler=True)

        # 3. Check simple questions
        for pattern, query_type in _SIMPLE_QUESTIONS.items():
            if re.search(pattern, text):
                return _simple_query_response(query_type)

        # 4. Fallback: generate filler while cognition works
        return ReflexOutput(
            text="Let me think about that...",
            is_filler=True,
            confidence=0.5,
        )

    def can_handle(self, input_: DualSystemInput) -> bool:
        """Check if reflex can fully handle this input."""
        text = input_.text.lower().strip()
        if self._greeting_re.search(text):
            return True
        if self._ack_re.match(text):
            return True
        return any(re.search(p, text) for p in _SIMPLE_QUESTIONS)


def _compile_patterns(patterns: list[str]) -> re.Pattern:
    """Compile patterns into single regex."""
    return re.compile("|".join(patterns), re.IGNORECASE)


def _greeting_response(input_: DualSystemInput) -> ReflexOutput:
    """Generate greeting response."""
    user_name = input_.context.get("user_name", "")
    greeting = f"Hi{', ' + user_name if user_name else ''}! How can I help you?"
    return ReflexOutput(text=greeting, confidence=1.0)


def _simple_query_response(query_type: str) -> ReflexOutput:
    """Handle simple queries without LLM."""
    import datetime

    now = datetime.datetime.now()
    if query_type == "time_query":
        return ReflexOutput(text=f"It's {now.strftime('%I:%M %p')}.")
    if query_type == "date_query":
        return ReflexOutput(text=f"Today is {now.strftime('%A, %B %d')}.")
    return ReflexOutput(text="I'm not sure.", confidence=0.3)
