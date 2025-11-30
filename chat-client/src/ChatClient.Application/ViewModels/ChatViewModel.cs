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
        var message = CurrentInput.Trim();
        if (string.IsNullOrEmpty(message)) return;

        CurrentInput = string.Empty;
        ResetAudioForNewMessage();

        AddUserMessage(message);
        CreateAssistantPlaceholder();

        _isProcessing.OnNext(true);
        await _client.SendAsync(message, ct);
    }

    private void ResetAudioForNewMessage()
    {
        _audio.Reset();
    }

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
        if (_currentAssistantMessage is null) return;
        MarkAssistantHasAudio();
        _audio.Queue(e.Data);
    }

    private void HandleComplete()
    {
        FinalizeAssistantMessage();
        _audio.Flush();
        _isProcessing.OnNext(false);
    }

    private void HandleInterrupted()
    {
        AppendInterruptedMarker();
        _audio.Clear();
        _isProcessing.OnNext(false);
    }

    private void HandleError(ErrorOccurred e)
    {
        _log.Error("Chat error: {Message}", e.Message);
        AddSystemMessage($"Error: {e.Message}");
        FinalizeAssistantMessage();
        _isProcessing.OnNext(false);
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
        if (_currentAssistantMessage is null) return;
        var index = Messages.IndexOf(_currentAssistantMessage);
        if (index < 0) return;

        _currentAssistantMessage = _currentAssistantMessage
            .WithContent(_currentAssistantMessage.Content + chunk);
        Messages[index] = _currentAssistantMessage;
    }

    private void MarkAssistantHasAudio()
    {
        if (_currentAssistantMessage is null) return;
        var index = Messages.IndexOf(_currentAssistantMessage);
        if (index < 0) return;

        _currentAssistantMessage = _currentAssistantMessage.WithAudio(true);
        Messages[index] = _currentAssistantMessage;
    }

    private void FinalizeAssistantMessage()
    {
        if (_currentAssistantMessage is null) return;
        var index = Messages.IndexOf(_currentAssistantMessage);
        if (index < 0) return;

        _currentAssistantMessage = _currentAssistantMessage.WithStreaming(false);
        Messages[index] = _currentAssistantMessage;
        _currentAssistantMessage = null;
    }

    private void AppendInterruptedMarker()
    {
        if (_currentAssistantMessage is null) return;
        var index = Messages.IndexOf(_currentAssistantMessage);
        if (index < 0) return;

        _currentAssistantMessage = _currentAssistantMessage
            .WithContent(_currentAssistantMessage.Content + " [Interrupted]")
            .WithStreaming(false);
        Messages[index] = _currentAssistantMessage;
        _currentAssistantMessage = null;
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
