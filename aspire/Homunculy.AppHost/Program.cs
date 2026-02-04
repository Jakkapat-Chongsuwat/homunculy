using Aspire.Hosting;
using Aspire.Hosting.ApplicationModel;

var builder = CreateBuilder(args);

var urls = GetUrls(builder);
var homunculySecrets = AddHomunculySecrets(builder);
var managementSecrets = AddManagementSecrets(builder);
var lineSettings = GetLineSettings(builder);
var homunculyEnv = GetHomunculyEnv(builder);
var managementEnv = GetManagementEnv(builder);
var chatClientEnv = GetChatClientEnv(builder, urls);

var homunculyPostgres = AddHomunculyPostgres(builder, homunculySecrets.DbPassword);
var homunculyMigrations = AddHomunculyMigrations(builder, homunculyPostgres, homunculySecrets.DbPassword);
var homunculyApp = AddHomunculyApp(
    builder,
    homunculySecrets,
    lineSettings,
    homunculyEnv,
    urls,
    homunculyMigrations);

AddChatClientWeb(builder, urls, chatClientEnv, homunculyApp);

var managementPostgres = AddManagementPostgres(builder, managementSecrets.DbPassword);
var managementMigrations = AddManagementMigrations(builder, managementPostgres, managementSecrets.DbPassword);
AddManagementApp(
    builder,
    urls,
    managementEnv,
    managementSecrets.DbPassword,
    managementMigrations,
    homunculyApp);

builder.Build().Run();

static IDistributedApplicationBuilder CreateBuilder(string[] args)
{
    var builder = DistributedApplication.CreateBuilder(args);
    builder.Configuration["ASPIRE_ALLOW_UNSECURED_TRANSPORT"] = "true";
    return builder;
}

static Urls GetUrls(IDistributedApplicationBuilder builder)
    => new(
        builder.Configuration["Urls:HomunculyUrl"] ?? "http://homunculy-app:8000",
        builder.Configuration["Urls:ManagementUrl"] ?? "http://management-app:8080");

static HomunculySecrets AddHomunculySecrets(IDistributedApplicationBuilder builder)
    => new(
        builder.AddParameter("homunculy-db-password", secret: true),
        builder.AddParameter("openai-api-key", secret: true),
        builder.AddParameter("elevenlabs-api-key", secret: true));
static LineSettings GetLineSettings(IDistributedApplicationBuilder builder)
    => new(
        builder.Configuration["Line:ChannelAccessToken"],
        builder.Configuration["Line:ChannelSecret"]);

static HomunculyEnv GetHomunculyEnv(IDistributedApplicationBuilder builder)
    => new(
        DbHost: builder.Configuration["Homunculy:DbHost"] ?? "homunculy-postgres",
        DbPort: builder.Configuration["Homunculy:DbPort"] ?? "5432",
        DbName: builder.Configuration["Homunculy:DbName"] ?? "homunculy",
        DbUser: builder.Configuration["Homunculy:DbUser"] ?? "postgres",
        LlmProvider: builder.Configuration["Homunculy:LlmProvider"] ?? "openai",
        LlmDefaultModel: builder.Configuration["Homunculy:LlmDefaultModel"] ?? "gpt-4o-mini",
        LlmDefaultTemperature: builder.Configuration["Homunculy:LlmDefaultTemperature"] ?? "0.7",
        LlmDefaultMaxTokens: builder.Configuration["Homunculy:LlmDefaultMaxTokens"] ?? "2000",
        TtsProvider: builder.Configuration["Homunculy:TtsProvider"] ?? "elevenlabs",
        TtsElevenlabsModelId: builder.Configuration["Homunculy:TtsElevenlabsModelId"]
            ?? "eleven_multilingual_v2",
        TtsElevenlabsStreamingModelId: builder.Configuration[
            "Homunculy:TtsElevenlabsStreamingModelId"
        ] ?? "eleven_turbo_v2_5",
        TtsDefaultVoiceId: builder.Configuration["Homunculy:TtsDefaultVoiceId"]
            ?? "lhTvHflPVOqgSWyuWQry",
        HealthPort: builder.Configuration["Homunculy:HealthPort"] ?? "8000",
        LoggingLevel: builder.Configuration["Homunculy:LoggingLevel"] ?? "DEBUG",
        LoggingFormat: builder.Configuration["Homunculy:LoggingFormat"] ?? "json");

static ManagementEnv GetManagementEnv(IDistributedApplicationBuilder builder)
    => new(
        ServerHost: builder.Configuration["Management:ServerHost"] ?? "0.0.0.0",
        ServerPort: builder.Configuration["Management:ServerPort"] ?? "8080",
        DbHost: builder.Configuration["Management:DbHost"] ?? "management-postgres",
        DbPort: builder.Configuration["Management:DbPort"] ?? "5432",
        DbName: builder.Configuration["Management:DbName"] ?? "management",
        DbUser: builder.Configuration["Management:DbUser"] ?? "postgres",
        DbSslMode: builder.Configuration["Management:DbSslMode"] ?? "disable",
        ApiKey: builder.Configuration["Management:ApiKey"] ?? "dev_api_key_123");

static ChatClientEnv GetChatClientEnv(IDistributedApplicationBuilder builder, Urls urls)
    => new(
        AspNetCoreUrls: builder.Configuration["ChatClient:AspNetCoreUrls"]
            ?? "http://+:5000",
        Environment: builder.Configuration["ChatClient:Environment"] ?? "Development",
        HomunculyUrl: builder.Configuration["ChatClient:HomunculyUrl"] ?? urls.HomunculyUrl);


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
    LineSettings line,
    HomunculyEnv env,
    Urls urls,
    IResourceBuilder<ContainerResource> migrations)
{
    return builder.AddContainer("homunculy-app", "homunculy-app")
        .WithDockerfile("../../homunculy", "Dockerfile")
        .WithHttpEndpoint(port: 8000, targetPort: 8000, name: "health")
        .WithEnvironment("DB_HOST", env.DbHost)
        .WithEnvironment("DB_PORT", env.DbPort)
        .WithEnvironment("DB_NAME", env.DbName)
        .WithEnvironment("DB_USER", env.DbUser)
        .WithEnvironment("DB_PASSWORD", secrets.DbPassword)
        .WithEnvironment("LLM_PROVIDER", env.LlmProvider)
        .WithEnvironment("LLM_OPENAI_API_KEY", secrets.OpenaiApiKey)
        .WithEnvironment("LLM_DEFAULT_MODEL", env.LlmDefaultModel)
        .WithEnvironment("LLM_DEFAULT_TEMPERATURE", env.LlmDefaultTemperature)
        .WithEnvironment("LLM_DEFAULT_MAX_TOKENS", env.LlmDefaultMaxTokens)
        .WithEnvironment("TTS_PROVIDER", env.TtsProvider)
        .WithEnvironment("ELEVEN_API_KEY", secrets.ElevenLabsApiKey)
        .WithEnvironment("TTS_ELEVENLABS_MODEL_ID", env.TtsElevenlabsModelId)
        .WithEnvironment(
            "TTS_ELEVENLABS_STREAMING_MODEL_ID",
            env.TtsElevenlabsStreamingModelId)
        .WithEnvironment("TTS_DEFAULT_VOICE_ID", env.TtsDefaultVoiceId)
        .WithEnvironment("HEALTH_PORT", env.HealthPort)
        //
        .WithEnvironment("OPENAI_API_KEY", secrets.OpenaiApiKey)
        .WithEnvironment("LINE_CHANNEL_ACCESS_TOKEN", line.ChannelAccessToken ?? string.Empty)
        .WithEnvironment("LINE_CHANNEL_SECRET", line.ChannelSecret ?? string.Empty)
        .WithEnvironment("LOGGING_LEVEL", env.LoggingLevel)
        .WithEnvironment("LOGGING_FORMAT", env.LoggingFormat)
        .WithBindMount("../../homunculy/logs", "/app/logs")
        .WithContainerRuntimeArgs("--add-host=host.docker.internal:host-gateway")
        .WithOtlpExporter(OtlpProtocol.HttpProtobuf)
        .WaitFor(migrations)
        ;
}

static IResourceBuilder<ContainerResource> AddChatClientWeb(
    IDistributedApplicationBuilder builder,
    Urls urls,
    ChatClientEnv env,
    IResourceBuilder<ContainerResource> homunculyApp)
    => builder.AddContainer("chat-client-web", "chat-client-web")
        .WithDockerfile("../..", "chat-client/Dockerfile")
        .WithHttpEndpoint(port: 5000, targetPort: 5000, name: "http")
        .WithEnvironment("ASPNETCORE_URLS", env.AspNetCoreUrls)
        .WithEnvironment("ASPNETCORE_ENVIRONMENT", env.Environment)
        .WithContainerRuntimeArgs("--add-host=host.docker.internal:host-gateway")
        .WithOtlpExporter(OtlpProtocol.HttpProtobuf)
        .WithEnvironment("ConnectionStrings__homunculy-app", env.HomunculyUrl)
        .WithEnvironment("ChatClient__ServerUri", env.HomunculyUrl)
        //
        .WithExternalHttpEndpoints()
        .WithExplicitStart()
        .WaitFor(homunculyApp);

static IResourceBuilder<PostgresServerResource> AddManagementPostgres(
    IDistributedApplicationBuilder builder,
    IResourceBuilder<ParameterResource> password)
{
    var postgres = builder.AddPostgres("management-postgres", password: password)
        .WithDataVolume("management-postgres-data")
        .WithExplicitStart();
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
        .WithExplicitStart()
        .WaitFor(postgres);

static IResourceBuilder<ContainerResource> AddManagementApp(
    IDistributedApplicationBuilder builder,
    Urls urls,
    ManagementEnv env,
    IResourceBuilder<ParameterResource> password,
    IResourceBuilder<ContainerResource> migrations,
    IResourceBuilder<ContainerResource> homunculyApp)
    => builder.AddContainer("management-app", "management-app")
        .WithDockerfile("../../management-service", "Dockerfile")
        .WithHttpEndpoint(port: 8080, targetPort: 8080, name: "http")
        .WithEnvironment("SERVER_HOST", env.ServerHost)
        .WithEnvironment("SERVER_PORT", env.ServerPort)
        //
        .WithEnvironment("DB_HOST", env.DbHost)
        .WithEnvironment("DB_PORT", env.DbPort)
        .WithEnvironment("DB_NAME", env.DbName)
        .WithEnvironment("DB_USER", env.DbUser)
        .WithEnvironment("DB_PASSWORD", password)
        .WithEnvironment("DB_SSL_MODE", env.DbSslMode)
        .WithEnvironment("HOMUNCULY_BASE_URL", urls.HomunculyUrl)
        .WithEnvironment("HOMUNCULY_API_KEY", env.ApiKey)
        //
        .WithContainerRuntimeArgs("--add-host=host.docker.internal:host-gateway")
        .WithOtlpExporter(OtlpProtocol.HttpProtobuf)
        .WithExternalHttpEndpoints()
        .WithExplicitStart()
        .WaitFor(migrations)
        .WaitFor(homunculyApp);

record Urls(
    string HomunculyUrl,
    string ManagementUrl);

record HomunculySecrets(
    IResourceBuilder<ParameterResource> DbPassword,
    IResourceBuilder<ParameterResource> OpenaiApiKey,
    IResourceBuilder<ParameterResource> ElevenLabsApiKey);

record LineSettings(
    string? ChannelAccessToken,
    string? ChannelSecret);

record HomunculyEnv(
    string DbHost,
    string DbPort,
    string DbName,
    string DbUser,
    string LlmProvider,
    string LlmDefaultModel,
    string LlmDefaultTemperature,
    string LlmDefaultMaxTokens,
    string TtsProvider,
    string TtsElevenlabsModelId,
    string TtsElevenlabsStreamingModelId,
    string TtsDefaultVoiceId,
    string HealthPort,
    string LoggingLevel,
    string LoggingFormat);

record ManagementEnv(
    string ServerHost,
    string ServerPort,
    string DbHost,
    string DbPort,
    string DbName,
    string DbUser,
    string DbSslMode,
    string ApiKey);

record ChatClientEnv(
    string AspNetCoreUrls,
    string Environment,
    string HomunculyUrl);

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
