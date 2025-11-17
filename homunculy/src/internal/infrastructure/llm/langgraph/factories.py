"""Reusable LangGraph helpers for building conversation flows."""

from typing import Annotated, Any, Dict, List, Optional

from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic_ai import Agent as PydanticAgent, ModelSettings
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from typing_extensions import TypedDict

from internal.domain.entities import AgentConfiguration


class ConversationState(TypedDict):
    """Structured LangGraph state shared across services."""

    messages: Annotated[list, add_messages]
    system_prompt: str
    response: Optional[str]
    error: Optional[str]
    summary: Optional[str]


def _build_personality_context(configuration: AgentConfiguration) -> str:
    personality = configuration.personality
    return (
        f"You are {personality.name}. {personality.description}. "
        f"Your current mood is {personality.mood}."
    )


def _build_user_instruction(messages: List[Dict[str, Any]], summary: Optional[str]) -> str:
    if not messages:
        return ""

    latest = messages[-1]
    latest_text = latest.get("content", str(latest)) if isinstance(latest, dict) else str(latest)

    history_block = "\n".join(
        f"{msg.get('role', 'user').title()}: {msg.get('content', str(msg))}"
        for msg in messages[:-1]
        if isinstance(msg, dict)
    )

    prompt_sections: List[str] = []
    if summary:
        prompt_sections.append(f"Conversation summary so far:\n{summary}")
    if history_block:
        prompt_sections.append(f"Recent exchanges:\n{history_block}")
    prompt_sections.append(f"Latest user message:\n{latest_text}")

    return "\n\n".join(prompt_sections)


def create_primary_agent(api_key: str, configuration: AgentConfiguration) -> PydanticAgent:
    """Create the main conversational agent with personality context applied."""

    provider = OpenAIProvider(api_key=api_key)
    model = OpenAIChatModel(configuration.model_name, provider=provider)
    base_prompt = (configuration.system_prompt or "").strip()
    personality_context = _build_personality_context(configuration)
    full_system_prompt = f"{base_prompt}\n\n{personality_context}".strip()

    return PydanticAgent(
        model,
        system_prompt=full_system_prompt,
        model_settings=ModelSettings(
            temperature=configuration.temperature,
            max_tokens=configuration.max_tokens,
        ),
    )


def create_summarizer_agent(api_key: str, configuration: AgentConfiguration) -> PydanticAgent:
    """Create a low-temperature summarizer agent sharing the same provider."""

    provider = OpenAIProvider(api_key=api_key)
    model = OpenAIChatModel(configuration.model_name, provider=provider)
    return PydanticAgent(
        model,
        system_prompt=(
            "You are a diligent meeting notes assistant. "
            "Summaries must capture objectives, decisions, facts, and emotions."
        ),
        model_settings=ModelSettings(temperature=0.2, max_tokens=400),
    )


def create_llm_node(agent: PydanticAgent):
    """Wrap the agent inside a LangGraph node for reuse across services."""

    async def call_llm(state: ConversationState) -> Dict[str, Any]:
        if not state.get("messages"):
            return {"error": "No messages in conversation", "response": None}

        try:
            user_instruction = _build_user_instruction(state["messages"], state.get("summary"))
            result = await agent.run(user_instruction)
            response_text = result.output
            return {
                "response": response_text,
                "messages": [{"role": "assistant", "content": response_text}],
                "error": None,
            }
        except Exception as exc:  # pragma: no cover - surfaced upstream
            return {"error": str(exc), "response": None}

    return call_llm


def build_conversation_graph(agent: PydanticAgent):
    """Compile the minimal conversation graph for chat orchestration."""

    graph_builder = StateGraph(ConversationState)
    graph_builder.add_node("llm", create_llm_node(agent))
    graph_builder.add_edge(START, "llm")
    graph_builder.add_edge("llm", END)
    return graph_builder.compile()
