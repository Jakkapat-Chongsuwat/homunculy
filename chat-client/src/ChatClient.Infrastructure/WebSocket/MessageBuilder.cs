using ChatClient.Application.Configuration;
using ChatClient.Infrastructure.WebSocket.Messages;

namespace ChatClient.Infrastructure.WebSocket;

/// <summary>
/// Builds chat request messages.
/// </summary>
internal static class MessageBuilder
{
    public static ChatRequestMessage CreateRequest(
        ChatSettings settings,
        string message) => new()
    {
        UserId = settings.UserId,
        Message = message,
        StreamAudio = settings.AudioEnabled,
        VoiceId = settings.Agent.VoiceId,
        Configuration = CreateConfiguration(settings)
    };

    private static ConfigurationMessage CreateConfiguration(
        ChatSettings settings) => new()
    {
        Provider = settings.Agent.Provider,
        ModelName = settings.Agent.ModelName,
        SystemPrompt = settings.Agent.SystemPrompt,
        Temperature = settings.Agent.Temperature,
        MaxTokens = settings.Agent.MaxTokens,
        Personality = CreatePersonality(settings)
    };

    private static PersonalityMessage CreatePersonality(
        ChatSettings settings) => new()
    {
        Name = settings.Agent.Personality.Name,
        Description = settings.Agent.Personality.Description,
        Mood = settings.Agent.Personality.Mood
    };
}
