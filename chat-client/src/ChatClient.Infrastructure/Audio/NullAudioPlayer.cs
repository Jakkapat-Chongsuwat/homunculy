using ChatClient.Domain.Abstractions;

namespace ChatClient.Infrastructure.Audio;

/// <summary>
/// No-op audio player for unsupported platforms.
/// </summary>
public sealed class NullAudioPlayer : IAudioPlayer
{
    public bool IsEnabled => false;

    public Task InitializeAsync() => Task.CompletedTask;

    public void Queue(byte[] audioData) { }

    public void Flush() { }

    public void Stop() { }

    public void Reset() { }

    public void Clear() { }

    public void Dispose() { }
}
