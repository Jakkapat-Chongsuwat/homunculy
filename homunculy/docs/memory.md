# LangGraph Long-Term Memory System

## Overview

Implements LangGraph Store pattern for cross-thread long-term memory storage following the architecture described in the [LangGraph memory documentation](https://langchain-ai.github.io/langgraph/how-tos/memory/).

## Architecture

### Components

```
domain/interfaces/
  ├── memory.py      # Legacy interface (semantic memory)
  └── store.py       # LangGraph Store interface

application/services/
  └── memory.py      # Memory service (get_memory/update_memory)

infrastructure/adapters/store/
  └── in_memory.py   # InMemoryStore implementation
```

### Memory Layers

**Thread-Level (Short-Term)**: Managed by checkpointer
- Current conversation context
- Message history within session
- Cleared when thread ends

**Cross-Thread (Long-Term)**: Managed by Store
- User preferences across sessions
- Learning from feedback
- Facts and knowledge accumulation

## Usage

### Basic Memory Operations

```python
from application.services import MemoryService
from infrastructure.adapters.store import SQLiteStoreAdapter

# Production: File-based SQLite
store = SQLiteStoreAdapter("data/memory.db")

# Testing: In-memory SQLite
# store = SQLiteStoreAdapter(":memory:")

memory = MemoryService(store)

# Namespace: (tenant_id, category, user_id)
namespace = ("companion", "user_123")

# Get memory with default initialization
prefs = await memory.get_memory(
    namespace,
    "preferences",
    default="User prefers concise responses.",
)

# Update memory
await memory.update_memory(
    namespace,
    "preferences",
    "User prefers detailed technical explanations.",
)

# Search memories
items = await memory.search_memories(namespace, limit=10)
```

### Namespace Organization

Namespaces organize memories hierarchically:

```python
# User preferences
("companion", "user_123", "preferences")

# Session context
("companion", "user_123", "session_456")

# Learning patterns
("companion", "learning", "communication_style")
```

### Integration with LangGraph

The store is automatically wired into graph compilation:

```python
# In infrastructure/adapters/langgraph/graph_manager.py
graph = StateGraph(GraphState)
# ... add nodes ...
compiled = graph.compile(
    checkpointer=checkpointer,
    store=store,  # Cross-thread memory
)
```

### Memory in Graph Nodes

Access memory within LangGraph nodes:

```python
from langgraph.store.base import BaseStore

async def agent_node(state: GraphState, store: BaseStore) -> dict:
    """Node with memory access."""
    # Get user preferences
    prefs = store.get(("companion", user_id), "preferences")
    
    # Use in prompt
    prompt = f"Context: {prefs.value['content']}"
    
    # Update based on feedback
    store.put(
        ("companion", user_id),
        "preferences",
        {"content": "Updated preference"},
    )
    
    return {"messages": [response]}
```

## Testing

### Unit Tests

```bash
# SQLite adapter tests
poetry run pytest src/infrastructure/adapters/store/sqlite_test.py -v

# InMemory adapter tests (for fast unit tests)
poetry run pytest src/infrastructure/adapters/store/in_memory_test.py -v

# Memory service tests
poetry run pytest src/application/services/memory_test.py -v
```

### E2E Tests (Tests Both Adapters)

E2E tests automatically run against **both** InMemory and SQLite adapters:

```bash
poetry run pytest src/tests/integration/memory_e2e_test.py -v
```

This ensures compatibility across all store implementations.

### Test Coverage

- Namespace isolation
- Get/Put/Search/Delete operations
- Filter and limit queries
- Created/updated timestamp tracking
- Default initialization

## Production Considerations

### SQLite Store (Default - Portable)

**Current implementation** uses SQLite for production:

```python
# infrastructure/adapters/store/sqlite.py
store = SQLiteStoreAdapter("data/memory.db")
```

**Benefits:**
- **Portable**: Single file, works on Windows/Linux/macOS
- **Zero setup**: No external database server required
- **Persistent**: Data survives restarts
- **Fast**: Excellent for single-instance deployments
- **Embeddable**: Perfect for containerized apps

**Limitations:**
- Single-writer (not ideal for multi-instance horizontal scaling)
- No built-in replication

### PostgreSQL Store (Future)

For production with horizontal scaling, replace with PostgreSQL:

```python
# infrastructure/adapters/store/postgres.py
class PostgresStoreAdapter(StorePort):
    """PostgreSQL-backed store with pgvector."""
    
    def __init__(self, connection_string: str):
        self._pool = create_pool(connection_string)
```

**Benefits:**
- Multi-writer support
- Enterprise-grade reliability
- Built-in replication
- Strong consistency

### Redis Store (Future - High Performance)

### Semantic Search (Future)

Add vector embeddings for semantic memory:

```python
@dataclass
class StoreItem:
    # ... existing fields ...
    embedding: list[float] | None = None

async def search_semantic(
    self,
    query: str,
    namespace: tuple[str, ...],
    limit: int = 5,
) -> list[StoreItem]:
    """Semantic search using embeddings."""
```

### Memory Update Strategies

**Hot Path** (inline): Update during request
```python
# In node execution
await store.put(namespace, key, updated_value)
```

**Background Task**: Update after response
```python
# Queue for async processing
await queue.enqueue_memory_update(namespace, key, feedback)
```

## Design Principles

### SOLID Compliance

- **SRP**: StorePort handles storage, MemoryService handles business logic
- **OCP**: Extend with new store implementations (Postgres, Redis)
- **LSP**: All StorePort implementations are substitutable
- **ISP**: Minimal interface with only essential methods
- **DIP**: Application depends on StorePort interface

### Clean Architecture

- **Domain**: Interfaces (StorePort)
- **Application**: Services (MemoryService)
- **Infrastructure**: Adapters (InMemoryStoreAdapter)
- **Dependency Flow**: Inward (adapters depend on domain)

### Code Quality

- Functions: 4-5 lines max
- No deep nesting (flat abstractions)
- Explicit over implicit
- Type hints throughout
- Short docstrings only

## References

- [LangGraph Memory Guide](https://langchain-ai.github.io/langgraph/how-tos/memory/)
- [FareedKhan Long-Term Memory](https://github.com/FareedKhan-dev/langgraph-long-memory)
- [LangGraph Store API](https://langchain-ai.github.io/langgraph/reference/store/)
