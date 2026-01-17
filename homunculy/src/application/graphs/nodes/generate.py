"""Generate node - Generate response using LLM."""

from common.logger import get_logger
from domain.entities import AgentConfiguration

from application.graphs.state import GraphState, with_generation

logger = get_logger(__name__)


async def generate_node(
    state: GraphState,
    llm_fn,
    config: AgentConfiguration,
) -> GraphState:
    """Generate response using retrieved documents."""
    question = state.get("question", "")
    docs = state.get("documents", [])

    context = _build_context(docs)
    prompt = _build_prompt(question, context)
    response = await _invoke_llm(llm_fn, prompt, config)

    return with_generation(state, response)


def _build_context(docs: list[dict]) -> str:
    """Build context string from documents."""
    chunks = [_extract_content(doc) for doc in docs]
    return "\n\n".join(chunks)


def _extract_content(doc: dict) -> str:
    """Extract content from document."""
    return doc.get("content", doc.get("text", ""))


def _build_prompt(question: str, context: str) -> str:
    """Build generation prompt."""
    return f"Context:\n{context}\n\nQuestion: {question}"


async def _invoke_llm(llm_fn, prompt: str, config: AgentConfiguration) -> str:
    """Invoke LLM and return response."""
    logger.debug("Generating response", prompt_len=len(prompt))
    result = await llm_fn(prompt, config)
    return result.message if hasattr(result, "message") else str(result)
