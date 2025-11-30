using Microsoft.Extensions.Logging;
using ChatClient.Domain.Abstractions;

namespace ChatClient.Infrastructure.Logging;

/// <summary>
/// Structured logging implementation.
/// </summary>
public sealed class LogService : ILogService
{
    private readonly ILogger _logger;

    public LogService(ILogger<LogService> logger) =>
        _logger = logger;

    public void Debug(string message, params object[] args) =>
        _logger.LogDebug(message, args);

    public void Information(string message, params object[] args) =>
        _logger.LogInformation(message, args);

    public void Warning(string message, params object[] args) =>
        _logger.LogWarning(message, args);

    public void Error(string message, params object[] args) =>
        _logger.LogError(message, args);

    public void Error(Exception ex, string message, params object[] args) =>
        _logger.LogError(ex, message, args);
}
