namespace ChatClient.Domain.Events;

/// <summary>
/// Base class for all chat events.
/// </summary>
public abstract record ChatEvent
{
    public DateTimeOffset Timestamp { get; init; } = DateTimeOffset.UtcNow;
}

/// <summary>
/// Text chunk received from server.
/// </summary>
public sealed record TextChunkReceived(string Chunk) : ChatEvent;

/// <summary>
/// Audio chunk received from server.
/// </summary>
public sealed record AudioChunkReceived(byte[] Data) : ChatEvent;

/// <summary>
/// Response completed.
/// </summary>
public sealed record ResponseCompleted : ChatEvent;

/// <summary>
/// Response was interrupted.
/// </summary>
public sealed record ResponseInterrupted : ChatEvent;

/// <summary>
/// Error occurred.
/// </summary>
public sealed record ErrorOccurred(string Message) : ChatEvent;

/// <summary>
/// Connection state changed.
/// </summary>
public sealed record ConnectionStateChanged(
    ChatClient.Domain.ValueObjects.ConnectionState State) : ChatEvent;

/// <summary>
/// Status message received.
/// </summary>
public sealed record StatusMessageReceived(string Message) : ChatEvent;
