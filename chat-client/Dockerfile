# =============================================================================
# Chat Client - Multi-stage Dockerfile
# =============================================================================
# Purpose: Build and run Blazor Server application
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build TypeScript
# -----------------------------------------------------------------------------
FROM node:22-alpine AS typescript-build

WORKDIR /src

# Copy TypeScript project files
COPY src/ChatClient.Presentation.Web/TypeScript/package*.json ./
RUN npm ci

# Copy and build TypeScript
COPY src/ChatClient.Presentation.Web/TypeScript/ ./
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2: Build .NET Application
# -----------------------------------------------------------------------------
FROM mcr.microsoft.com/dotnet/sdk:10.0-preview AS dotnet-build

ARG ASPNETCORE_ENVIRONMENT=Production

WORKDIR /src

# Copy solution and project files
COPY *.sln ./
COPY src/ChatClient.Domain/*.csproj src/ChatClient.Domain/
COPY src/ChatClient.Application/*.csproj src/ChatClient.Application/
COPY src/ChatClient.Infrastructure/*.csproj src/ChatClient.Infrastructure/
COPY src/ChatClient.Presentation.Shared/*.csproj src/ChatClient.Presentation.Shared/
COPY src/ChatClient.Presentation.Web/*.csproj src/ChatClient.Presentation.Web/
COPY src/ChatClient.MauiServiceDefaults/*.csproj src/ChatClient.MauiServiceDefaults/

# Copy Aspire service defaults (required reference)
COPY ../aspire/Homunculy.ServiceDefaults/*.csproj ../aspire/Homunculy.ServiceDefaults/

# Restore dependencies
RUN dotnet restore src/ChatClient.Presentation.Web/ChatClient.Presentation.Web.csproj

# Copy source code
COPY src/ src/
COPY ../aspire/Homunculy.ServiceDefaults/ ../aspire/Homunculy.ServiceDefaults/

# Copy built TypeScript assets
COPY --from=typescript-build /src/dist/ src/ChatClient.Presentation.Web/wwwroot/js/

# Build and publish
WORKDIR /src/src/ChatClient.Presentation.Web
RUN dotnet publish -c Release -o /app/publish --no-restore

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
