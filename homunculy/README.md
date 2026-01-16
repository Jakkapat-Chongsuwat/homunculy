# Homunculy AI Agent Service

🤖 **Core AI Agent Backend** - Python/FastAPI service powering conversational AI agents with streaming support.

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
make up

# Run tests
make test
```

## LiveKit + Pipecat + LangGraph (Worker)

This repo supports a LiveKit-first runtime via a separate worker process (recommended) while keeping FastAPI for HTTP management APIs.

For local self-hosted LiveKit, this repo uses a dev config with defaults:
- `LIVEKIT_URL=ws://localhost:7880`
- `LIVEKIT_API_KEY=devkey`
- `LIVEKIT_API_SECRET=devsecret`

```bash
# Install optional worker dependencies
poetry install --with livekit

# Start local LiveKit server (root docker-compose)
make livekit-up

# Generate a room join token (JWT) for a WebRTC client
make livekit-token ROOM=dev-room ID=web NAME="Web Client"

# Run the LiveKit Agents worker (preferred)
export LIVEKIT_URL=...
export LIVEKIT_API_KEY=...
export LIVEKIT_API_SECRET=...
make livekit-agent

# Alternatively run the standalone Pipecat worker (requires a room name)
export LIVEKIT_ROOM_NAME=dev-room
make livekit-worker
```