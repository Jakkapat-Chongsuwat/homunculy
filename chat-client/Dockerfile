# =============================================================================
# Chat Client - Multi-stage Dockerfile
# =============================================================================
# Purpose: Build and run Blazor Server application
# Note: Build from repo root: docker build -f chat-client/Dockerfile .
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build TypeScript
# -----------------------------------------------------------------------------
FROM node:22-alpine AS typescript-build

WORKDIR /src

# Copy TypeScript project files
COPY chat-client/src/ChatClient.Presentation.Web/TypeScript/package*.json ./
RUN npm ci

# Copy and build TypeScript (outputs all .ts files to dist/)
COPY chat-client/src/ChatClient.Presentation.Web/TypeScript/ ./
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2: Build .NET Application
# -----------------------------------------------------------------------------
FROM mcr.microsoft.com/dotnet/sdk:10.0-preview AS dotnet-build

ARG ASPNETCORE_ENVIRONMENT=Production

WORKDIR /src

# Add NuGet source for preview packages
RUN dotnet nuget add source https://pkgs.dev.azure.com/dnceng/public/_packaging/dotnet10/nuget/v3/index.json -n dotnet10

# Copy solution and project files
COPY chat-client/*.sln ./chat-client/
COPY chat-client/src/ChatClient.Domain/*.csproj chat-client/src/ChatClient.Domain/
COPY chat-client/src/ChatClient.Application/*.csproj chat-client/src/ChatClient.Application/
COPY chat-client/src/ChatClient.Infrastructure/*.csproj chat-client/src/ChatClient.Infrastructure/
COPY chat-client/src/ChatClient.Presentation.Shared/*.csproj chat-client/src/ChatClient.Presentation.Shared/
COPY chat-client/src/ChatClient.Presentation.Web/*.csproj chat-client/src/ChatClient.Presentation.Web/
COPY chat-client/src/ChatClient.MauiServiceDefaults/*.csproj chat-client/src/ChatClient.MauiServiceDefaults/

# Copy Aspire service defaults (required reference)
COPY aspire/Homunculy.ServiceDefaults/*.csproj aspire/Homunculy.ServiceDefaults/

# Restore dependencies
RUN dotnet restore chat-client/src/ChatClient.Presentation.Web/ChatClient.Presentation.Web.csproj

# Copy source code
COPY chat-client/src/ chat-client/src/
COPY aspire/Homunculy.ServiceDefaults/ aspire/Homunculy.ServiceDefaults/

# Copy built TypeScript assets (all files from dist/)
COPY --from=typescript-build /src/dist/ chat-client/src/ChatClient.Presentation.Web/wwwroot/js/

# Build and publish (restore again to get packages from dotnet10 feed)
WORKDIR /src/chat-client/src/ChatClient.Presentation.Web
RUN dotnet publish -c Release -o /app/publish

# -----------------------------------------------------------------------------
# Stage 3: Runtime
# -----------------------------------------------------------------------------
FROM mcr.microsoft.com/dotnet/aspnet:10.0-preview AS runtime

# Set environment variables
ENV ASPNETCORE_URLS=http://+:8080 \
    ASPNETCORE_ENVIRONMENT=Production \
    DOTNET_RUNNING_IN_CONTAINER=true

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy published application
COPY --from=dotnet-build --chown=appuser:appuser /app/publish .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start application
ENTRYPOINT ["dotnet", "ChatClient.Presentation.Web.dll"]
