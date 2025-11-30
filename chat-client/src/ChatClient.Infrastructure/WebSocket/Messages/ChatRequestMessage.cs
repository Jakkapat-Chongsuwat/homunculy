using System.Text.Json.Serialization;

namespace ChatClient.Infrastructure.WebSocket.Messages;

/// <summary>
/// Chat request message.
/// </summary>
internal sealed record ChatRequestMessage
{
    [JsonPropertyName("type")]
    public string Type => "chat_request";

    [JsonPropertyName("user_id")]
    public required string UserId { get; init; }

    [JsonPropertyName("message")]
    public required string Message { get; init; }

    [JsonPropertyName("configuration")]
    public required ConfigurationMessage Configuration { get; init; }

    [JsonPropertyName("context")]
    public Dictionary<string, object> Context { get; init; } = [];

    [JsonPropertyName("stream_audio")]
    public bool StreamAudio { get; init; }

    [JsonPropertyName("voice_id")]
    public string? VoiceId { get; init; }
}

/// <summary>
/// Configuration section of request.
/// </summary>
internal sealed record ConfigurationMessage
{
    [JsonPropertyName("provider")]
    public required string Provider { get; init; }

    [JsonPropertyName("model_name")]
    public required string ModelName { get; init; }

    [JsonPropertyName("personality")]
    public required PersonalityMessage Personality { get; init; }

    [JsonPropertyName("system_prompt")]
    public required string SystemPrompt { get; init; }

    [JsonPropertyName("temperature")]
    public double Temperature { get; init; }

    [JsonPropertyName("max_tokens")]
    public int MaxTokens { get; init; }
}

/// <summary>
/// Personality section of request.
/// </summary>
internal sealed record PersonalityMessage
{
    [JsonPropertyName("name")]
    public required string Name { get; init; }

    [JsonPropertyName("description")]
    public required string Description { get; init; }

    [JsonPropertyName("traits")]
    public Dictionary<string, object> Traits { get; init; } = [];

    [JsonPropertyName("mood")]
    public required string Mood { get; init; }
}
