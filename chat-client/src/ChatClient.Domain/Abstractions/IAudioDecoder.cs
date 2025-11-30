namespace ChatClient.Domain.Abstractions;

/// <summary>
/// Decodes compressed audio to raw PCM.
/// </summary>
public interface IAudioDecoder
{
    /// <summary>
    /// Decode audio data to PCM format.
    /// </summary>
    byte[] Decode(byte[] audioData);

    /// <summary>
    /// Whether the decoder is available.
    /// </summary>
    bool IsAvailable { get; }
}
