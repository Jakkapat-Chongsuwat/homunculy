# Chat Client

💬 **Multi-Platform Chat UI** - .NET Blazor application for interacting with Homunculy AI agents.

## Overview 

| Aspect | Details |
|--------|---------|
| **Framework** | .NET 8 / Blazor |
| **Platforms** | Web (WASM) + MAUI (Desktop/Mobile) |
| **UI** | Blazor Components |
| **Architecture** | Clean Architecture + MVVM |

## Key Features

- 🌐 **Web Client** - Blazor WebAssembly for browser access
- 📱 **MAUI Client** - Native Windows/macOS/iOS/Android
- 🔄 **Real-time Chat** - WebSocket streaming integration
- 🎨 **Shared Components** - Reusable UI across platforms
- 🏗️ **Aspire Ready** - Integrated with .NET Aspire orchestration

## Project Structure

```
chat-client/
├── src/
│   ├── ChatClient.Domain/              # Domain entities
│   ├── ChatClient.Application/         # Use cases & services
│   ├── ChatClient.Infrastructure/      # API clients, persistence
│   ├── ChatClient.Presentation.Shared/ # Shared Blazor components
│   ├── ChatClient.Presentation.Web/    # Blazor WASM app
│   ├── ChatClient.Presentation.Maui/   # MAUI native app
│   └── ChatClient.MauiServiceDefaults/ # MAUI service config
└── Dockerfile                          # Web container build
```

## Quick Start

### Web (Blazor WASM)
```bash
cd src/ChatClient.Presentation.Web
dotnet run
```

### MAUI (Desktop)
```bash
cd src/ChatClient.Presentation.Maui
dotnet build -f net8.0-windows10.0.19041.0
```

### Via Aspire (Recommended)
```bash
cd ../aspire
dotnet run --project Homunculy.AppHost
```

## Configuration

| Setting | Description |
|---------|-------------|
| `ConnectionStrings__homunculy-app` | AI service URL |
| `ApiSettings__BaseUrl` | API base URL |

## Platforms Supported

| Platform | Status |
|----------|--------|
| Web (WASM) | ✅ Production |
| Windows | ✅ Supported |
| macOS | 🔄 In Progress |
| iOS/Android | 📋 Planned |
