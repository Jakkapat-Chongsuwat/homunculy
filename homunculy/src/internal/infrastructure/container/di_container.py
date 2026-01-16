"""Dependency Injector container.

This is the composition root for infrastructure services.
It keeps framework/infrastructure wiring out of domain and usecases.
"""

from __future__ import annotations

import os
from typing import Optional

from dependency_injector import containers, providers
from settings import settings

from internal.domain.services import RAGService, TTSService
from internal.infrastructure.services.langgraph import LangGraphAgentService
from internal.infrastructure.services.rag import HTTPRAGService
from internal.infrastructure.services.tts import ElevenLabsTTSService


def _rag_url() -> str:
    return os.getenv("RAG_SERVICE_URL", "")


def _tts_key() -> str:
    return settings.tts.elevenlabs_api_key or os.getenv("ELEVENLABS_API_KEY", "")


def _maybe_rag_service() -> Optional[RAGService]:
    url = _rag_url()
    return HTTPRAGService(base_url=url) if url else None


def _maybe_tts_service() -> Optional[TTSService]:
    key = _tts_key()
    return ElevenLabsTTSService(api_key=key) if key else None


class Container(containers.DeclarativeContainer):
    """Application container for infra services."""

    rag_service = providers.Callable(_maybe_rag_service)
    tts_service = providers.Callable(_maybe_tts_service)

    llm_service = providers.Factory(
        LangGraphAgentService,
        tts_service=tts_service,
        rag_service=rag_service,
    )


_container: Container | None = None


def get_container() -> Container:
    global _container
    if _container is None:
        _container = Container()
    return _container
