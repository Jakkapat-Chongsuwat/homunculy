/*
 * Homunculy AppHost - .NET Aspire Orchestration
 * 
 * This AppHost orchestrates the entire Homunculy microservices ecosystem:
 * - Homunculy (Python/FastAPI) - AI Agent Service
 * - Management Service (Go/Fiber) - User & Quota Management
 * - PostgreSQL Databases (2 instances)
 * - Liquibase Migrations
 * - pgAdmin (development tool)
 * 
 * Architecture follows Clean Architecture principles across all services.
 */

var builder = DistributedApplication.CreateBuilder(args);

// =============================================================================
// PARAMETERS - Externalized secrets and configuration
// =============================================================================

var homunculyDbPassword = builder.AddParameter("homunculy-db-password", secret: true);
var managementDbPassword = builder.AddParameter("management-db-password", secret: true);
var openaiApiKey = builder.AddParameter("openai-api-key", secret: true);
var elevenLabsApiKey = builder.AddParameter("elevenlabs-api-key", secret: true);

// =============================================================================
// HOMUNCULY SERVICE STACK (Python/FastAPI + PostgreSQL)
// =============================================================================

// Homunculy PostgreSQL Database with pgAdmin
var homunculyPostgres = builder.AddPostgres("homunculy-postgres", password: homunculyDbPassword)
    .WithDataVolume("homunculy-postgres-data")
    .WithPgAdmin();
    
var homunculyDb = homunculyPostgres.AddDatabase("homunculy");

// Homunculy Liquibase Migrations (runs once and exits)
var homunculyMigrations = builder.AddContainer("homunculy-migrations", "liquibase/liquibase", "4.33.0")
    .WithBindMount("../../homunculy-db/changelog", "/liquibase/changelog")
    .WithEnvironment("LIQUIBASE_COMMAND_CHANGELOG_FILE", "changelog/db.changelog-master.xml")
    .WithEnvironment("LIQUIBASE_COMMAND_URL", "jdbc:postgresql://homunculy-postgres:5432/homunculy")
    .WithEnvironment("LIQUIBASE_COMMAND_USERNAME", "postgres")
    .WithEnvironment("LIQUIBASE_COMMAND_PASSWORD", homunculyDbPassword)
    .WithArgs("update")
    .WaitFor(homunculyPostgres);

// Homunculy Python/FastAPI Application
var homunculyApp = builder.AddContainer("homunculy-app", "homunculy-app")
    .WithDockerfile("../../homunculy", "Dockerfile")
    .WithHttpEndpoint(port: 8000, targetPort: 8000, name: "http")
    // App Settings
    .WithEnvironment("APP_HOST", "0.0.0.0")
    .WithEnvironment("APP_PORT", "8000")
    .WithEnvironment("APP_DEBUG", "false")
    // Database Settings
    .WithEnvironment("DB_HOST", "homunculy-postgres")
    .WithEnvironment("DB_PORT", "5432")
    .WithEnvironment("DB_NAME", "homunculy")
    .WithEnvironment("DB_USER", "postgres")
    .WithEnvironment("DB_PASSWORD", homunculyDbPassword)
    // LLM Settings
    .WithEnvironment("LLM_PROVIDER", "openai")
    .WithEnvironment("LLM_OPENAI_API_KEY", openaiApiKey)
    .WithEnvironment("LLM_DEFAULT_MODEL", "gpt-4o-mini")
    .WithEnvironment("LLM_DEFAULT_TEMPERATURE", "0.7")
    .WithEnvironment("LLM_DEFAULT_MAX_TOKENS", "2000")
    // TTS Settings
    .WithEnvironment("TTS_PROVIDER", "elevenlabs")
    .WithEnvironment("ELEVENLABS_API_KEY", elevenLabsApiKey)
    .WithEnvironment("TTS_ELEVENLABS_API_KEY", elevenLabsApiKey)
    .WithEnvironment("TTS_ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
    .WithEnvironment("TTS_ELEVENLABS_STREAMING_MODEL_ID", "eleven_turbo_v2_5")
    // Logging
    .WithEnvironment("LOGGING_LEVEL", "INFO")
    .WithEnvironment("LOGGING_FORMAT", "json")
    .WithBindMount("../../homunculy/logs", "/app/logs")
    .WaitFor(homunculyMigrations);

// =============================================================================
// MANAGEMENT SERVICE STACK (Go/Fiber + PostgreSQL)
// =============================================================================

// Management PostgreSQL Database
var managementPostgres = builder.AddPostgres("management-postgres", password: managementDbPassword)
    .WithDataVolume("management-postgres-data");
    
var managementDb = managementPostgres.AddDatabase("management");

// Management Liquibase Migrations
var managementMigrations = builder.AddContainer("management-migrations", "liquibase/liquibase", "4.33.0")
    .WithBindMount("../../management-service-db/changelog", "/liquibase/changelog")
    .WithEnvironment("LIQUIBASE_COMMAND_CHANGELOG_FILE", "changelog/db.changelog-master.xml")
    .WithEnvironment("LIQUIBASE_COMMAND_URL", "jdbc:postgresql://management-postgres:5432/management")
    .WithEnvironment("LIQUIBASE_COMMAND_USERNAME", "postgres")
    .WithEnvironment("LIQUIBASE_COMMAND_PASSWORD", managementDbPassword)
    .WithArgs("update")
    .WaitFor(managementPostgres);

// Management Go/Fiber Application
var managementApp = builder.AddContainer("management-app", "management-app")
    .WithDockerfile("../../management-service", "Dockerfile")
    .WithHttpEndpoint(port: 8080, targetPort: 8080, name: "http")
    .WithEnvironment("SERVER_HOST", "0.0.0.0")
    .WithEnvironment("SERVER_PORT", "8080")
    .WithEnvironment("DB_HOST", "management-postgres")
    .WithEnvironment("DB_PORT", "5432")
    .WithEnvironment("DB_NAME", "management")
    .WithEnvironment("DB_USER", "postgres")
    .WithEnvironment("DB_PASSWORD", managementDbPassword)
    .WithEnvironment("DB_SSL_MODE", "disable")
    .WithEnvironment("HOMUNCULY_BASE_URL", homunculyApp.GetEndpoint("http"))
    .WithEnvironment("HOMUNCULY_API_KEY", "dev_api_key_123")
    .WaitFor(managementMigrations)
    .WaitFor(homunculyApp);

// =============================================================================
// EXTERNAL HTTP ENDPOINTS (exposed to outside)
// =============================================================================

homunculyApp.WithExternalHttpEndpoints();
managementApp.WithExternalHttpEndpoints();

// =============================================================================
// BUILD AND RUN
// =============================================================================

builder.Build().Run();
