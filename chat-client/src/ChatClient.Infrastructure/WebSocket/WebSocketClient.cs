using System.Reactive.Disposables;
using System.Reactive.Linq;
using System.Reactive.Subjects;
using ChatClient.Application.Configuration;
using ChatClient.Domain.Abstractions;
using ChatClient.Domain.Events;
using ChatClient.Domain.Exceptions;
using ChatClient.Domain.ValueObjects;

namespace ChatClient.Infrastructure.WebSocket;

/// <summary>
/// Reactive WebSocket client with automatic reconnection.
/// Composes small, focused components following SRP.
/// </summary>
public sealed class WebSocketClient : IWebSocketClient
{
    private readonly ChatSettings _settings;
    private readonly ILogService _log;
    private readonly WebSocketConfig _config;

    // Composed components (SRP)
    private readonly SocketConnection _connection;
    private readonly SocketReceiver _receiver;
    private readonly SocketSender _sender;
    private readonly ReconnectStrategy _reconnect;

    // Reactive state
    private readonly BehaviorSubject<ConnectionState> _state;
    private readonly Subject<ChatEvent> _events;
    private readonly CompositeDisposable _subscriptions;
    
    private IDisposable? _pingSubscription;
    private IDisposable? _receiveSubscription;
    private DateTime _lastPongReceived = DateTime.UtcNow;

    public WebSocketClient(ChatSettings settings, ILogService log)
        : this(settings, log, WebSocketConfig.Default) { }

    public WebSocketClient(ChatSettings settings, ILogService log, WebSocketConfig config)
    {
        _settings = settings;
        _log = log;
        _config = config;

        _connection = new SocketConnection(config);
        _receiver = new SocketReceiver(config);
        _sender = new SocketSender();
        _reconnect = new ReconnectStrategy(config);

        _state = new BehaviorSubject<ConnectionState>(ConnectionState.Disconnected);
        _events = new Subject<ChatEvent>();
        _subscriptions = new CompositeDisposable();

        WireStateToEvents();
    }

    public ConnectionState State => _state.Value;
    public IObservable<ChatEvent> Events => _events.AsObservable();

    public async Task<bool> ConnectAsync(CancellationToken ct = default)
    {
        if (State == ConnectionState.Connected)
            return true;

        _reconnect.Reset();
        return await RunConnectLoop(ct);
    }

    public async Task SendAsync(string message, CancellationToken ct = default)
    {
        if (!_connection.IsOpen)
        {
            EmitError("Not connected");
            return;
        }

        try
        {
            var request = MessageBuilder.CreateRequest(_settings, message);
            await _sender.SendJsonAsync(_connection, request, ct);
        }
        catch (Exception ex)
        {
            _log.Error(ex, "Send failed");
            EmitError($"Send failed: {ex.Message}");
            await HandleDisconnectAsync();
        }
    }

    public async Task DisconnectAsync(CancellationToken ct = default)
    {
        _reconnect.PreventAutoReconnect();
        await CleanupAsync();
        SetState(ConnectionState.Disconnected);
    }

    public async ValueTask DisposeAsync()
    {
        await DisconnectAsync();
        _subscriptions.Dispose();
        _state.Dispose();
        _events.Dispose();
    }

    private void WireStateToEvents()
    {
        var stateSubscription = _state
            .DistinctUntilChanged()
            .Select(s => new ConnectionStateChanged(s))
            .Subscribe(_events);

        _subscriptions.Add(stateSubscription);
    }

    private async Task<bool> ConnectWithRetryAsync(CancellationToken ct)
    {
        return await RunConnectLoop(ct);
    }

    private async Task<bool> RunConnectLoop(CancellationToken ct)
    {
        while (CanRetry(ct))
        {
            try
            {
                await ConnectOnce(ct);
                return true;
            }
            catch (OperationCanceledException) when (ct.IsCancellationRequested)
            {
                throw;
            }
            catch (Exception ex)
            {
                var delay = HandleConnectFailure(ex);
                if (delay == TimeSpan.Zero) return false;
                await Task.Delay(delay, ct);
            }
        }

        return false;
    }

    private bool CanRetry(CancellationToken ct) =>
        _reconnect.CanRetry && !ct.IsCancellationRequested;

    private async Task ConnectOnce(CancellationToken ct)
    {
        SetConnectingState();
        await EstablishConnectionAsync(ct);
        OnConnected();
    }

    private void SetConnectingState() =>
        SetState(_reconnect.Attempts == 0
            ? ConnectionState.Connecting
            : ConnectionState.Reconnecting);

    private void OnConnected()
    {
        _reconnect.Reset();
        SetState(ConnectionState.Connected);
        StartPingLoop();
        StartReceiveLoop();
    }

    private TimeSpan HandleConnectFailure(Exception ex)
    {
        _reconnect.RecordAttempt();
        if (!_reconnect.CanRetry) return StopRetry(ex);
        return LogRetry(ex);
    }

    private TimeSpan StopRetry(Exception ex)
    {
        _log.Error(ex, "Max reconnection attempts reached");
        EmitError($"Connection failed after {_reconnect.MaxAttempts} attempts");
        SetState(ConnectionState.Disconnected);
        return TimeSpan.Zero;
    }

    private TimeSpan LogRetry(Exception ex)
    {
        var delay = _reconnect.GetNextDelay();
        _log.Warning(
            "Attempt {N}/{Max} failed: {Error}. Retry in {Delay}ms",
            _reconnect.Attempts, _reconnect.MaxAttempts,
            ex.Message, delay.TotalMilliseconds);
        return delay;
    }

    private async Task EstablishConnectionAsync(CancellationToken ct)
    {
        var uri = new Uri(_settings.WebSocketUri);
        
        _log.Information("Connecting to {Uri}", uri);
        await _connection.ConnectAsync(uri, ct);

        var status = await _receiver.ReceiveOneAsync(_connection, ct);
        var evt = MessageParser.Parse(status);
        
        if (evt is StatusMessageReceived msg)
            _events.OnNext(msg);

        _log.Information("Connected successfully");
    }

    private void StartPingLoop()
    {
        _pingSubscription?.Dispose();
        _lastPongReceived = DateTime.UtcNow;
        
        _pingSubscription = Observable
            .Interval(_config.PingInterval)
            .Where(_ => _connection.IsOpen)
            .SelectMany(_ => SendPingAndCheckPong())
            .Subscribe();

        _subscriptions.Add(_pingSubscription);
    }

    private async Task<bool> SendPingAndCheckPong()
    {
        if (IsPongStale()) return await HandleDeadConnection();
        return await TrySendPing();
    }

    private bool IsPongStale()
    {
        var delta = DateTime.UtcNow - _lastPongReceived;
        return delta > _config.PongTimeout + _config.PingInterval;
    }

    private async Task<bool> HandleDeadConnection()
    {
        _log.Warning("No pong received in {Seconds}s, connection may be dead",
            (DateTime.UtcNow - _lastPongReceived).TotalSeconds);
        await HandleDisconnectAsync();
        return false;
    }

    private async Task<bool> TrySendPing()
    {
        try
        {
            await _sender.SendPingAsync(_connection, _connection.Token);
            return true;
        }
        catch
        {
            return false;
        }
    }

    private void StartReceiveLoop()
    {
        _receiveSubscription?.Dispose();

        _receiveSubscription = _receiver
            .CreateReceiveStream(_connection)
            .Subscribe(
                ProcessMessage,
                async ex => await OnReceiveError(ex),
                async () => await OnReceiveComplete());

        _subscriptions.Add(_receiveSubscription);
    }

    private void ProcessMessage(string json)
    {
        if (IsPong(json))
        {
            _lastPongReceived = DateTime.UtcNow;
            return;
        }

        var evt = MessageParser.Parse(json);
        if (evt is not null)
            _events.OnNext(evt);
    }

    private static bool IsPong(string json) =>
        json.Contains("\"type\":\"pong\"") || 
        json.Contains("\"type\": \"pong\"");

    private async Task OnReceiveError(Exception ex)
    {
        _log.Error(ex, "Receive error");
        EmitError($"Connection error: {ex.Message}");
        await HandleDisconnectAsync();
    }

    private async Task OnReceiveComplete()
    {
        _log.Information("Connection closed");
        await HandleDisconnectAsync();
    }

    private async Task HandleDisconnectAsync()
    {
        if (IsReconnecting()) return;
        var wasConnected = IsConnected();
        await CloseConnection(wasConnected);
        ScheduleReconnect();
    }

    private bool IsReconnecting() =>
        State == ConnectionState.Reconnecting;

    private bool IsConnected() =>
        State == ConnectionState.Connected;

    private async Task CloseConnection(bool wasConnected)
    {
        SetState(ConnectionState.Disconnected);
        await CleanupAsync();
        if (wasConnected) _reconnect.Reset();
    }

    private void ScheduleReconnect()
    {
        if (!_reconnect.CanRetry)
        {
            LogReconnectDisabled();
            return;
        }
        _log.Information("Auto-reconnecting...");
        _ = Task.Run(() => RunConnectLoop(CancellationToken.None));
    }

    private void LogReconnectDisabled() =>
        _log.Warning("Auto-reconnect disabled");

    private async Task CleanupAsync()
    {
        _pingSubscription?.Dispose();
        _pingSubscription = null;
        
        _receiveSubscription?.Dispose();
        _receiveSubscription = null;

        await _connection.CloseAsync();
    }

    private void SetState(ConnectionState state) => _state.OnNext(state);
    
    private void EmitError(string message) => _events.OnNext(new ErrorOccurred(message));
}
