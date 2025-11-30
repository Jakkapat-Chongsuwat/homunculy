using System.Net.WebSockets;
using ChatClient.Domain.Exceptions;
using ChatClient.Domain.ValueObjects;

namespace ChatClient.Infrastructure.WebSocket;

/// <summary>
/// Manages WebSocket connection lifecycle.
/// Single Responsibility: Connect, disconnect, and maintain socket state.
/// </summary>
internal sealed class SocketConnection : IAsyncDisposable
{
    private readonly WebSocketConfig _config;
    private ClientWebSocket? _socket;
    private CancellationTokenSource? _cts;

    public SocketConnection(WebSocketConfig config)
    {
        _config = config;
    }

    public ClientWebSocket? Socket => _socket;
    public bool IsOpen => _socket?.State == WebSocketState.Open;
    public CancellationToken Token => _cts?.Token ?? CancellationToken.None;

    public async Task ConnectAsync(Uri uri, CancellationToken ct)
    {
        await ((IAsyncDisposable)this).DisposeAsync();

        _cts = CancellationTokenSource.CreateLinkedTokenSource(ct);
        _socket = new ClientWebSocket();
        _socket.Options.KeepAliveInterval = _config.KeepAliveInterval;

        using var timeoutCts = new CancellationTokenSource(_config.ConnectTimeout);
        using var linked = CancellationTokenSource.CreateLinkedTokenSource(
            _cts.Token, timeoutCts.Token);

        try
        {
            await _socket.ConnectAsync(uri, linked.Token);
        }
        catch (OperationCanceledException) when (timeoutCts.IsCancellationRequested)
        {
            throw new Domain.Exceptions.TimeoutException(_config.ConnectTimeout);
        }
    }

    public async Task CloseAsync()
    {
        if (_socket?.State == WebSocketState.Open)
        {
            try
            {
                await _socket.CloseAsync(
                    WebSocketCloseStatus.NormalClosure,
                    "Closing",
                    CancellationToken.None);
            }
            catch
            {
                // Ignore close errors
            }
        }
    }

    async ValueTask IAsyncDisposable.DisposeAsync()
    {
        await CleanupAsync();
    }

    private async Task CleanupAsync()
    {
        if (_cts is not null)
        {
            await _cts.CancelAsync();
            _cts.Dispose();
            _cts = null;
        }

        if (_socket is not null)
        {
            await CloseAsync();
            _socket.Dispose();
            _socket = null;
        }
    }
}
