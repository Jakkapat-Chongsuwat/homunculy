namespace ChatClient.Domain.Exceptions;

/// <summary>
/// Base exception for all chat-related errors.
/// </summary>
public abstract class ChatException : Exception
{
    public string Code { get; }

    protected ChatException(string code, string message) 
        : base(message)
    {
        Code = code;
    }

    protected ChatException(string code, string message, Exception inner) 
        : base(message, inner)
    {
        Code = code;
    }
}

/// <summary>
/// Thrown when WebSocket connection fails.
/// </summary>
public sealed class ConnectionException : ChatException
{
    public int AttemptCount { get; }

    public ConnectionException(string message, int attemptCount = 1)
        : base("CONNECTION_FAILED", message)
    {
        AttemptCount = attemptCount;
    }

    public ConnectionException(string message, Exception inner)
        : base("CONNECTION_FAILED", message, inner)
    {
        AttemptCount = 1;
    }
}

/// <summary>
/// Thrown when sending a message fails.
/// </summary>
public sealed class SendException : ChatException
{
    public SendException(string message)
        : base("SEND_FAILED", message) { }

    public SendException(string message, Exception inner)
        : base("SEND_FAILED", message, inner) { }
}

/// <summary>
/// Thrown when receiving data fails.
/// </summary>
public sealed class ReceiveException : ChatException
{
    public ReceiveException(string message)
        : base("RECEIVE_FAILED", message) { }

    public ReceiveException(string message, Exception inner)
        : base("RECEIVE_FAILED", message, inner) { }
}

/// <summary>
/// Thrown when connection times out.
/// </summary>
public sealed class TimeoutException : ChatException
{
    public TimeSpan Timeout { get; }

    public TimeoutException(TimeSpan timeout)
        : base("TIMEOUT", $"Operation timed out after {timeout.TotalSeconds}s")
    {
        Timeout = timeout;
    }
}
