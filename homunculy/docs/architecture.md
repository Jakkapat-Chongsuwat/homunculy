# Homunculy 2026 Architecture

## Hybrid Dual-System Architecture

This document describes the Clean Architecture implementation of the Homunculy AI agent using the 2026 Hybrid Dual-System pattern.

## Architecture Diagram

```mermaid
flowchart TB
    subgraph "Transport Layer (LiveKit/WebRTC)"
        Input["🎤 Audio/Visual Stream"]
        Output["🔊 Voice/Avatar Response"]
    end

    subgraph "Presentation Layer"
        API["FastAPI Handlers"]
        Worker["LiveKit Agent Worker"]
    end

    subgraph "Application Layer"
        DualSystem["DualSystemOrchestrator"]
    end

    subgraph "Domain Layer (Interfaces/Ports)"
        ReflexPort["ReflexPort"]
        CognitionPort["CognitionPort"]
        EmotionPort["EmotionDetectorPort"]
        OrchestratorPort["OrchestratorPort"]
    end

    subgraph "Infrastructure Layer (Adapters)"
        Reflex["ReflexAdapter<br/>Pattern Matching<br/>< 300ms"]
        Cognition["CognitionAdapter<br/>LangGraph"]
        Emotion["EmotionDetector"]
        
        subgraph "Orchestration Adapters"
            LangGraph["LangGraphOrchestrator"]
            Swarm["SwarmOrchestrator<br/>Handoff Pattern"]
        end
        
        subgraph "Transport Adapters"
            LiveKit["LiveKitRoom"]
            TokenGen["TokenGenerator"]
        end
    end

    subgraph "External Services"
        OpenAI["OpenAI API"]
        ElevenLabs["ElevenLabs TTS"]
        Postgres["PostgreSQL<br/>Checkpointer"]
    end

    Input --> Worker
    Worker --> DualSystem
    API --> DualSystem
    
    DualSystem --> ReflexPort
    DualSystem --> CognitionPort
    DualSystem --> EmotionPort
    
    ReflexPort -.-> Reflex
    CognitionPort -.-> Cognition
    EmotionPort -.-> Emotion
    
    Cognition --> OrchestratorPort
    OrchestratorPort -.-> LangGraph
    OrchestratorPort -.-> Swarm
    
    LangGraph --> OpenAI
    Swarm --> OpenAI
    Cognition --> Postgres
    
    DualSystem --> Output
    
    classDef domain fill:#e1f5fe,stroke:#01579b
    classDef infra fill:#fff3e0,stroke:#e65100
    classDef external fill:#f3e5f5,stroke:#4a148c
    classDef fast fill:#c8e6c9,stroke:#1b5e20
    classDef slow fill:#ffcdd2,stroke:#b71c1c
    
    class ReflexPort,CognitionPort,EmotionPort,OrchestratorPort domain
    class Reflex,Cognition,Emotion,LangGraph,Swarm,LiveKit,TokenGen infra
    class OpenAI,ElevenLabs,Postgres external
    class Reflex fast
    class Cognition,LangGraph,Swarm slow
```

## Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant Worker as LiveKit Worker
    participant DS as DualSystem
    participant Reflex as ReflexAdapter
    participant Emotion as EmotionDetector
    participant Cognition as CognitionAdapter
    participant LLM as OpenAI

    User->>Worker: "Hello, how are you?"
    Worker->>DS: process(input)
    
    par Parallel Processing
        DS->>Emotion: detect(input)
        Emotion-->>DS: NEUTRAL
    and
        DS->>Reflex: can_handle(input)
        Reflex-->>DS: true (greeting)
    end
    
    DS->>Reflex: respond(input)
    Reflex-->>DS: "Hi! How can I help?"
    DS-->>Worker: ReflexOutput
    Worker-->>User: Fast response (< 300ms)

    Note over User,LLM: Complex query flow

    User->>Worker: "Explain quantum computing"
    Worker->>DS: process(input)
    
    DS->>Reflex: can_handle(input)
    Reflex-->>DS: false (complex)
    
    DS->>Reflex: respond(input)
    Reflex-->>DS: "Let me think..."
    DS-->>Worker: Filler response
    
    DS->>Cognition: reason(input)
    Cognition->>LLM: invoke(prompt)
    LLM-->>Cognition: detailed response
    Cognition-->>DS: CognitionOutput
    DS-->>Worker: Final response
    Worker-->>User: Deep response
```

## Layer Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  (FastAPI handlers, LiveKit worker, GraphQL)               │
│                         ↓                                   │
├─────────────────────────────────────────────────────────────┤
│                    Application Layer                        │
│  (Use cases, DualSystemOrchestrator)                        │
│                         ↓                                   │
├─────────────────────────────────────────────────────────────┤
│                      Domain Layer                           │
│  (Entities, Interfaces/Ports - NO external dependencies)   │
│                         ↑                                   │
├─────────────────────────────────────────────────────────────┤
│                   Infrastructure Layer                      │
│  (Adapters: LangGraph, LiveKit, OpenAI, Postgres)          │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Dual-System  │  │ Orchestration│  │   Transport  │      │
│  │   Adapters   │  │   Adapters   │  │   Adapters   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Principles

### 1. Dependency Inversion (DIP)
- Domain layer defines interfaces (ports)
- Infrastructure implements these interfaces (adapters)
- Dependencies point inward (toward domain)

### 2. Single Responsibility (SRP)
- `ReflexAdapter`: Fast pattern-based responses only
- `CognitionAdapter`: Deep reasoning only
- `EmotionDetector`: Emotional tone detection only
- `DualSystemOrchestrator`: Coordination only

### 3. Open/Closed Principle (OCP)
- Add new orchestrators without modifying existing code
- Swap LangGraph for AutoGen via factory
- Add new transport (Daily) via adapter

### 4. Interface Segregation (ISP)
- `ReflexPort`: `respond()`, `can_handle()`
- `CognitionPort`: `reason()`, `stream()`
- `OrchestratorPort`: `invoke()`, `stream()`

### 5. Liskov Substitution (LSP)
- Any `OrchestratorPort` implementation works
- Swarm and LangGraph are interchangeable

## Directory Structure

```
src/
├── main.py                          # Entrypoint - ALL wiring here
├── domain/
│   ├── entities/                    # Business objects
│   │   ├── agent.py
│   │   ├── message.py
│   │   └── session.py
│   └── interfaces/                  # Ports (contracts)
│       ├── dual_system.py           # ReflexPort, CognitionPort
│       ├── orchestration.py         # OrchestratorPort
│       └── transport.py             # RoomPort, TokenGeneratorPort
├── application/
│   └── use_cases/
│       ├── chat.py
│       └── voice.py
├── infrastructure/
│   ├── container.py                 # DI container
│   └── adapters/
│       ├── factory.py               # Adapter creation
│       ├── dual_system/             # Reflex + Cognition adapters
│       │   ├── reflex.py
│       │   ├── cognition.py
│       │   ├── emotion.py
│       │   └── orchestrator.py
│       ├── orchestration/           # LangGraph, Swarm
│       │   ├── langgraph_adapter.py
│       │   └── swarm_adapter.py
│       └── transport/               # LiveKit
│           └── livekit_adapter.py
├── presentation/
│   └── http/
│       └── handlers/
└── tests/
    └── e2e/                         # End-to-end with testcontainers
        ├── conftest.py
        ├── test_dual_system.py
        └── test_api.py
```

## Running Tests

```bash
# Unit tests
cd homunculy && make test

# E2E tests with containers
cd homunculy && pytest src/tests/e2e/ -v

# Full stack with Aspire
cd aspire && dotnet run --project Homunculy.AppHost
```
