# Homunculy AI Agent Service

🤖 Python/FastAPI backend for AI agents with LiveKit + Pipecat + LangGraph.

## Architecture

```mermaid
graph TB
    subgraph DI["DI Container"]
        C[Container]
    end
    
    subgraph Presentation["presentation/"]
        HTTP[HTTP Handlers]
    end

    subgraph Application["application/"]
        UC[Use Cases]
        LG[LangGraph]
    end

    subgraph Infrastructure["infrastructure/"]
        AD[Adapters]
        UOW[CheckpointerUoW]
        FAC[Factory]
    end

    C -->|inject| HTTP
    C -->|inject| AD
    HTTP --> UC --> LG --> AD
    FAC -->|create| UOW
    UOW -->|checkpointer| LG
```

## Quick Start

```bash
poetry install && make up   # :8000
make test                   # 90+ tests
```

## Voice (LiveKit)

```bash
make livekit-up && make livekit-agent
```
