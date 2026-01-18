using ChatClient.Presentation.Web.Services;
using MudBlazor.Services;
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

    builder.Services.AddMudServices();
    builder.Services.Configure<LiveKitSettings>(
        builder.Configuration.GetSection("ChatClient:LiveKit"));
    builder.Services.AddHttpClient();
    builder.Services.AddScoped<LiveKitService>();

    // Debug: Log all connection strings
    var allConnStrings = builder.Configuration.GetSection("ConnectionStrings").GetChildren();
    foreach (var cs in allConnStrings)
    {
        Log.Information("ConnectionString [{Key}] = {Value}", cs.Key, cs.Value);
    }

    var aspireEndpoint = ResolveServiceHttp(builder.Configuration, "homunculy-app");
    ConfigureLiveKit(builder, aspireEndpoint);
}

static void ConfigureLiveKit(WebApplicationBuilder builder, string homunculyHttp)
{
    var livekitHttp = ResolveServiceHttp(builder.Configuration, "livekit");
    var managementHttp = ResolveServiceHttp(builder.Configuration, "management-app");
    var livekitWs = string.IsNullOrWhiteSpace(livekitHttp)
        ? string.Empty
        : livekitHttp.Replace("https://", "wss://").Replace("http://", "ws://");

    builder.Services.Configure<LiveKitSettings>(options =>
    {
        if (!IsAbsolute(options.Url) && !string.IsNullOrWhiteSpace(livekitWs))
            options.Url = livekitWs;

        if (!IsAbsolute(options.TokenEndpoint) && !string.IsNullOrWhiteSpace(managementHttp))
            options.TokenEndpoint = $"{managementHttp}/api/v1/livekit/token";

        if (!IsAbsolute(options.TokenEndpoint) && !string.IsNullOrWhiteSpace(homunculyHttp))
            options.TokenEndpoint = $"{homunculyHttp}/api/v1/livekit/token";
    });
}

static string ResolveServiceHttp(IConfiguration config, string name)
{
    var http = config[$"services:{name}:http:0"];
    if (IsAbsolute(http)) return http!.TrimEnd('/');

    var conn = config.GetConnectionString(name);
    return IsAbsolute(conn) ? conn!.TrimEnd('/') : string.Empty;
}

static bool IsAbsolute(string? value) =>
    Uri.TryCreate(value, UriKind.Absolute, out _);

static void ConfigurePipeline(WebApplication app)
{
    app.UseSerilogRequestLogging();

    var pathBase = app.Configuration["PATH_BASE"] ?? Environment.GetEnvironmentVariable("PATH_BASE");
    if (!string.IsNullOrWhiteSpace(pathBase) && pathBase != "/")
    {
        if (!pathBase.StartsWith('/'))
        {
            pathBase = "/" + pathBase;
        }

        app.UsePathBase(pathBase);
    }
    
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
