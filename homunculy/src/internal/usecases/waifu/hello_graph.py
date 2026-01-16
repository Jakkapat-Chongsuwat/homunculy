from __future__ import annotations

from typing import TypedDict

from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph import END, START, StateGraph


class HelloGraphState(TypedDict):
    messages: list[BaseMessage]


def _hello(state: HelloGraphState) -> HelloGraphState:
    return {"messages": [*state.get("messages", []), AIMessage(content="Hello world")]}


def create_hello_world_graph():
    graph = StateGraph(HelloGraphState)
    graph.add_node("hello", _hello)
    graph.add_edge(START, "hello")
    graph.add_edge("hello", END)
    return graph.compile()
