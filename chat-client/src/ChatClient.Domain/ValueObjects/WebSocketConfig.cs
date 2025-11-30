namespace ChatClient.Domain.ValueObjects;

/// <summary>
/// WebSocket connection configuration (immutable).
/// </summary>
public sealed record WebSocketConfig
{
    public TimeSpan ConnectTimeout { get; init; } = TimeSpan.FromSeconds(30);
    public TimeSpan PingInterval { get; init; } = TimeSpan.FromSeconds(15);
    public TimeSpan ReconnectBaseDelay { get; init; } = TimeSpan.FromSeconds(1);
    public TimeSpan ReconnectMaxDelay { get; init; } = TimeSpan.FromSeconds(30);
    public TimeSpan KeepAliveInterval { get; init; } = TimeSpan.FromSeconds(30);
    public TimeSpan PongTimeout { get; init; } = TimeSpan.FromSeconds(10);
    public int MaxReconnectAttempts { get; init; } = int.MaxValue;
    public int ReceiveBufferSize { get; init; } = 8192;
    public bool InfiniteReconnect { get; init; } = true;

    /// <summary>
    /// Default configuration optimized for mobile networks.
    /// - Infinite reconnect attempts
    /// - Faster ping to detect disconnects
    /// - Aggressive keepalive
    /// </summary>
    public static WebSocketConfig Default => new();

    /// <summary>
    /// Conservative config for stable connections.
    /// </summary>
    public static WebSocketConfig Stable => new()
    {
        PingInterval = TimeSpan.FromSeconds(30),
        KeepAliveInterval = TimeSpan.FromSeconds(60),
        MaxReconnectAttempts = 10,
        InfiniteReconnect = false
    };
}
