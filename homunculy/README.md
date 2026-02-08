# Homunculy AI Agent Service

🤖 Python/FastAPI backend for AI agents with LangGraph.

## How It Works

```mermaid
graph LR
    LINE[LINE] -->|webhook| WH[Webhook Handler]
    API[REST API] -->|/chat| AH[Agent Handler]

    WH --> RI[RouteInbound]
    AH --> CU[ChatUseCase]

    RI --> GW[GatewayOrchestrator]
    CU --> LLM

    GW --> DS[DualSystem]

    DS --> R[Reflex<br/>fast ≤300ms]
    DS --> C[Cognition<br/>deep reasoning]

    R --> LLM[LLM Provider]
    C --> LG[LangGraph]
    LG --> LLM

    LG --> MEM[(Memory<br/>SQLite)]
    LG --> CP[(Checkpointer)]
```

## Layers

```mermaid
graph TB
    subgraph Presentation
        H[handlers/line_webhook.py<br/>handlers/agent.py]
    end

    subgraph Application
        UC[use_cases/gateway/route_inbound.py<br/>use_cases/chat.py]
        SV[services/memory.py]
    end

    subgraph Domain
        E[entities/ — agent, message, session]
        P[interfaces/ — ports]
    end

    subgraph Infrastructure
        GW[adapters/gateway/ — orchestrator, routing]
        DS[adapters/dual_system/ — reflex, cognition]
        LG[adapters/langgraph/ — graph manager]
        ST[adapters/store/ — sqlite, in_memory]
        PS[persistence/ — checkpointer, session]
    end

    Presentation --> Application
    Application --> Domain
    Infrastructure --> Domain
    Application -.->|via ports| Infrastructure
```

## Quick Start

```bash
poetry install && make up   # :8000
make test                   # 90+ tests
```

<!-- LiveKit and Pipecat removed -->
