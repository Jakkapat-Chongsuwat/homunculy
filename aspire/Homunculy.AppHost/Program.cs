using Aspire.Hosting.ApplicationModel;

var builder = DistributedApplication.CreateBuilder(args);

// Secrets
var homunculyDbPassword = builder.AddParameter("homunculy-db-password", secret: true);
var openaiApiKey = builder.AddParameter("openai-api-key", secret: true);
var elevenLabsApiKey = builder.AddParameter("elevenlabs-api-key", secret: true);
var livekitApiKey = builder.AddParameter("livekit-api-key", secret: true);
var livekitApiSecret = builder.AddParameter("livekit-api-secret", secret: true);

// Container network URLs
const string livekitWsInternal = "ws://livekit:7880";
const string livekitWsExternal = "ws://localhost:7880";
const string homunculyUrl = "http://homunculy-app:8000";
const string managementUrl = "http://management-app:8080";
const string livekitDevKey = "devkey";
const string livekitDevSecret = "devsecretdevsecretdevsecretdevsecret";

// LiveKit
var livekit = builder.AddContainer("livekit", "livekit/livekit-server", "v1.9.11")
    .WithBindMount("../../infra/livekit/livekit.yaml", "/livekit.yaml")
    .WithArgs("--config", "/livekit.yaml")
    .WithHttpEndpoint(port: 7880, targetPort: 7880, name: "http")
    .WithEndpoint(port: 7881, targetPort: 7881, name: "rtc-tcp")
    .WithEndpoint(port: 50000, targetPort: 50000, name: "rtc-udp", protocol: System.Net.Sockets.ProtocolType.Udp)
    .WithExternalHttpEndpoints();

// PostgreSQL + pgAdmin
var homunculyPostgres = builder.AddPostgres("homunculy-postgres", password: homunculyDbPassword)
    .WithDataVolume("homunculy-postgres-data")
    .WithPgAdmin();
var homunculyDb = homunculyPostgres.AddDatabase("homunculy");

// Migrations
var homunculyMigrations = builder.AddContainer("homunculy-migrations", "liquibase/liquibase", "4.33.0")
    .WithBindMount("../../homunculy-db/changelog", "/liquibase/changelog")
    .WithEnvironment("LIQUIBASE_COMMAND_CHANGELOG_FILE", "changelog/db.changelog-master.xml")
    .WithEnvironment("LIQUIBASE_COMMAND_URL", "jdbc:postgresql://homunculy-postgres:5432/homunculy")
    .WithEnvironment("LIQUIBASE_COMMAND_USERNAME", "postgres")
    .WithEnvironment("LIQUIBASE_COMMAND_PASSWORD", homunculyDbPassword)
    .WithArgs("update")
    .WaitFor(homunculyPostgres);

// Homunculy API
var homunculyApp = builder.AddContainer("homunculy-app", "homunculy-app")
    .WithDockerfile("../../homunculy", "Dockerfile")
    .WithHttpEndpoint(port: 8000, targetPort: 8000, name: "health")
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
    .WithEnvironment("ELEVEN_API_KEY", elevenLabsApiKey)  // Single source - aliased in code
    .WithEnvironment("TTS_ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
    .WithEnvironment("TTS_ELEVENLABS_STREAMING_MODEL_ID", "eleven_turbo_v2_5")
    .WithEnvironment("TTS_DEFAULT_VOICE_ID", "lhTvHflPVOqgSWyuWQry")  // Custom voice
    .WithEnvironment("LIVEKIT_URL", livekitWsInternal)
    // Use livekit-worker transport for proper agent framework integration
    .WithEnvironment("AGENT_TRANSPORT", "livekit-worker")
    .WithEnvironment("AGENT_NAME", "homunculy-super")
    .WithEnvironment("HEALTH_PORT", "8000")
    .WithEnvironment("LIVEKIT_API_KEY", livekitDevKey)
    .WithEnvironment("LIVEKIT_API_SECRET", livekitDevSecret)
    .WithEnvironment("OPENAI_API_KEY", openaiApiKey)
    .WithEnvironment("LOGGING_LEVEL", "DEBUG")
    .WithEnvironment("LOGGING_FORMAT", "json")
    .WithBindMount("../../homunculy/logs", "/app/logs")
    .WaitFor(homunculyMigrations)
    .WaitFor(livekit);

// Chat Client (Blazor)
var chatClientWeb = builder.AddContainer("chat-client-web", "chat-client-web")
    .WithDockerfile("../..", "chat-client/Dockerfile")
    .WithHttpEndpoint(port: 5000, targetPort: 5000, name: "http")
    .WithEnvironment("ASPNETCORE_URLS", "http://+:5000")
    .WithEnvironment("ASPNETCORE_ENVIRONMENT", "Development")
    .WithEnvironment("ConnectionStrings__homunculy-app", homunculyUrl)
    .WithEnvironment("ChatClient__ServerUri", homunculyUrl)
    .WithEnvironment("ChatClient__LiveKit__Url", livekitWsExternal)
    .WithEnvironment("ChatClient__LiveKit__TokenEndpoint", $"{managementUrl}/api/v1/livekit/token")
    .WithExternalHttpEndpoints()
    .WaitFor(homunculyApp);

// --- Management Stack ---
var managementDbPassword = builder.AddParameter("management-db-password", secret: true);

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
    .WithEnvironment("LIVEKIT_HOST", "http://livekit:7880")
    .WithEnvironment("DB_HOST", "management-postgres")
    .WithEnvironment("DB_PORT", "5432")
    .WithEnvironment("DB_NAME", "management")
    .WithEnvironment("DB_USER", "postgres")
    .WithEnvironment("DB_PASSWORD", managementDbPassword)
    .WithEnvironment("DB_SSL_MODE", "disable")
    .WithEnvironment("HOMUNCULY_BASE_URL", homunculyUrl)
    .WithEnvironment("HOMUNCULY_API_KEY", "dev_api_key_123")
    .WithEnvironment("LIVEKIT_API_KEY", livekitDevKey)
    .WithEnvironment("LIVEKIT_API_SECRET", livekitDevSecret)
    .WithEnvironment("LIVEKIT_TOKEN_TTL", "3600")
    .WithExternalHttpEndpoints()
    .WaitFor(managementMigrations)
    .WaitFor(homunculyApp);

builder.Build().Run();

// =============================================================================
// DISABLED SERVICES (uncomment when needed)
// =============================================================================
#if false

// --- RAG Stack ---
var ragServiceUrl = "http://rag-service:8001";

var pineconeLocal = builder.AddContainer("pinecone-local", "ghcr.io/pinecone-io/pinecone-index", "latest")
    .WithHttpEndpoint(port: 5081, targetPort: 5081, name: "grpc")
    .WithEnvironment("PORT", "5081")
    .WithEnvironment("INDEX_TYPE", "serverless")
    .WithEnvironment("DIMENSION", "1536")
    .WithEnvironment("METRIC", "cosine")
    .WithVolume("pinecone-local-data", "/data");

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

// Add to homunculyApp: .WithEnvironment("RAG_SERVICE_URL", ragServiceUrl).WaitFor(ragService)

// --- MAUI Client ---
var mauiApp = builder.AddMauiProject("chat-client-maui", @"../../chat-client/src/ChatClient.Presentation.Maui/ChatClient.Presentation.Maui.csproj");
mauiApp.AddWindowsDevice();

#endif
