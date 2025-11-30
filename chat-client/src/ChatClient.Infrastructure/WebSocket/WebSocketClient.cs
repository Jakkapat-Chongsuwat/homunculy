using System.Net.WebSockets;
using System.Reactive.Linq;
using System.Reactive.Subjects;
using System.Text;
using System.Text.Json;
using ChatClient.Application.Configuration;
using ChatClient.Domain.Abstractions;
using ChatClient.Domain.Events;
using ChatClient.Domain.ValueObjects;

namespace ChatClient.Infrastructure.WebSocket;

/// <summary>
/// WebSocket client implementation.
/// </summary>
public sealed class WebSocketClient : IWebSocketClient
{
    private readonly ChatSettings _settings;
    private readonly ILogService _log;
    private readonly Subject<ChatEvent> _events;

    private ClientWebSocket? _socket;
    private CancellationTokenSource? _receiveCts;
    private Task? _receiveTask;

    public WebSocketClient(ChatSettings settings, ILogService log)
    {
        _settings = settings;
        _log = log;
        _events = new Subject<ChatEvent>();
    }

    public ConnectionState State { get; private set; } = ConnectionState.Disconnected;

    public IObservable<ChatEvent> Events => _events.AsObservable();

    public async Task<bool> ConnectAsync(CancellationToken ct = default)
    {
        if (State == ConnectionState.Connected)
            return true;

        try
        {
            return await DoConnectAsync(ct);
        }
        catch (Exception ex)
        {
            HandleConnectError(ex);
            return false;
        }
    }

    public async Task SendAsync(string message, CancellationToken ct = default)
    {
        if (!IsConnected())
        {
            EmitError("Not connected");
            return;
        }

        var request = MessageBuilder.CreateRequest(_settings, message);
        await SendJsonAsync(request, ct);
    }

    public async Task DisconnectAsync(CancellationToken ct = default)
    {
        await CancelReceiveLoop();
        await CloseSocketAsync();
        SetState(ConnectionState.Disconnected);
    }

    public async ValueTask DisposeAsync()
    {
        await DisconnectAsync();
        _events.Dispose();
        _receiveCts?.Dispose();
    }

    private async Task<bool> DoConnectAsync(CancellationToken ct)
    {
        SetState(ConnectionState.Connecting);

        _socket = new ClientWebSocket();
        await _socket.ConnectAsync(new Uri(_settings.WebSocketUri), ct);

        await ReceiveStatusAsync(ct);
        SetState(ConnectionState.Connected);

        StartReceiveLoop();
        return true;
    }

    private async Task ReceiveStatusAsync(CancellationToken ct)
    {
        var message = await ReceiveOneAsync(ct);
        var evt = MessageParser.Parse(message);

        if (evt is StatusMessageReceived status)
            _events.OnNext(status);
    }

    private void StartReceiveLoop()
    {
        _receiveCts = new CancellationTokenSource();
        _receiveTask = ReceiveLoopAsync(_receiveCts.Token);
    }

    private async Task ReceiveLoopAsync(CancellationToken ct)
    {
        var buffer = new StringBuilder();

        try
        {
            while (!ct.IsCancellationRequested && IsConnected())
            {
                var (data, endOfMessage) = await ReceiveChunkAsync(ct);

                buffer.Append(data);

                if (!endOfMessage) continue;

                ProcessMessage(buffer.ToString());
                buffer.Clear();
            }
        }
        catch (OperationCanceledException)
        {
            // Normal shutdown
        }
        catch (Exception ex)
        {
            HandleReceiveError(ex);
        }
    }

    private async Task<(string Data, bool EndOfMessage)> ReceiveChunkAsync(
        CancellationToken ct)
    {
        var buffer = new byte[8192];
        var result = await _socket!.ReceiveAsync(buffer, ct);

        if (result.MessageType == WebSocketMessageType.Close)
        {
            SetState(ConnectionState.Disconnected);
            return (string.Empty, true);
        }

        var data = Encoding.UTF8.GetString(buffer, 0, result.Count);
        return (data, result.EndOfMessage);
    }

    private async Task<string> ReceiveOneAsync(CancellationToken ct)
    {
        var buffer = new StringBuilder();

        while (true)
        {
            var (data, endOfMessage) = await ReceiveChunkAsync(ct);
            buffer.Append(data);

            if (endOfMessage)
                return buffer.ToString();
        }
    }

    private void ProcessMessage(string json)
    {
        var evt = MessageParser.Parse(json);

        if (evt is not null)
            _events.OnNext(evt);
    }

    private async Task SendJsonAsync<T>(T message, CancellationToken ct)
    {
        var json = JsonSerializer.Serialize(message);
        var bytes = Encoding.UTF8.GetBytes(json);
        var segment = new ArraySegment<byte>(bytes);

        await _socket!.SendAsync(segment, WebSocketMessageType.Text, true, ct);
    }

    private async Task CancelReceiveLoop()
    {
        if (_receiveCts is null) return;

        await _receiveCts.CancelAsync();

        if (_receiveTask is not null)
        {
            try { await _receiveTask; }
            catch (OperationCanceledException) { }
        }
    }

    private async Task CloseSocketAsync()
    {
        if (_socket?.State != WebSocketState.Open)
            return;

        await _socket.CloseAsync(
            WebSocketCloseStatus.NormalClosure,
            "Closing",
            CancellationToken.None);

        _socket.Dispose();
        _socket = null;
    }

    private bool IsConnected() =>
        _socket?.State == WebSocketState.Open;

    private void SetState(ConnectionState state)
    {
        State = state;
        _events.OnNext(new ConnectionStateChanged(state));
    }

    private void EmitError(string message) =>
        _events.OnNext(new ErrorOccurred(message));

    private void HandleConnectError(Exception ex)
    {
        _log.Error(ex, "Connection failed");
        EmitError($"Connection failed: {ex.Message}");
        SetState(ConnectionState.Disconnected);
    }

    private void HandleReceiveError(Exception ex)
    {
        _log.Error(ex, "Receive error");
        EmitError($"Receive error: {ex.Message}");
        SetState(ConnectionState.Disconnected);
    }
}
