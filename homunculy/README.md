# Homunculy AI Agent Service

🤖 Python/FastAPI backend for conversational AI agents with real-time voice via LiveKit + Pipecat + LangGraph.

## Architecture

```mermaid
graph TB
    subgraph Presentation["presentation/ (User-Facing)"]
        HTTP["/chat HTTP API"]
        WH["Webhooks"]
    end

    subgraph Application["application/ (Business Logic)"]
        UC["Use Cases"]
        LG["LangGraph RAG"]
    end

    subgraph Infrastructure["infrastructure/ (External)"]
        subgraph Transport["transport/ (WebRTC)"]
            LK["LiveKit Worker"]
            PC["Pipecat Pipeline"]
        end
        AD["Adapters (LLM/TTS/STT)"]
        DB["Persistence"]
    end

    subgraph Domain["domain/ (Core)"]
        EN["Entities"]
        IF["Interfaces (Ports)"]
    end

    HTTP --> UC
    LK --> PC
    PC --> LG
    UC --> LG
    LG --> AD
    AD --> IF
    UC --> IF
```

## Quick Start

```bash
poetry install && make up        # HTTP API on :8000
make test                        # 75 tests in parallel
```

## Voice Agent (LiveKit)

```bash
make livekit-up                  # Start local LiveKit server
make livekit-token ROOM=dev-room # Generate JWT token
make livekit-agent               # Run voice worker
```

Environment: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
