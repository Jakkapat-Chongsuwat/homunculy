"""Memory tools for LangGraph agent.

Provides search_memory and save_memory tools using InjectedStore.
Cognition (System 2) decides when to call these tools.
"""

import uuid
from typing import Annotated

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedStore
from langgraph.store.base import BaseStore

from common.logger import get_logger

logger = get_logger(__name__)


@tool
def search_memory(
    query: str,
    *,
    config: RunnableConfig,
    store: Annotated[BaseStore, InjectedStore()],
) -> str:
    """Search long-term memory for relevant user information."""
    namespace = _user_namespace(config)
    items = store.search(namespace, query=query, limit=5)
    return _format_results(items)


@tool
def save_memory(
    content: str,
    *,
    config: RunnableConfig,
    store: Annotated[BaseStore, InjectedStore()],
) -> str:
    """Save important information to long-term memory."""
    namespace = _user_namespace(config)
    key = str(uuid.uuid4())
    store.put(namespace, key, {"data": content})
    logger.debug("Saved memory", namespace=namespace, key=key)
    return f"Saved: {content}"


def _user_namespace(config: RunnableConfig) -> tuple[str, ...]:
    """Extract user namespace from config."""
    user_id = config.get("configurable", {}).get("user_id", "default")
    return ("memories", user_id)


def _format_results(items: list) -> str:
    """Format store items as readable text."""
    if not items:
        return "No relevant memories found."
    entries = [_extract_data(item) for item in items]
    return "\n".join(entries)


def _extract_data(item) -> str:
    """Extract data string from store item."""
    return item.value.get("data", "")
