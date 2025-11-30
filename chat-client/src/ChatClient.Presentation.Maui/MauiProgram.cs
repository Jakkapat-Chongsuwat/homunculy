using ChatClient.Infrastructure;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Serilog;

namespace ChatClient.Presentation.Maui;

/// <summary>
/// MAUI application entry point with Aspire integration.
/// 
/// Configuration Priority (highest to lowest):
/// 1. Aspire service discovery (automatic when run from AppHost)
/// 2. Environment variables (OTEL_*, service endpoints)
/// 3. appsettings.json (embedded resource)
/// 4. Default fallback values
/// 
/// Platforms:
/// - Windows/Mac: Connect directly via localhost (service discovery)
/// - iOS/Android: Use Dev Tunnels (configured in AppHost)
/// </summary>
public static class MauiProgram
{
    public static MauiApp CreateMauiApp()
    {
        var builder = MauiApp.CreateBuilder();

        ConfigureApp(builder);
        ConfigureLogging(builder);
        
        // Add Aspire service defaults (service discovery, resilience, telemetry)
        builder.AddServiceDefaults();
        
        ConfigureServices(builder);

        return builder.Build();
    }

    private static void ConfigureApp(MauiAppBuilder builder)
    {
        builder
            .UseMauiApp<App>()
            .ConfigureFonts(fonts =>
            {
                fonts.AddFont("OpenSans-Regular.ttf", "OpenSansRegular");
            });
    }

    private static void ConfigureLogging(MauiAppBuilder builder)
    {
        var logDirectory = Path.Combine(
            FileSystem.Current.AppDataDirectory,
            "logs");
        
        Directory.CreateDirectory(logDirectory);
        
        var logPath = Path.Combine(logDirectory, "chatclient-maui-.log");

        Log.Logger = new LoggerConfiguration()
            .MinimumLevel.Debug()
            .Enrich.FromLogContext()
            .Enrich.WithProperty("Application", "ChatClient.Maui")
            .WriteTo.File(
                logPath,
                rollingInterval: RollingInterval.Day,
                outputTemplate: "{Timestamp:yyyy-MM-dd HH:mm:ss.fff zzz} [{Level:u3}] {Message:lj}{NewLine}{Exception}")
#if DEBUG
            .WriteTo.Debug(
                outputTemplate: "[{Timestamp:HH:mm:ss} {Level:u3}] {Message:lj}{NewLine}{Exception}")
#endif
            .CreateLogger();

        Log.Information("Starting ChatClient MAUI - Logs at: {LogPath}", logPath);
        builder.Logging.AddSerilog(Log.Logger);

#if DEBUG
        builder.Logging.AddDebug();
#endif
    }

    private static void ConfigureServices(MauiAppBuilder builder)
    {
        builder.Services.AddMauiBlazorWebView();

#if DEBUG
        builder.Services.AddBlazorWebViewDeveloperTools();
#endif

        // Get server URI from Aspire service discovery or configuration
        // Service name "homunculy-app" matches the name in AppHost
        var homunculyEndpoint = builder.Configuration.GetConnectionString("homunculy-app")
            ?? builder.Configuration["services:homunculy-app:http:0"]
            ?? "http://localhost:8000";
        
        // Convert HTTP endpoint to WebSocket endpoint
        var wsEndpoint = homunculyEndpoint
            .Replace("https://", "wss://")
            .Replace("http://", "ws://")
            .TrimEnd('/') + "/api/v1/ws/chat";

        Log.Information("Connecting to Homunculy at: {Endpoint}", wsEndpoint);

        builder.Services.AddChatClient(settings =>
        {
            settings.ServerUri = wsEndpoint;
            settings.UserId = Guid.NewGuid().ToString();
            settings.EnableAudio = true;
        });
    }
}
