using ChatClient.Infrastructure;
using Serilog;

Log.Logger = new LoggerConfiguration()
    .MinimumLevel.Debug()
    .WriteTo.Console()
    .CreateBootstrapLogger();

try
{
    var builder = WebApplication.CreateBuilder(args);
    ConfigureServices(builder);
    
    var app = builder.Build();
    ConfigurePipeline(app);
    app.Run();
}
catch (Exception ex)
{
    Log.Fatal(ex, "Application terminated unexpectedly");
}
finally
{
    Log.CloseAndFlush();
}

static void ConfigureServices(WebApplicationBuilder builder)
{
    // Serilog from config - can be changed at runtime
    var logPath = Path.Combine(AppContext.BaseDirectory, "logs", "chatclient-web-.log");
    
    builder.Host.UseSerilog((context, services, config) => config
        .MinimumLevel.Debug()
        .ReadFrom.Configuration(context.Configuration)
        .ReadFrom.Services(services)
        .Enrich.FromLogContext()
        .Enrich.WithProperty("Application", "ChatClient.Web")
        .WriteTo.Console(outputTemplate: "[{Timestamp:HH:mm:ss} {Level:u3}] {Message:lj}{NewLine}{Exception}")
        .WriteTo.File(logPath, rollingInterval: RollingInterval.Day,
            outputTemplate: "{Timestamp:yyyy-MM-dd HH:mm:ss.fff zzz} [{Level:u3}] {Message:lj}{NewLine}{Exception}"));

    Log.Information("Starting ChatClient Web - Logs at: {LogPath}", logPath);

    builder.AddServiceDefaults();

    builder.Services.AddRazorComponents()
        .AddInteractiveServerComponents();

    // Debug: Log all connection strings
    var allConnStrings = builder.Configuration.GetSection("ConnectionStrings").GetChildren();
    foreach (var cs in allConnStrings)
    {
        Log.Information("ConnectionString [{Key}] = {Value}", cs.Key, cs.Value);
    }

    var aspireEndpoint = builder.Configuration.GetConnectionString("homunculy-app");
    var configEndpoint = builder.Configuration["ChatClient:ServerUri"];
    
    string wsEndpoint;
    if (!string.IsNullOrEmpty(aspireEndpoint))
    {
        wsEndpoint = aspireEndpoint
            .Replace("https://", "wss://")
            .Replace("http://", "ws://")
            .TrimEnd('/') + "/api/v1/ws/chat";
        Log.Information("Using Aspire endpoint: {Aspire} -> {WebSocket}", aspireEndpoint, wsEndpoint);
    }
    else if (!string.IsNullOrEmpty(configEndpoint))
    {
        // Config already has full WebSocket URL with path
        wsEndpoint = configEndpoint;
        Log.Information("Using config endpoint: {WebSocket}", wsEndpoint);
    }
    else
    {
        wsEndpoint = "ws://localhost:8000/api/v1/ws/chat";
        Log.Warning("No endpoint configured, using default: {WebSocket}", wsEndpoint);
    }

    Log.Information("Connecting to Homunculy WebSocket at: {Endpoint}", wsEndpoint);

    builder.Services.AddChatClientWithWebAudio(settings =>
    {
        settings.ServerUri = wsEndpoint;
        settings.UserId = Guid.NewGuid().ToString();
        settings.EnableAudio = true;
    });
}

static void ConfigurePipeline(WebApplication app)
{
    app.UseSerilogRequestLogging();
    
    if (!app.Environment.IsDevelopment())
    {
        app.UseExceptionHandler("/Error");
        app.UseHsts();
    }

    app.UseHttpsRedirection();
    app.UseStaticFiles();
    app.UseAntiforgery();

    app.MapDefaultEndpoints();
    app.MapRazorComponents<ChatClient.Presentation.Web.Components.App>()
        .AddInteractiveServerRenderMode();
}
