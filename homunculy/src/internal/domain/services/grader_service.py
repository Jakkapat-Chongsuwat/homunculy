"""Grader Service Interfaces."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class DocumentGraderService(ABC):
    """Abstract interface for document relevance grading."""

    @abstractmethod
    async def grade(self, question: str, document: str) -> bool:
        """Grade single document relevance."""

    @abstractmethod
    async def grade_batch(
        self, question: str, documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Filter documents by relevance."""


class HallucinationGraderService(ABC):
    """Abstract interface for hallucination detection."""

    @abstractmethod
    async def check(self, documents: List[Dict[str, Any]], generation: str) -> bool:
        """Check if generation is grounded in documents."""


class AnswerGraderService(ABC):
    """Abstract interface for answer usefulness grading."""

    @abstractmethod
    async def grade(self, question: str, generation: str) -> bool:
        """Grade if answer addresses question."""


class QueryRewriterService(ABC):
    """Abstract interface for query rewriting."""

    @abstractmethod
    async def rewrite(self, question: str) -> str:
        """Rewrite question for better retrieval."""
