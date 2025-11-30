namespace ChatClient.Domain.Entities;

/// <summary>
/// Agent personality configuration.
/// </summary>
public sealed record AgentPersonality
{
    public required string Name { get; init; }
    public required string Description { get; init; }
    public required string Mood { get; init; }
}
