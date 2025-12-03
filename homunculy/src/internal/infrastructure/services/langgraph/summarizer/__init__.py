"""
Summarizer module for LangGraph conversation management.

Provides background conversation summarization utilities.
"""

from internal.infrastructure.services.langgraph.summarizer.background import (
    BackgroundSummarizer,
    create_background_summarizer,
)


__all__ = [
    "BackgroundSummarizer",
    "create_background_summarizer",
]
