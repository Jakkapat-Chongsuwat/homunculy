# 🧬 Homunculy

**AI Agent Management System** - A microservices platform for creating, managing, and interacting with conversational AI agents.

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        Chat Clients                               │
│           (Blazor Web + MAUI Desktop/Mobile)                     │
└────────────────────────────┬─────────────────────────────────────┘
                             │ WebSocket/REST
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Management Service (Go)                        │
│              Users • Quotas • Agent Assignment                    │
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTP
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Homunculy AI Service (Python)                   │
│           LangGraph Agents • TTS • Streaming Chat                │
└────────────────────────────┬─────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
  ┌────────────┐      ┌────────────┐      ┌────────────┐
  │ PostgreSQL │      │ PostgreSQL │      │   RAG      │
  │ (Homunculy)│      │(Management)│      │  Service   │
  └────────────┘      └────────────┘      └─────┬──────┘
                                                │
                                          ┌─────┴──────┐
                                          │  Pinecone  │
                                          │ (Vectors)  │
                                          └────────────┘
```

## 📁 Project Structure

| Folder | Language | Description |
|--------|----------|-------------|
| [`homunculy/`](./homunculy/) | Python | Core AI agent service (FastAPI + LangGraph) |
| [`rag-service/`](./rag-service/) | Python | RAG pipeline & semantic search (Pinecone) |
| [`management-service/`](./management-service/) | Go | User & quota management (Fiber) |
| [`chat-client/`](./chat-client/) | C# | Multi-platform UI (Blazor + MAUI) |
| [`aspire/`](./aspire/) | C# | Local dev orchestration (.NET Aspire) |
| [`infra/`](./infra/) | HCL | Azure infrastructure (Terraform) |
| [`homunculy-db/`](./homunculy-db/) | SQL | AI service database migrations |
| [`management-service-db/`](./management-service-db/) | SQL | Management database migrations |
| [`docs/`](./docs/) | MD | Project documentation |

## 🚀 Quick Start

### Prerequisites
- Docker Desktop
- .NET 10 SDK + Aspire workload
- Poetry (Python)
- Go 1.25+

### Run Everything (Recommended)
```bash
cd aspire
dotnet run --project Homunculy.AppHost
```
Opens Aspire Dashboard with all services running.

### Run Individual Services
```bash
# AI Service
cd homunculy && make run

# Management Service
cd management-service && go run ./cmd/server

# Chat Client (Web)
cd chat-client/src/ChatClient.Presentation.Web && dotnet run
```

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **AI/ML** | LangGraph, LangChain, OpenAI, PydanticAI |
| **RAG** | Pinecone (Vector DB), OpenAI Embeddings |
| **TTS** | ElevenLabs |
| **Backend** | FastAPI (Python), Fiber (Go) |
| **Frontend** | Blazor WebAssembly, MAUI |
| **Database** | PostgreSQL, Liquibase migrations |
| **Orchestration** | .NET Aspire |
| **Infrastructure** | Azure Container Apps, Terraform |
| **CI/CD** | GitHub Actions |

## 📋 Environment Setup

1. **Clone & setup secrets:**
```bash
git clone https://github.com/Jakkapat-Chongsuwat/homunculy.git
cd homunculy/aspire/Homunculy.AppHost

dotnet user-secrets set "Parameters:openai-api-key" "sk-..."
dotnet user-secrets set "Parameters:elevenlabs-api-key" "..."
```

2. **Run with Aspire:**
```bash
dotnet run --project Homunculy.AppHost
```

## 🔗 Service Endpoints (Local)

| Service | URL |
|---------|-----|
| Aspire Dashboard | http://localhost:15178 |
| Homunculy API | http://localhost:8000 |
| RAG Service | http://localhost:8001 |
| Management API | http://localhost:8080 |
| Chat Client | http://localhost:5000 |
| Pinecone Local | localhost:5081 |

## 📚 Documentation

- [Aspire Setup](./aspire/README.md) - Local development guide
- [Infrastructure](./infra/README.md) - Azure deployment
- [CI/CD Setup](./.github/CICD_SETUP.md) - GitHub Actions config

## 🏛️ Architecture Principles

- **Clean Architecture** - Separation of concerns
- **SOLID Principles** - Maintainable, testable code
- **Microservices** - Independent, deployable services
- **Infrastructure as Code** - Reproducible environments

## 📄 License

MIT License - see LICENSE file for details.
