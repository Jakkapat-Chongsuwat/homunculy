using ChatClient.Domain.ValueObjects;

namespace ChatClient.Infrastructure.WebSocket;

/// <summary>
/// Calculates reconnection delays with exponential backoff.
/// Single Responsibility: Retry delay calculation.
/// </summary>
internal sealed class ReconnectStrategy
{
    private readonly WebSocketConfig _config;
    private int _attempts;
    private bool _preventReconnect;

    public ReconnectStrategy(WebSocketConfig config)
    {
        _config = config;
    }

    public int Attempts => _attempts;
    
    public bool CanRetry => !_preventReconnect && 
        (_config.InfiniteReconnect || _attempts < _config.MaxReconnectAttempts);
    
    public int MaxAttempts => _config.InfiniteReconnect 
        ? int.MaxValue 
        : _config.MaxReconnectAttempts;

    public void Reset()
    {
        _attempts = 0;
        _preventReconnect = false;
    }

    public void RecordAttempt() => _attempts++;

    public TimeSpan GetNextDelay()
    {
        // Cap exponential growth at reasonable level
        var cappedAttempts = Math.Min(_attempts - 1, 10);
        
        var exponentialMs = _config.ReconnectBaseDelay.TotalMilliseconds 
            * Math.Pow(2, cappedAttempts);
        
        var jitter = Random.Shared.NextDouble() * 0.3 * exponentialMs;
        
        var totalMs = Math.Min(
            exponentialMs + jitter,
            _config.ReconnectMaxDelay.TotalMilliseconds);

        return TimeSpan.FromMilliseconds(totalMs);
    }

    public void PreventAutoReconnect() => _preventReconnect = true;
}
