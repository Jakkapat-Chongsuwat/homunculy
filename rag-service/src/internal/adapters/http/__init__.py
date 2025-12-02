"""
HTTP Adapters Layer.

REST API endpoints for RAG operations.
"""

from .ingest_router import router as ingest_router
from .query_router import router as query_router

__all__ = [
    "ingest_router",
    "query_router",
]
