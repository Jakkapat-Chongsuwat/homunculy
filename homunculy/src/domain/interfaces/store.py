"""Store Port - LangGraph cross-thread memory storage.

Re-exports LangGraph BaseStore as the domain contract.
Adapters extend BaseStore directly for InjectedStore compatibility.
"""

from langgraph.store.base import BaseStore, Item

StorePort = BaseStore
StoreItem = Item

__all__ = ["StoreItem", "StorePort"]
