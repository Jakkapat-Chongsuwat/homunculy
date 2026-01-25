"""
Emotion Detector - Detect emotional state from input.

Uses text analysis and optional audio features.
"""

from __future__ import annotations

import re

from domain.interfaces.dual_system import (
    DualSystemInput,
    EmotionalTone,
    EmotionDetectorPort,
)

# Simple keyword-based detection (can be replaced with ML model)
_EMOTION_PATTERNS = {
    EmotionalTone.FRUSTRATED: [
        r"\b(frustrated|annoying|annoyed|angry|mad|hate)\b",
        r"\b(doesn'?t\s+work|broken|stupid)\b",
        r"!{2,}",  # Multiple exclamation marks
    ],
    EmotionalTone.URGENT: [
        r"\b(urgent|asap|emergency|quickly|hurry)\b",
        r"\b(deadline|now|immediately)\b",
    ],
    EmotionalTone.CONFUSED: [
        r"\b(confused|don'?t\s+understand|what\s+do\s+you\s+mean)\b",
        r"\b(huh|what\?|i\s+don'?t\s+get\s+it)\b",
        r"\?{2,}",  # Multiple question marks
    ],
    EmotionalTone.HAPPY: [
        r"\b(thanks|thank\s+you|awesome|great|love\s+it)\b",
        r"\b(happy|excited|wonderful|amazing)\b",
        r"!+\s*$",  # Ends with exclamation
    ],
}


class EmotionDetector(EmotionDetectorPort):
    """Detect emotion from text and audio features."""

    def __init__(self) -> None:
        """Compile emotion patterns."""
        self._patterns = {
            tone: [re.compile(p, re.IGNORECASE) for p in patterns]
            for tone, patterns in _EMOTION_PATTERNS.items()
        }

    async def detect(self, input_: DualSystemInput) -> EmotionalTone:
        """Detect emotion from text and audio features."""
        text = input_.text

        # Check each emotion pattern
        for tone, patterns in self._patterns.items():
            if any(p.search(text) for p in patterns):
                return tone

        # Check audio features if available
        if input_.audio_features:
            return _detect_from_audio(input_.audio_features)

        return EmotionalTone.NEUTRAL


def _detect_from_audio(features: dict[str, float]) -> EmotionalTone:
    """Detect emotion from audio features (pitch, energy, etc.)."""
    energy = features.get("energy", 0.5)
    pitch_variance = features.get("pitch_variance", 0.5)

    if energy > 0.8 and pitch_variance > 0.7:
        return EmotionalTone.FRUSTRATED
    if energy > 0.7:
        return EmotionalTone.URGENT
    if energy < 0.3:
        return EmotionalTone.CONFUSED

    return EmotionalTone.NEUTRAL
