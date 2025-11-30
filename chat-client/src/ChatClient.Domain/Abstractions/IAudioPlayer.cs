namespace ChatClient.Domain.Abstractions;

/// <summary>
/// Audio player abstraction with buffering support.
/// </summary>
public interface IAudioPlayer : IDisposable
{
    /// <summary>
    /// Whether audio playback is enabled.
    /// </summary>
    bool IsEnabled { get; }

    /// <summary>
    /// Initialize the audio player.
    /// For web, call this after Blazor circuit is established.
    /// </summary>
    Task InitializeAsync();

    /// <summary>
    /// Queue audio data for playback.
    /// </summary>
    void Queue(byte[] audioData);

    /// <summary>
    /// Flush buffered audio to output.
    /// </summary>
    void Flush();

    /// <summary>
    /// Stop playback and clear queues.
    /// </summary>
    void Stop();

    /// <summary>
    /// Reset state for new message stream.
    /// </summary>
    void Reset();

    /// <summary>
    /// Clear all pending audio (interruption).
    /// </summary>
    void Clear();
}
