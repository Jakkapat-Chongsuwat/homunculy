"""
Dual-System Adapters - Human-like cognitive architecture.

Provides:
- ReflexAdapter: Fast <300ms responses using lightweight LLM
- CognitionAdapter: Deep reasoning using LangGraph
- DualSystemOrchestrator: Coordinates reflex + cognition
"""

from infrastructure.adapters.dual_system.cognition import CognitionAdapter
from infrastructure.adapters.dual_system.emotion import EmotionDetector
from infrastructure.adapters.dual_system.orchestrator import DualSystemOrchestrator
from infrastructure.adapters.dual_system.reflex import ReflexAdapter

__all__ = [
    "CognitionAdapter",
    "DualSystemOrchestrator",
    "EmotionDetector",
    "ReflexAdapter",
]
