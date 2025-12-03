var builder = DistributedApplication.CreateBuilder(args);

// Parameters
var homunculyDbPassword = builder.AddParameter("homunculy-db-password", secret: true);
var managementDbPassword = builder.AddParameter("management-db-password", secret: true);
var openaiApiKey = builder.AddParameter("openai-api-key", secret: true);
var elevenLabsApiKey = builder.AddParameter("elevenlabs-api-key", secret: true);

// ============================================================================
// RAG Stack (Pinecone Local + RAG Service)
// ============================================================================

// Pinecone Local - Vector Database for RAG
var pineconeLocal = builder.AddContainer("pinecone-local", "ghcr.io/pinecone-io/pinecone-index", "latest")
    .WithHttpEndpoint(port: 5081, targetPort: 5081, name: "grpc")
    .WithEnvironment("PORT", "5081")
    .WithEnvironment("INDEX_TYPE", "serverless")
    .WithEnvironment("DIMENSION", "1536")
    .WithEnvironment("METRIC", "cosine")
    .WithVolume("pinecone-local-data", "/data");

// RAG Service (Python/FastAPI)
var ragService = builder.AddContainer("rag-service", "rag-service")
    .WithDockerfile("../../rag-service", "Dockerfile")
    .WithHttpEndpoint(port: 8001, targetPort: 8001, name: "http")
    .WithEnvironment("APP_HOST", "0.0.0.0")
    .WithEnvironment("APP_PORT", "8001")
    .WithEnvironment("PINECONE_ENVIRONMENT", "local")
    .WithEnvironment("PINECONE_API_KEY", "pclocal")
    .WithEnvironment("PINECONE_HOST", "pinecone-local:5081")
    .WithEnvironment("PINECONE_INDEX_NAME", "homunculy-rag")
    .WithEnvironment("PINECONE_DIMENSION", "1536")
    .WithEnvironment("OPENAI_API_KEY", openaiApiKey)
    .WithEnvironment("EMBEDDING_MODEL", "text-embedding-3-small")
    .WithEnvironment("RAG_CHUNK_SIZE", "512")
    .WithEnvironment("RAG_TOP_K", "5")
    .WithExternalHttpEndpoints()
    .WaitFor(pineconeLocal);

// ============================================================================
// Homunculy Stack (Python/FastAPI + PostgreSQL)
// ============================================================================
var homunculyPostgres = builder.AddPostgres("homunculy-postgres", password: homunculyDbPassword)
    .WithDataVolume("homunculy-postgres-data")
    .WithPgAdmin();
    
var homunculyDb = homunculyPostgres.AddDatabase("homunculy");

var homunculyMigrations = builder.AddContainer("homunculy-migrations", "liquibase/liquibase", "4.33.0")
    .WithBindMount("../../homunculy-db/changelog", "/liquibase/changelog")
    .WithEnvironment("LIQUIBASE_COMMAND_CHANGELOG_FILE", "changelog/db.changelog-master.xml")
    .WithEnvironment("LIQUIBASE_COMMAND_URL", "jdbc:postgresql://homunculy-postgres:5432/homunculy")
    .WithEnvironment("LIQUIBASE_COMMAND_USERNAME", "postgres")
    .WithEnvironment("LIQUIBASE_COMMAND_PASSWORD", homunculyDbPassword)
    .WithArgs("update")
    .WaitFor(homunculyPostgres);

var homunculyApp = builder.AddContainer("homunculy-app", "homunculy-app")
    .WithDockerfile("../../homunculy", "Dockerfile")
    .WithHttpEndpoint(port: 8000, targetPort: 8000, name: "http")
    .WithEnvironment("APP_HOST", "0.0.0.0")
    .WithEnvironment("APP_PORT", "8000")
    .WithEnvironment("APP_DEBUG", "false")
    .WithEnvironment("DB_HOST", "homunculy-postgres")
    .WithEnvironment("DB_PORT", "5432")
    .WithEnvironment("DB_NAME", "homunculy")
    .WithEnvironment("DB_USER", "postgres")
    .WithEnvironment("DB_PASSWORD", homunculyDbPassword)
    .WithEnvironment("LLM_PROVIDER", "openai")
    .WithEnvironment("LLM_OPENAI_API_KEY", openaiApiKey)
    .WithEnvironment("LLM_DEFAULT_MODEL", "gpt-4o-mini")
    .WithEnvironment("LLM_DEFAULT_TEMPERATURE", "0.7")
    .WithEnvironment("LLM_DEFAULT_MAX_TOKENS", "2000")
    .WithEnvironment("TTS_PROVIDER", "elevenlabs")
    .WithEnvironment("ELEVENLABS_API_KEY", elevenLabsApiKey)
    .WithEnvironment("TTS_ELEVENLABS_API_KEY", elevenLabsApiKey)
    .WithEnvironment("TTS_ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
    .WithEnvironment("TTS_ELEVENLABS_STREAMING_MODEL_ID", "eleven_turbo_v2_5")
    .WithEnvironment("RAG_SERVICE_URL", ragService.GetEndpoint("http"))
    .WithEnvironment("LOGGING_LEVEL", "INFO")
    .WithEnvironment("LOGGING_FORMAT", "json")
    .WithBindMount("../../homunculy/logs", "/app/logs")
    .WithExternalHttpEndpoints()
    .WaitFor(homunculyMigrations)
    .WaitFor(ragService);

// Management Stack (Go/Fiber + PostgreSQL)
var managementPostgres = builder.AddPostgres("management-postgres", password: managementDbPassword)
    .WithDataVolume("management-postgres-data");
    
var managementDb = managementPostgres.AddDatabase("management");

var managementMigrations = builder.AddContainer("management-migrations", "liquibase/liquibase", "4.33.0")
    .WithBindMount("../../management-service-db/changelog", "/liquibase/changelog")
    .WithEnvironment("LIQUIBASE_COMMAND_CHANGELOG_FILE", "changelog/db.changelog-master.xml")
    .WithEnvironment("LIQUIBASE_COMMAND_URL", "jdbc:postgresql://management-postgres:5432/management")
    .WithEnvironment("LIQUIBASE_COMMAND_USERNAME", "postgres")
    .WithEnvironment("LIQUIBASE_COMMAND_PASSWORD", managementDbPassword)
    .WithArgs("update")
    .WaitFor(managementPostgres);

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
    .WithExternalHttpEndpoints()
    .WaitFor(managementMigrations)
    .WaitFor(homunculyApp);

// Chat Clients
var chatClientWeb = builder.AddProject<Projects.ChatClient_Presentation_Web>("chat-client-web")
    .WithExternalHttpEndpoints()
    .WaitFor(homunculyApp)
    .WithEnvironment("ConnectionStrings__homunculy-app", homunculyApp.GetEndpoint("http"));

var mauiApp = builder.AddMauiProject("chat-client-maui", @"../../chat-client/src/ChatClient.Presentation.Maui/ChatClient.Presentation.Maui.csproj");
mauiApp.AddWindowsDevice();

builder.Build().Run();
