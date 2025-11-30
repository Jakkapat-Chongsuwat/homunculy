namespace ChatClient.Domain.Abstractions;

/// <summary>
/// Structured logging abstraction.
/// </summary>
public interface ILogService
{
    void Debug(string message, params object[] args);
    void Information(string message, params object[] args);
    void Warning(string message, params object[] args);
    void Error(string message, params object[] args);
    void Error(Exception ex, string message, params object[] args);
}
