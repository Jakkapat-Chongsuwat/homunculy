# Management Service

🔧 **User & Quota Management** - Go/Fiber microservice for user accounts, quotas, and agent assignments.

## Overview

| Aspect | Details |
|--------|---------|
| **Language** | Go 1.25+ |
| **Framework** | Fiber v2 |
| **Database** | PostgreSQL (pgx) |
| **Logging** | Uber Zap |
| **Architecture** | Clean Architecture |

## Key Features

- 👤 **User Management** - Account creation, subscription tiers
- 📊 **Quota Tracking** - Token usage limits per user
- 🤖 **Agent Assignment** - Map users to AI agent configurations
- 📈 **Usage Metrics** - Track costs and consumption
- 🔗 **Homunculy Integration** - Proxy calls to AI service

## Project Structure

```
management-service/
├── cmd/
│   └── server/main.go       # Application entry point
├── internal/
│   ├── adapters/            # HTTP/gRPC handlers
│   │   ├── http/            # REST controllers
│   │   └── grpc/            # gRPC handlers
│   ├── domain/              # Business entities
│   │   ├── entities/        # User, Quota, Agent models
│   │   ├── repositories/    # Repository interfaces
│   │   └── services/        # Domain services
│   ├── infrastructure/      # External integrations
│   │   ├── config/          # Configuration loader
│   │   └── database/        # PostgreSQL connection
│   └── usecases/            # Application logic
│       ├── agent/           # Agent use cases
│       └── user/            # User use cases
├── pkg/                     # Shared packages
└── Dockerfile               # Container definition
```

## Quick Start

```bash
# Build
go build -o bin/server ./cmd/server

# Run
./bin/server

# With hot reload
air
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/users` | Create user |
| `GET` | `/api/users/:id` | Get user |
| `GET` | `/api/users/:id/quota` | Get user quota |
| `POST` | `/api/users/:id/agents` | Assign agent |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SERVER_HOST` | Bind address (default: 0.0.0.0) |
| `SERVER_PORT` | Port (default: 8080) |
| `DB_HOST`, `DB_NAME` | PostgreSQL connection |
| `HOMUNCULY_BASE_URL` | AI service URL |
