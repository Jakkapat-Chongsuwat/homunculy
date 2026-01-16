"""Grader service contracts."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class DocumentGraderService(ABC):
    """Document relevance grading."""

    @abstractmethod
    async def grade(self, question: str, document: str) -> bool:
        """Grade one document."""

    @abstractmethod
    async def grade_batch(
        self, question: str, documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter documents by relevance."""


class HallucinationGraderService(ABC):
    """Hallucination detection."""

    @abstractmethod
    async def check(self, documents: List[Dict[str, Any]], generation: str) -> bool:
        """Check grounding."""


class AnswerGraderService(ABC):
    """Answer usefulness grading."""

    @abstractmethod
    async def grade(self, question: str, generation: str) -> bool:
        """Grade answer usefulness."""


class QueryRewriterService(ABC):
    """Query rewriting."""

    @abstractmethod
    async def rewrite(self, question: str) -> str:
        """Rewrite question."""
