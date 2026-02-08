# Homunculy AI Agent Service

🤖 Python/FastAPI backend for AI agents with LangGraph.

## Request Flow

```mermaid
graph LR
    A[LINE Webhook] --> B[presentation/webhooks/line.py]
    B --> C[infrastructure/adapters/gateway]
    C --> D{Route by tenant}
    
    D --> E1[Chat Use Case]
    D --> E2[Voice Use Case]
    D --> E3[Companion Use Case]
    
    E1 --> F[LangGraph Agent]
    E2 --> F
    E3 --> F
    
    F --> G1[Memory Service<br/>long-term storage]
    F --> G2[Checkpointer<br/>thread state]
    
    G1 --> H1[(SQLite Store)]
    G2 --> H2[(Postgres/Memory)]
    
    F --> I[LLM Provider]
    I --> F
    F --> E1
    F --> E2
    F --> E3
    E1 --> C
    E2 --> C
    E3 --> C
    C --> B
    B --> A
```

## Layers

```mermaid
graph TB
    subgraph P[Presentation Layer]
        HTTP[webhooks/line.py<br/>http/api.py]
    end
    
    subgraph A[Application Layer]
        UC[use_cases/<br/>chat, voice, companion]
        MS[services/memory.py]
    end
    
    subgraph I[Infrastructure Layer]
        GW[adapters/gateway]
        ST[adapters/store<br/>in_memory, sqlite]
        CP[persistence/checkpointer]
        SS[persistence/session]
    end
    
    subgraph D[Domain Layer]
        E[entities/<br/>agent, message, session]
        IF[interfaces/<br/>ports]
    end
    
    P --> A
    A --> I
    A --> D
    I --> D
```

## Quick Start

```bash
poetry install && make up   # :8000
make test                   # 90+ tests
```

<!-- LiveKit and Pipecat removed -->
