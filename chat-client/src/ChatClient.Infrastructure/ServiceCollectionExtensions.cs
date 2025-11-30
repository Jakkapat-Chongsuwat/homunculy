using Microsoft.Extensions.DependencyInjection;
using ChatClient.Application.Configuration;
using ChatClient.Application.ViewModels;
using ChatClient.Domain.Abstractions;
using ChatClient.Infrastructure.Audio;
using ChatClient.Infrastructure.Logging;
using ChatClient.Infrastructure.WebSocket;

namespace ChatClient.Infrastructure;

/// <summary>
/// Dependency injection extensions.
/// </summary>
public static class ServiceCollectionExtensions
{
    /// <summary>
    /// Add chat client services with NullAudioPlayer.
    /// </summary>
    public static IServiceCollection AddChatClient(
        this IServiceCollection services,
        Action<ChatSettings>? configure = null)
    {
        var settings = ConfigureSettings(configure);
        return RegisterServices(services, settings);
    }

    /// <summary>
    /// Add chat client services with WebAudioPlayer for browser.
    /// </summary>
    public static IServiceCollection AddChatClientWithWebAudio(
        this IServiceCollection services,
        Action<ChatSettings>? configure = null)
    {
        var settings = ConfigureSettings(configure);
        RegisterCoreServices(services, settings);
        services.AddScoped<IAudioPlayer, WebAudioPlayer>();
        services.AddTransient<ChatViewModel>();
        return services;
    }

    private static ChatSettings ConfigureSettings(Action<ChatSettings>? configure)
    {
        var settings = new ChatSettings();
        configure?.Invoke(settings);
        return settings;
    }

    private static IServiceCollection RegisterServices(
        IServiceCollection services,
        ChatSettings settings)
    {
        RegisterCoreServices(services, settings);
        services.AddSingleton<IAudioPlayer, NullAudioPlayer>();
        services.AddTransient<ChatViewModel>();
        return services;
    }

    private static void RegisterCoreServices(
        IServiceCollection services,
        ChatSettings settings)
    {
        services.AddSingleton(settings);
        services.AddSingleton<ILogService, LogService>();
        services.AddScoped<IWebSocketClient, WebSocketClient>();
    }
}
