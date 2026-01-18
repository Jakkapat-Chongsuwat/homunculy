using System.Collections.ObjectModel;
using System.Reactive.Linq;
using System.Reactive.Subjects;
using ChatClient.Application.Configuration;
using ChatClient.Domain.Abstractions;
using ChatClient.Domain.Entities;
using ChatClient.Domain.Events;
using ChatClient.Domain.ValueObjects;

namespace ChatClient.Application.ViewModels;

/// <summary>
/// Chat ViewModel - MVVM pattern with Reactive Extensions.
/// </summary>
public sealed class ChatViewModel : ViewModelBase
{
    private readonly IWebSocketClient _client;
    private readonly IAudioPlayer _audio;
    private readonly ILogService _log;
    private readonly ChatSettings _settings;

    private readonly BehaviorSubject<ConnectionState> _connectionState;
    private readonly BehaviorSubject<bool> _isProcessing;
    private readonly BehaviorSubject<string> _currentInput;
    private readonly Subject<ChatMessage> _messageAdded;

    private ChatMessage? _currentAssistantMessage;

    public ChatViewModel(
        IWebSocketClient client,
        IAudioPlayer audio,
        ILogService log,
        ChatSettings settings)
    {
        _client = client;
        _audio = audio;
        _log = log;
        _settings = settings;

        _connectionState = new(Domain.ValueObjects.ConnectionState.Disconnected);
        _isProcessing = new(false);
        _currentInput = new(string.Empty);
        _messageAdded = new();

        Messages = [];

        SubscribeToEvents();
    }

    public ObservableCollection<ChatMessage> Messages { get; }

    public IObservable<ConnectionState> ConnectionState =>
        _connectionState.AsObservable();

    public IObservable<bool> IsProcessing =>
        _isProcessing.AsObservable();

    public IObservable<bool> CanSend =>
        Observable.CombineLatest(
            _connectionState,
            _isProcessing,
            _currentInput,
            (state, processing, input) =>
                state == Domain.ValueObjects.ConnectionState.Connected &&
                !processing &&
                !string.IsNullOrWhiteSpace(input));

    public IObservable<ChatMessage> MessageAdded =>
        _messageAdded.AsObservable();

    public string CurrentInput
    {
        get => _currentInput.Value;
        set => _currentInput.OnNext(value);
    }

    public async Task ConnectAsync(CancellationToken ct = default)
    {
        _log.Information("Connecting to server...");
        await _client.ConnectAsync(ct);
    }

    public async Task SendMessageAsync(CancellationToken ct = default)
    {
        var message = GetTrimmedInput();
        if (message is null) return;
        PrepareSend(message);
        await _client.SendAsync(message, ct);
    }

    private string? GetTrimmedInput() =>
        string.IsNullOrWhiteSpace(CurrentInput) ? null : CurrentInput.Trim();

    private void PrepareSend(string message)
    {
        ClearInput();
        ResetAudio();
        AddUserMessage(message);
        CreateAssistantPlaceholder();
        SetProcessing(true);
    }

    private void ClearInput() =>
        CurrentInput = string.Empty;

    private void ResetAudio() =>
        _audio.Reset();

    private void SetProcessing(bool value) =>
        _isProcessing.OnNext(value);

    public async Task DisconnectAsync(CancellationToken ct = default)
    {
        _log.Information("Disconnecting...");
        await _client.DisconnectAsync(ct);
    }

    private void SubscribeToEvents()
    {
        var subscription = _client.Events.Subscribe(HandleEvent);
        AddDisposable(subscription);
    }

    private void HandleEvent(ChatEvent evt)
    {
        switch (evt)
        {
            case ConnectionStateChanged e:
                HandleConnectionState(e);
                break;
            case TextChunkReceived e:
                HandleTextChunk(e);
                break;
            case AudioChunkReceived e:
                HandleAudioChunk(e);
                break;
            case ResponseCompleted:
                HandleComplete();
                break;
            case ResponseInterrupted:
                HandleInterrupted();
                break;
            case ErrorOccurred e:
                HandleError(e);
                break;
            case StatusMessageReceived e:
                HandleStatus(e);
                break;
        }
    }

    private void HandleConnectionState(ConnectionStateChanged e)
    {
        _connectionState.OnNext(e.State);
        _log.Information("Connection state: {State}", e.State);
    }

    private void HandleTextChunk(TextChunkReceived e)
    {
        if (_currentAssistantMessage is null) return;
        UpdateAssistantContent(e.Chunk);
    }

    private void HandleAudioChunk(AudioChunkReceived e)
    {
        _log.Information("Audio chunk received: {Length} bytes", e.Data.Length);
        if (_currentAssistantMessage is null) return;
        MarkAssistantHasAudio();
        _audio.Queue(e.Data);
    }

    private void HandleComplete()
    {
        FinalizeAssistantMessage();
        _audio.Flush();
        SetProcessing(false);
    }

    private void HandleInterrupted()
    {
        AppendInterruptedMarker();
        _audio.Clear();
        SetProcessing(false);
    }

    private void HandleError(ErrorOccurred e)
    {
        _log.Error("Chat error: {Message}", e.Message);
        AddSystemMessage($"Error: {e.Message}");
        FinalizeAssistantMessage();
        SetProcessing(false);
    }

    private void HandleStatus(StatusMessageReceived e)
    {
        _log.Information("Status: {Message}", e.Message);
        AddSystemMessage(e.Message);
    }

    private void AddUserMessage(string content) =>
        AddMessage(CreateMessage(content, MessageRole.User));

    private void AddSystemMessage(string content) =>
        AddMessage(CreateMessage(content, MessageRole.System));

    private void CreateAssistantPlaceholder()
    {
        _currentAssistantMessage = CreateMessage(
            string.Empty,
            MessageRole.Assistant,
            isStreaming: true);
        AddMessage(_currentAssistantMessage);
    }

    private void UpdateAssistantContent(string chunk)
    {
        UpdateAssistant(
            message => message.WithContent(message.Content + chunk),
            clear: false);
    }

    private void MarkAssistantHasAudio()
    {
        UpdateAssistant(message => message.WithAudio(true), clear: false);
    }

    private void FinalizeAssistantMessage()
    {
        UpdateAssistant(message => message.WithStreaming(false), clear: true);
    }

    private void AppendInterruptedMarker()
    {
        UpdateAssistant(
            message => message
                .WithContent(message.Content + " [Interrupted]")
                .WithStreaming(false),
            clear: true);
    }

    private void UpdateAssistant(Func<ChatMessage, ChatMessage> update, bool clear)
    {
        if (!TryGetAssistantIndex(out var index)) return;
        _currentAssistantMessage = update(_currentAssistantMessage!);
        Messages[index] = _currentAssistantMessage;
        if (clear) _currentAssistantMessage = null;
    }

    private bool TryGetAssistantIndex(out int index)
    {
        index = _currentAssistantMessage is null
            ? -1
            : Messages.IndexOf(_currentAssistantMessage);
        return index >= 0;
    }

    private void AddMessage(ChatMessage message)
    {
        Messages.Add(message);
        _messageAdded.OnNext(message);
    }

    private static ChatMessage CreateMessage(
        string content,
        MessageRole role,
        bool isStreaming = false) => new()
    {
        Id = Guid.NewGuid().ToString(),
        Content = content,
        Role = role,
        Timestamp = DateTimeOffset.Now,
        IsStreaming = isStreaming
    };

    protected override void Dispose(bool disposing)
    {
        if (disposing)
        {
            _connectionState.Dispose();
            _isProcessing.Dispose();
            _currentInput.Dispose();
            _messageAdded.Dispose();
        }
        base.Dispose(disposing);
    }
}
