# Agent-as-Service Architecture

The "Super Agent" pattern where **Agent controls itself**, not LiveKit.

## Language Split (2026 Best Practice)

| Layer | Language | Responsibility |
|-------|----------|----------------|
| **Control Plane** | Go | Users, DB, auth, calling agent /join API |
| **Agent Worker** | Python | LiveKit connection, STT/LLM/TTS pipeline |
| **Supervisor Logic** | Python (LangGraph) | Orchestrating specialist sub-agents |

## Clean Architecture Structure

```
homunculy/src/
├── domain/                      # DOMAIN LAYER (innermost)
│   ├── entities/                # Core business objects
│   │   ├── agent.py             # AgentConfiguration, AgentResponse
│   │   ├── message.py           # Message entities
│   │   └── session.py           # Session entities
│   └── interfaces/              # Ports (abstractions)
│       ├── agent.py             # AgentPort, AgentRouterPort
│       ├── llm.py               # LLMPort
│       ├── stt.py               # STTPort
│       ├── tts.py               # TTSPort
│       └── rag.py               # RAGPort
│
├── application/                 # APPLICATION LAYER
│   ├── graphs/                  # LangGraph workflows
│   │   ├── builder.py           # Graph construction
│   │   ├── state.py             # GraphState definitions
│   │   ├── nodes/               # Graph nodes
│   │   └── edges/               # Routing logic
│   └── use_cases/               # Use case orchestration
│       ├── chat.py              # ChatUseCase
│       └── voice.py             # VoiceUseCase
│
├── agents/                      # AGENT LAYER (uses application)
│   ├── supervisor/              # Supervisor agent
│   │   ├── agent.py             # SupervisorAgent class
│   │   └── router.py            # LangGraph router
│   ├── specialists/             # Sub-agents
│   │   ├── sales.py             # SalesAgent
│   │   └── tech_support.py      # TechSupportAgent
│   └── session.py               # AgentSession lifecycle
│
├── infrastructure/              # INFRASTRUCTURE LAYER (outermost)
│   ├── adapters/                # Port implementations
│   │   ├── langgraph/           # LangGraph adapters
│   │   │   ├── adapter.py       # LangGraphLLMAdapter
│   │   │   └── pipecat_service.py # Pipecat bridge
│   │   ├── elevenlabs/          # TTS adapter
│   │   └── openai/              # LLM/STT adapters
│   ├── transport/               # Transport layer
│   │   ├── livekit_worker.py    # HTTP service (thin)
│   │   └── session_handle.py    # Session management
│   ├── persistence/             # State persistence
│   │   └── checkpointer.py      # UoW for checkpointer
│   └── container.py             # DI container
│
└── presentation/                # PRESENTATION LAYER
    ├── http/                    # REST API handlers
    └── webhooks/                # Webhook handlers
```

## SOLID Principles Applied

| Principle | Implementation |
|-----------|----------------|
| **S - Single Responsibility** | Each file has ONE job (session_handle.py, livekit_worker.py) |
| **O - Open/Closed** | Add specialists without modifying Supervisor |
| **L - Liskov Substitution** | All adapters implement domain interfaces |
| **I - Interface Segregation** | Small focused ports (LLMPort, TTSPort, STTPort) |
| **D - Dependency Inversion** | Infrastructure depends on domain, not reverse |

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER (Browser/Client)                    │
│  1. Request token → 4. Connect to LiveKit with token            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              MANAGEMENT SERVICE (Control Plane)                  │
│                                                                  │
│  2. Issue user token (no dispatch)                              │
│  3. POST /join to Agent (room, user_id, metadata)               │
│                                                                  │
│  Management decides WHEN and IF agent joins                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ AGENT (Python)  │  │ AGENT (Python)  │  │ AGENT (Python)  │
│ Agent Service   │  │ Agent Service   │  │ Agent Service   │
│                 │  │                 │  │                 │
│ POST /join      │  │ POST /join      │  │ POST /join      │
│ POST /leave     │  │ POST /leave     │  │ POST /leave     │
│ GET /sessions   │  │ GET /sessions   │  │ GET /sessions   │
│ GET /health     │  │ GET /health     │  │ GET /health     │
│                 │  │                 │  │                 │
│ Agent creates   │  │ Agent creates   │  │ Agent creates   │
│ its own token   │  │ its own token   │  │ its own token   │
│ and connects    │  │ and connects    │  │ and connects    │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LIVEKIT (Media Router ONLY)                    │
│                                                                  │
│  Just routes audio/video/data between participants              │
│  Has NO control over agents                                     │
│  Doesn't dispatch anything                                      │
└─────────────────────────────────────────────────────────────────┘
```

## Key Points

1. **Agent is ACTIVE** - It decides to connect when commanded by Control Plane
2. **LiveKit is PASSIVE** - Just routes media, no agent dispatch logic
3. **Control Plane owns orchestration** - Management Service decides who joins when
4. **Agent creates own token** - Agent has API keys, creates its own join token
5. **Horizontal scaling** - Multiple agent instances, each an HTTP service

## API Endpoints

### Agent Service (homunculy-app:8000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/join` | POST | Control Plane commands agent to join room |
| `/leave` | POST | Control Plane commands agent to leave room |
| `/sessions` | GET | List active agent sessions |
| `/health` | GET | Health check |

### Management Service (management-app:8080)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/livekit/token` | POST | Issue token AND tell agent to join |
| `/api/v1/health` | GET | Health check |

## Request Flow

```
POST /api/v1/livekit/token
{
  "room": "room-123",
  "identity": "user-456"
}

Management Service:
  1. Creates user token (no dispatch)
  2. POST to http://homunculy-app:8000/join
     {
       "room": "room-123",
       "user_id": "user-456",
       "metadata": {...}
     }
  3. Returns token to user

Agent receives /join:
  1. Creates session handle
  2. Creates own token with API keys
  3. Connects to LiveKit room
  4. Runs STT/LLM/TTS pipeline
```

## Scaling

Each agent replica is an independent HTTP service:
- Load balancer distributes `/join` requests
- Each agent manages its own sessions
- State stored in Redis (future: multi-tenant keyed by session_id)
