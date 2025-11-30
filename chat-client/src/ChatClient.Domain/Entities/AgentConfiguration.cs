namespace ChatClient.Domain.Entities;

/// <summary>
/// Agent configuration settings.
/// </summary>
public sealed record AgentConfiguration
{
    public required string Provider { get; init; }
    public required string ModelName { get; init; }
    public required string VoiceId { get; init; }
    public required string SystemPrompt { get; init; }
    public required double Temperature { get; init; }
    public required int MaxTokens { get; init; }
    public required AgentPersonality Personality { get; init; }
}
