"""
RAG pipeline settings.

Configuration for document chunking and retrieval.
"""

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class RAGSettings(BaseSettings):
    """
    RAG pipeline configuration settings.

    Environment Variables:
        RAG_CHUNK_SIZE: Target chunk size in tokens
        RAG_CHUNK_OVERLAP: Overlap between chunks in tokens
        RAG_TOP_K: Number of results to retrieve
        RAG_SIMILARITY_THRESHOLD: Minimum similarity score (0-1)
    """

    model_config = SettingsConfigDict(env_prefix="RAG_", extra="ignore")

    chunk_size: int = int(
        os.getenv(
            "RAG_CHUNK_SIZE",
            "512",
        )
    )
    chunk_overlap: int = int(
        os.getenv(
            "RAG_CHUNK_OVERLAP",
            "50",
        )
    )
    top_k: int = int(
        os.getenv(
            "RAG_TOP_K",
            "5",
        )
    )
    similarity_threshold: float = float(
        os.getenv(
            "RAG_SIMILARITY_THRESHOLD",
            "0.7",
        )
    )


rag_settings = RAGSettings()
