using Aspire.Hosting;
using Aspire.Hosting.ApplicationModel;

var builder = CreateBuilder(args);

var urls = BuildUrls();
var homunculySecrets = AddHomunculySecrets(builder);
var managementSecrets = AddManagementSecrets(builder);

var homunculyPostgres = AddHomunculyPostgres(builder, homunculySecrets.DbPassword);
var homunculyMigrations = AddHomunculyMigrations(builder, homunculyPostgres, homunculySecrets.DbPassword);
var homunculyApp = AddHomunculyApp(builder, homunculySecrets, urls, homunculyMigrations);

AddChatClientWeb(builder, urls, homunculyApp);

var managementPostgres = AddManagementPostgres(builder, managementSecrets.DbPassword);
var managementMigrations = AddManagementMigrations(builder, managementPostgres, managementSecrets.DbPassword);
AddManagementApp(builder, urls, managementSecrets.DbPassword, managementMigrations, homunculyApp);

builder.Build().Run();

static IDistributedApplicationBuilder CreateBuilder(string[] args)
{
    var builder = DistributedApplication.CreateBuilder(args);
    builder.Configuration["ASPIRE_ALLOW_UNSECURED_TRANSPORT"] = "true";
    return builder;
}

static Urls BuildUrls()
    => new(
        "http://homunculy-app:8000",
        "http://management-app:8080");

static HomunculySecrets AddHomunculySecrets(IDistributedApplicationBuilder builder)
    => new(
        builder.AddParameter("homunculy-db-password", secret: true),
        builder.AddParameter("openai-api-key", secret: true),
        builder.AddParameter("elevenlabs-api-key", secret: true));

static ManagementSecrets AddManagementSecrets(IDistributedApplicationBuilder builder)
    => new(builder.AddParameter("management-db-password", secret: true));

//

static IResourceBuilder<PostgresServerResource> AddHomunculyPostgres(
    IDistributedApplicationBuilder builder,
    IResourceBuilder<ParameterResource> password)
{
    var postgres = builder.AddPostgres("homunculy-postgres", password: password)
        .WithDataVolume("homunculy-postgres-data")
        .WithPgAdmin();
    postgres.AddDatabase("homunculy");
    return postgres;
}

static IResourceBuilder<ContainerResource> AddHomunculyMigrations(
    IDistributedApplicationBuilder builder,
    IResourceBuilder<PostgresServerResource> postgres,
    IResourceBuilder<ParameterResource> password)
    => builder.AddContainer("homunculy-migrations", "liquibase/liquibase", "4.33.0")
        .WithBindMount("../../homunculy-db/changelog", "/liquibase/changelog")
        .WithEnvironment("LIQUIBASE_COMMAND_CHANGELOG_FILE", "changelog/db.changelog-master.xml")
        .WithEnvironment("LIQUIBASE_COMMAND_URL", "jdbc:postgresql://homunculy-postgres:5432/homunculy")
        .WithEnvironment("LIQUIBASE_COMMAND_USERNAME", "postgres")
        .WithEnvironment("LIQUIBASE_COMMAND_PASSWORD", password)
        .WithArgs("update")
        .WaitFor(postgres);

static IResourceBuilder<ContainerResource> AddHomunculyApp(
    IDistributedApplicationBuilder builder,
    HomunculySecrets secrets,
    Urls urls,
    IResourceBuilder<ContainerResource> migrations)
{
    return builder.AddContainer("homunculy-app", "homunculy-app")
        .WithDockerfile("../../homunculy", "Dockerfile")
        .WithHttpEndpoint(port: 8000, targetPort: 8000, name: "health")
        .WithEnvironment("DB_HOST", "homunculy-postgres")
        .WithEnvironment("DB_PORT", "5432")
        .WithEnvironment("DB_NAME", "homunculy")
        .WithEnvironment("DB_USER", "postgres")
        .WithEnvironment("DB_PASSWORD", secrets.DbPassword)
        .WithEnvironment("LLM_PROVIDER", "openai")
        .WithEnvironment("LLM_OPENAI_API_KEY", secrets.OpenaiApiKey)
        .WithEnvironment("LLM_DEFAULT_MODEL", "gpt-4o-mini")
        .WithEnvironment("LLM_DEFAULT_TEMPERATURE", "0.7")
        .WithEnvironment("LLM_DEFAULT_MAX_TOKENS", "2000")
        .WithEnvironment("TTS_PROVIDER", "elevenlabs")
        .WithEnvironment("ELEVEN_API_KEY", secrets.ElevenLabsApiKey)
        .WithEnvironment("TTS_ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
        .WithEnvironment("TTS_ELEVENLABS_STREAMING_MODEL_ID", "eleven_turbo_v2_5")
        .WithEnvironment("TTS_DEFAULT_VOICE_ID", "lhTvHflPVOqgSWyuWQry")
        .WithEnvironment("HEALTH_PORT", "8000")
        //
        .WithEnvironment("OPENAI_API_KEY", secrets.OpenaiApiKey)
        .WithEnvironment("LOGGING_LEVEL", "DEBUG")
        .WithEnvironment("LOGGING_FORMAT", "json")
        .WithBindMount("../../homunculy/logs", "/app/logs")
        .WithContainerRuntimeArgs("--add-host=host.docker.internal:host-gateway")
        .WithOtlpExporter(OtlpProtocol.HttpProtobuf)
        .WaitFor(migrations)
        ;
}

static IResourceBuilder<ContainerResource> AddChatClientWeb(
    IDistributedApplicationBuilder builder,
    Urls urls,
    IResourceBuilder<ContainerResource> homunculyApp)
    => builder.AddContainer("chat-client-web", "chat-client-web")
        .WithDockerfile("../..", "chat-client/Dockerfile")
        .WithHttpEndpoint(port: 5000, targetPort: 5000, name: "http")
        .WithEnvironment("ASPNETCORE_URLS", "http://+:5000")
        .WithEnvironment("ASPNETCORE_ENVIRONMENT", "Development")
        .WithContainerRuntimeArgs("--add-host=host.docker.internal:host-gateway")
        .WithOtlpExporter(OtlpProtocol.HttpProtobuf)
        .WithEnvironment("ConnectionStrings__homunculy-app", urls.HomunculyUrl)
        .WithEnvironment("ChatClient__ServerUri", urls.HomunculyUrl)
        //
        .WithExternalHttpEndpoints()
        .WaitFor(homunculyApp);

static IResourceBuilder<PostgresServerResource> AddManagementPostgres(
    IDistributedApplicationBuilder builder,
    IResourceBuilder<ParameterResource> password)
{
    var postgres = builder.AddPostgres("management-postgres", password: password)
        .WithDataVolume("management-postgres-data");
    postgres.AddDatabase("management");
    return postgres;
}

static IResourceBuilder<ContainerResource> AddManagementMigrations(
    IDistributedApplicationBuilder builder,
    IResourceBuilder<PostgresServerResource> postgres,
    IResourceBuilder<ParameterResource> password)
    => builder.AddContainer("management-migrations", "liquibase/liquibase", "4.33.0")
        .WithBindMount("../../management-service-db/changelog", "/liquibase/changelog")
        .WithEnvironment("LIQUIBASE_COMMAND_CHANGELOG_FILE", "changelog/db.changelog-master.xml")
        .WithEnvironment("LIQUIBASE_COMMAND_URL", "jdbc:postgresql://management-postgres:5432/management")
        .WithEnvironment("LIQUIBASE_COMMAND_USERNAME", "postgres")
        .WithEnvironment("LIQUIBASE_COMMAND_PASSWORD", password)
        .WithArgs("update")
        .WaitFor(postgres);

static IResourceBuilder<ContainerResource> AddManagementApp(
    IDistributedApplicationBuilder builder,
    Urls urls,
    IResourceBuilder<ParameterResource> password,
    IResourceBuilder<ContainerResource> migrations,
    IResourceBuilder<ContainerResource> homunculyApp)
    => builder.AddContainer("management-app", "management-app")
        .WithDockerfile("../../management-service", "Dockerfile")
        .WithHttpEndpoint(port: 8080, targetPort: 8080, name: "http")
        .WithEnvironment("SERVER_HOST", "0.0.0.0")
        .WithEnvironment("SERVER_PORT", "8080")
        //
        .WithEnvironment("DB_HOST", "management-postgres")
        .WithEnvironment("DB_PORT", "5432")
        .WithEnvironment("DB_NAME", "management")
        .WithEnvironment("DB_USER", "postgres")
        .WithEnvironment("DB_PASSWORD", password)
        .WithEnvironment("DB_SSL_MODE", "disable")
        .WithEnvironment("HOMUNCULY_BASE_URL", urls.HomunculyUrl)
        .WithEnvironment("HOMUNCULY_API_KEY", "dev_api_key_123")
        //
        .WithContainerRuntimeArgs("--add-host=host.docker.internal:host-gateway")
        .WithOtlpExporter(OtlpProtocol.HttpProtobuf)
        .WithExternalHttpEndpoints()
        .WaitFor(migrations)
        .WaitFor(homunculyApp);

record Urls(
    string HomunculyUrl,
    string ManagementUrl);

record HomunculySecrets(
    IResourceBuilder<ParameterResource> DbPassword,
    IResourceBuilder<ParameterResource> OpenaiApiKey,
    IResourceBuilder<ParameterResource> ElevenLabsApiKey);

record ManagementSecrets(IResourceBuilder<ParameterResource> DbPassword);

#if false
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
    .WithEnvironment("OPENAI_API_KEY", homunculySecrets.OpenaiApiKey)
    .WithEnvironment("EMBEDDING_MODEL", "text-embedding-3-small")
    .WithEnvironment("RAG_CHUNK_SIZE", "512")
    .WithEnvironment("RAG_TOP_K", "5")
    .WithEnvironment("OTEL_EXPORTER_OTLP_ENDPOINT", "http://host.docker.internal:4317")
    .WithEnvironment("OTEL_SERVICE_NAME", "rag-service")
    .WithEnvironment("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
    .WithExternalHttpEndpoints()
    .WaitFor(pineconeLocal);

var mauiApp = builder.AddMauiProject(
    "chat-client-maui",
    @"../../chat-client/src/ChatClient.Presentation.Maui/ChatClient.Presentation.Maui.csproj");
mauiApp.AddWindowsDevice();
#endif
