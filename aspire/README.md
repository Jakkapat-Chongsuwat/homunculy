# Homunculy Aspire Orchestration

.NET Aspire AppHost that orchestrates the Homunculy microservices ecosystem.

## Quick Start

### Prerequisites

- **.NET 10 SDK** - [Download](https://dotnet.microsoft.com/download/dotnet/10.0)
- **Docker Desktop** - Running
- **Aspire Workload** - `dotnet workload install aspire`

### Configuration

Copy the template and fill in your values:

```bash
cp Homunculy.AppHost/appsettings.Development.json.template Homunculy.AppHost/appsettings.Development.json
```

Or use .NET User Secrets:

```bash
cd Homunculy.AppHost
dotnet user-secrets set "Parameters:homunculy-db-password" "your-password"
dotnet user-secrets set "Parameters:management-db-password" "your-password"
dotnet user-secrets set "Parameters:openai-api-key" "sk-..."
dotnet user-secrets set "Parameters:elevenlabs-api-key" "..."
dotnet user-secrets set "Parameters:livekit-api-key" "devkey"
dotnet user-secrets set "Parameters:livekit-api-secret" "devsecret"
```

### Run

```bash
dotnet run --project Homunculy.AppHost
```

The Aspire Dashboard opens automatically with logs, traces, and metrics.

## Service Endpoints

| Service | URL |
| ------- | --- |
| Aspire Dashboard | `http://localhost:15178` |
| Homunculy API | `http://localhost:8000` |
| Chat WebSocket | `ws://localhost:8000/api/v1/ws/chat` |
| LiveKit | `ws://localhost:7880` |
| Management API | `http://localhost:8080` |
| pgAdmin | `http://localhost:5050` |

## Project Structure

```text
aspire/
├── Homunculy.AppHost/           # Orchestration
│   ├── Program.cs               # Service definitions
│   └── appsettings.*.json       # Configuration
└── Homunculy.ServiceDefaults/   # Shared config (OpenTelemetry, health)
```

## Adding Services

```csharp
// Container (Python, Go, etc.)
var svc = builder.AddContainer("my-service", "image")
    .WithDockerfile("../path", "Dockerfile")
    .WithHttpEndpoint(port: 9000, targetPort: 9000)
    .WaitFor(homunculyApp);

// .NET project
var svc = builder.AddProject<Projects.MyService>("my-service")
    .WithReference(homunculyDb);
```

## Security

- `appsettings.Development.json` is gitignored - never commit secrets
- Use User Secrets locally, Azure Key Vault in production
