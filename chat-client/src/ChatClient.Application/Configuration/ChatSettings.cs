using ChatClient.Domain.Entities;

namespace ChatClient.Application.Configuration;

/// <summary>
/// Chat client configuration settings .
/// </summary>
public sealed class ChatSettings
{
    public string ServerUri { get; set; } = "ws://localhost:8000/api/v1/ws/chat";
    public string WebSocketUri => ServerUri;
    public string UserId { get; set; } = "User";
    public bool EnableAudio { get; set; } = true;
    public bool AudioEnabled => EnableAudio;
    public AgentConfiguration Agent { get; init; } = DefaultAgent;

    private static AgentConfiguration DefaultAgent => new()
    {
        Provider = "langraph",
        ModelName = "gpt-4o-mini",
        VoiceId = "lhTvHflPVOqgSWyuWQry",
        Temperature = 0.7,
        MaxTokens = 500,
        SystemPrompt = DefaultSystemPrompt,
        Personality = DefaultPersonality
    };

    private static AgentPersonality DefaultPersonality => new()
    {
        Name = "Homunculy",
        Description = "A friendly AI assistant",
        Mood = "cheerful"
    };

    private const string DefaultSystemPrompt =
        "You are Homunculy, a friendly AI assistant. " +
        "Respond directly to the user's message. Be concise. " +
        "Never summarize previous conversations. " +
        "If interrupted, just respond to the new message naturally.";
}
