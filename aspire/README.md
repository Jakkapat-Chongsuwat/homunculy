# Homunculy Aspire Orchestration

This directory contains the **.NET Aspire** AppHost that orchestrates the entire Homunculy microservices ecosystem for local development and provides a foundation for future cloud deployments.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Aspire Dashboard                                  │
│              (Logs, Traces, Metrics, Resource Management)               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┴───────────────────────────┐
        │                                                       │
        ▼                                                       ▼
┌───────────────────────────────┐         ┌───────────────────────────────┐
│      Homunculy Service        │         │    Management Service         │
│     (Python/FastAPI)          │◄────────│       (Go/Fiber)              │
│     Port: 8000                │         │     Port: 8080                │
│     - AI Agent Chat           │         │     - User Management         │
│     - WebSocket Streaming     │         │     - Quota Management        │
│     - TTS Integration         │         │     - Agent Assignment        │
└─────────────┬─────────────────┘         └──────────────┬────────────────┘
              │                                          │
              ▼                                          ▼
┌───────────────────────────────┐         ┌───────────────────────────────┐
│   Homunculy PostgreSQL        │         │   Management PostgreSQL       │
│     Port: 5433                │         │     Port: 5434                │
│     - Conversations           │         │     - Users                   │
│     - Agent State             │         │     - Quotas                  │
└───────────────────────────────┘         └───────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

1. **.NET 10 SDK** - [Download](https://dotnet.microsoft.com/download/dotnet/10.0)
2. **Docker Desktop** - Running and configured
3. **Aspire Workload** - Install with:
   ```bash
   dotnet workload install aspire
   ```

### Running the Application

```bash
# From the aspire directory
cd aspire

# Restore dependencies
dotnet restore

# Run the AppHost (this launches everything)
dotnet run --project Homunculy.AppHost
```

The Aspire Dashboard will automatically open in your browser, showing:
- All running services and their status
- Live logs from all containers
- Distributed traces
- Metrics and health checks

### Configuration

Secrets are managed via .NET User Secrets. Set them with:

```bash
cd Homunculy.AppHost

# Set database passwords
dotnet user-secrets set "Parameters:homunculy-db-password" "your-password"
dotnet user-secrets set "Parameters:management-db-password" "your-password"

# Set API keys
dotnet user-secrets set "Parameters:openai-api-key" "sk-..."
dotnet user-secrets set "Parameters:elevenlabs-api-key" "..."
```

Or for development, edit `appsettings.Development.json`.

## 📦 Project Structure

```
aspire/
├── Homunculy.sln                    # Solution file
├── global.json                       # .NET SDK version
├── Homunculy.AppHost/               # Main orchestration project
│   ├── Program.cs                   # App model definition
│   ├── Homunculy.AppHost.csproj
│   ├── appsettings.json
│   ├── appsettings.Development.json
│   └── Properties/
│       └── launchSettings.json
└── Homunculy.ServiceDefaults/       # Shared service configuration
    ├── Extensions.cs                # OpenTelemetry, health checks
    └── Homunculy.ServiceDefaults.csproj
```

## 🔧 What Aspire Provides (vs Docker Compose)

| Feature | Docker Compose | .NET Aspire |
|---------|---------------|-------------|
| Service Discovery | Manual env vars | Automatic injection |
| Health Checks | Manual setup | Built-in dashboard |
| Secrets Management | .env files | User secrets + Azure Key Vault |
| Observability | External tools | Integrated dashboard |
| Startup Order | depends_on | WaitFor with health checks |
| Port Conflicts | Manual resolution | Automatic allocation |
| Hot Reload | Limited | Full support for .NET |
| Deployment | Compose files | Kubernetes/Azure manifests |

## 🌐 Service Endpoints

When running, services are available at:

| Service | URL | Description |
|---------|-----|-------------|
| Aspire Dashboard | http://localhost:15178 | Orchestration UI |
| Homunculy API | http://localhost:8000 | AI Agent Service |
| Homunculy WebSocket | ws://localhost:8000/api/v1/ws/chat | Chat streaming |
| Management API | http://localhost:8080 | User/Quota management |
| pgAdmin | http://localhost:5050 | Database admin |

## 🚢 Deployment

### Generate Deployment Artifacts

```bash
# Generate Docker Compose (for self-hosted)
aspire publish -o ./artifacts/docker --publisher docker

# Generate Kubernetes manifests
aspire publish -o ./artifacts/k8s --publisher kubernetes

# Generate Azure Container Apps (preview)
aspire publish -o ./artifacts/azure --publisher azure
```

### Deploy to Azure Container Apps

```bash
# Using Azure Developer CLI
azd init
azd up
```

## 🔍 Telemetry Integration

For polyglot services (Python, Go), configure OTLP export to send telemetry to the Aspire dashboard:

### Python (Homunculy)
The service already uses structlog. Add OpenTelemetry:
```python
# In settings/logging.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Export to Aspire dashboard
exporter = OTLPSpanExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"))
```

### Go (Management Service)
```go
// In main.go
import "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"

exporter, _ := otlptracegrpc.New(ctx,
    otlptracegrpc.WithEndpoint(os.Getenv("OTEL_EXPORTER_OTLP_ENDPOINT")),
)
```

## 📝 Adding New Services

To add a new microservice:

```csharp
// In Program.cs

// For a .NET service
var newService = builder.AddProject<Projects.NewService>("new-service")
    .WithReference(homunculyDb)
    .WaitFor(homunculyApp);

// For a container (any language)
var newService = builder.AddContainer("new-service", "my-image")
    .WithDockerfile("../path-to-service", "Dockerfile")
    .WithHttpEndpoint(port: 9000, targetPort: 9000)
    .WithReference(homunculyApp);

// For an executable
var newService = builder.AddExecutable("worker", "python", "../scripts", "worker.py")
    .WithEnvironment("API_URL", homunculyApp.GetEndpoint("http"));
```

## ⚡ Development Workflow

1. **Make changes** to any service
2. **Re-run** `dotnet run --project Homunculy.AppHost`
3. **Monitor** via the Aspire Dashboard
4. **Debug** using VS Code or Visual Studio

### VS Code Integration

Install the "C# Dev Kit" extension for full Aspire support including:
- Service debugging
- Log viewing
- Resource inspection

## 🔒 Security Notes

- Never commit `appsettings.Development.json` with real secrets
- Use User Secrets for local development
- Use Azure Key Vault or similar for production
- API keys are passed as parameters, not hardcoded

## 📚 Resources

- [.NET Aspire Documentation](https://learn.microsoft.com/dotnet/aspire/)
- [Aspire Samples](https://github.com/dotnet/aspire-samples)
- [Aspire Community](https://github.com/dotnet/aspire)
