"""Agent HTTP handler."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from application.use_cases import ChatUseCase
from application.use_cases.chat import ChatInput
from common.logger import get_logger
from domain.entities import AgentConfiguration, AgentPersonality, AgentProvider
from domain.interfaces import LLMPort

logger = get_logger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request DTO."""

    message: str
    thread_id: str | None = None
    model: str = "gpt-4o-mini"
    temperature: float = 0.7


class ChatResponse(BaseModel):
    """Chat response DTO."""

    message: str
    thread_id: str
    confidence: float


# Dependency injection placeholder
_llm_service: LLMPort | None = None


def set_llm_service(service: LLMPort) -> None:
    """Set LLM service for dependency injection."""
    global _llm_service
    _llm_service = service


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Handle chat request."""
    if not _llm_service:
        raise HTTPException(status_code=503, detail="LLM service not available")

    use_case = ChatUseCase(_llm_service)
    input_ = _build_input(request)
    output = await use_case.execute(input_)
    return _build_response(output)


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    """Handle streaming chat request."""
    if not _llm_service:
        raise HTTPException(status_code=503, detail="LLM service not available")

    service = _llm_service  # Capture for closure
    config = _build_config(request)
    context = {"thread_id": request.thread_id or "default"}

    async def generate():
        async for chunk in service.stream_chat(config, request.message, context):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain")


def _build_input(request: ChatRequest) -> ChatInput:
    """Build ChatInput from request."""
    return ChatInput(
        message=request.message,
        config=_build_config(request),
        thread_id=request.thread_id or "default",
    )


def _build_config(request: ChatRequest) -> AgentConfiguration:
    """Build AgentConfiguration from request."""
    return AgentConfiguration(
        provider=AgentProvider.LANGRAPH,
        model_name=request.model,
        personality=_default_personality(),
        temperature=request.temperature,
    )


def _default_personality() -> AgentPersonality:
    """Create default personality."""
    return AgentPersonality(name="Assistant", description="Helpful assistant")


def _build_response(output) -> ChatResponse:
    """Build ChatResponse from output."""
    return ChatResponse(
        message=output.response.message,
        thread_id=output.thread_id,
        confidence=output.response.confidence,
    )
