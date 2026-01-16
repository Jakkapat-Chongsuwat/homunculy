"""Agent execution handler."""

from common.logger import get_logger
from fastapi import APIRouter, Depends, HTTPException, status

from internal.adapters.http.models import (
    AgentExecutionMetadata,
    AudioResponse,
    ChatResponse,
    ExecuteChatRequest,
)
from internal.domain.entities import AgentConfiguration, AgentPersonality, AgentProvider
from internal.domain.services import LLMService
from internal.infrastructure.container import get_llm_service

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

_METADATA_FIELDS = (
    "model_used",
    "tokens_used",
    "execution_time_ms",
    "tools_called",
    "checkpointer_state",
    "thread_id",
    "storage_type",
)
_AUDIO_FIELDS = ("data", "format", "encoding", "size_bytes", "voice_id", "duration_ms")


@router.post("/execute", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def execute_chat(
    request: ExecuteChatRequest, llm_service: LLMService = Depends(get_llm_service)
) -> ChatResponse:
    try:
        return await _execute_chat(request, llm_service)
    except Exception as exc:
        _log_execution_error(exc)
        raise _http_500(exc) from exc


async def _execute_chat(request: ExecuteChatRequest, llm_service: LLMService) -> ChatResponse:
    configuration = _build_configuration(request)
    context = _build_context(request)
    response = await llm_service.chat(configuration, request.message, context)
    return _build_chat_response(response)


def _build_configuration(request: ExecuteChatRequest) -> AgentConfiguration:
    data = request.configuration.model_dump()
    data["provider"] = _parse_provider(request)
    data["personality"] = _build_personality(request)
    return AgentConfiguration(**data)


def _build_personality(request: ExecuteChatRequest) -> AgentPersonality:
    data = request.configuration.personality.model_dump()
    return AgentPersonality(**data)


def _parse_provider(request: ExecuteChatRequest) -> AgentProvider:
    try:
        return AgentProvider(request.configuration.provider)
    except ValueError:
        return AgentProvider.LANGRAPH


def _build_context(request: ExecuteChatRequest) -> dict:
    context = request.context.copy()
    context["user_id"] = request.user_id
    context["include_audio"] = request.include_audio
    return context


def _build_chat_response(response) -> ChatResponse:
    metadata = _build_execution_metadata(response.metadata or {})
    audio = _build_audio_response(response.metadata or {})
    payload = _chat_response_payload(response, audio, metadata)
    return ChatResponse(**payload)


def _chat_response_payload(
    response, audio: AudioResponse, metadata: AgentExecutionMetadata
) -> dict:
    return dict(
        message=response.message,
        confidence=response.confidence,
        reasoning=response.reasoning or "",
        audio=audio,
        metadata=metadata,
    )


def _build_execution_metadata(metadata: dict) -> AgentExecutionMetadata:
    payload = _metadata_payload(metadata)
    return AgentExecutionMetadata(**payload)


def _metadata_payload(metadata: dict) -> dict:
    payload = {key: metadata.get(key) for key in _METADATA_FIELDS}
    payload["tools_called"] = metadata.get("tools_called") or []
    return payload


def _build_audio_response(metadata: dict) -> AudioResponse:
    audio = metadata.get("audio") or {}
    payload = _audio_payload(audio)
    return AudioResponse(**payload)


def _audio_payload(audio: dict) -> dict:
    payload = {key: audio.get(key) for key in _AUDIO_FIELDS}
    payload["generated"] = bool(audio.get("data"))
    return payload


def _log_execution_error(exc: Exception) -> None:
    logger.error("Agent execution failed", error=str(exc), exc_info=True)


def _http_500(exc: Exception) -> HTTPException:
    message = f"Chat execution failed: {str(exc)}"
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)
