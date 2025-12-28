# Homunculy AI Agent Service

🤖 **Core AI Agent Backend** - Python/FastAPI service powering conversational AI agents with streaming support.

## Overview

| Aspect | Details |
|--------|---------|
| **Language** | Python 3.12+ |
| **Framework** | FastAPI |
| **AI Engine** | LangGraph + LangChain + OpenAI |
| **TTS** | ElevenLabs Integration |
| **Database** | PostgreSQL (async) |
| **Architecture** | Clean Architecture |

## Key Features

- 🔄 **WebSocket Streaming** - Real-time chat with token-by-token responses
- 🎙️ **Text-to-Speech** - ElevenLabs voice synthesis integration
- 📊 **LangGraph Agents** - Stateful AI agents with memory persistence
- 🔌 **REST + GraphQL APIs** - Flexible API consumption options
- ✅ **Checkpoint System** - Conversation state persistence

## Project Structure

```
homunculy/
├── src/
│   ├── main.py              # FastAPI application entry
│   ├── common/              # Shared utilities & base classes
│   ├── internal/            # Core business logic (agents, chat)
│   └── settings/            # Configuration & environment
├── tests/                   # Unit, integration, e2e tests
├── logs/                    # Application logs & audio files
└── Dockerfile               # Container definition
```

## Quick Start

```bash
# Install dependencies
poetry install

# Run locally
make run

# Run tests
make test
```