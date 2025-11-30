namespace ChatClient.Domain.Entities;

/// <summary>
/// Immutable chat message entity.
/// </summary>
public sealed record ChatMessage
{
    public required string Id { get; init; }
    public required string Content { get; init; }
    public required MessageRole Role { get; init; }
    public required DateTimeOffset Timestamp { get; init; }
    public bool IsStreaming { get; init; }
    public bool HasAudio { get; init; }

    public ChatMessage WithContent(string content) =>
        this with { Content = content };

    public ChatMessage WithStreaming(bool streaming) =>
        this with { IsStreaming = streaming };

    public ChatMessage WithAudio(bool hasAudio) =>
        this with { HasAudio = hasAudio };
}

/// <summary>
/// Message sender role.
/// </summary>
public enum MessageRole
{
    User,
    Assistant,
    System
}
