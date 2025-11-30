namespace ChatClient.Domain.ValueObjects;

/// <summary>
/// Connection state value object.
/// </summary>
public enum ConnectionState
{
    Disconnected,
    Connecting,
    Connected,
    Reconnecting
}
