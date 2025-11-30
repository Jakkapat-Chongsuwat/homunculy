using ChatClient.Domain.Events;
using ChatClient.Domain.ValueObjects;

namespace ChatClient.Domain.Abstractions;

/// <summary>
/// WebSocket client abstraction.
/// </summary>
public interface IWebSocketClient : IAsyncDisposable
{
    /// <summary>
    /// Current connection state.
    /// </summary>
    ConnectionState State { get; }

    /// <summary>
    /// Observable stream of chat events.
    /// </summary>
    IObservable<ChatEvent> Events { get; }

    /// <summary>
    /// Connect to the server.
    /// </summary>
    Task<bool> ConnectAsync(CancellationToken ct = default);

    /// <summary>
    /// Send a text message.
    /// </summary>
    Task SendAsync(string message, CancellationToken ct = default);

    /// <summary>
    /// Disconnect from the server.
    /// </summary>
    Task DisconnectAsync(CancellationToken ct = default);
}
