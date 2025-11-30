using ChatClient.Domain.Abstractions;
using Microsoft.JSInterop;

namespace ChatClient.Infrastructure.Audio;

/// <summary>
/// Web Audio API player via JavaScript interop.
/// Safe to call before Blazor circuit is established.
/// </summary>
public sealed class WebAudioPlayer : IAudioPlayer, IAsyncDisposable
{
    private readonly IJSRuntime _js;
    private readonly ILogService _log;
    private bool _initialized;
    private bool _circuitReady;

    public WebAudioPlayer(IJSRuntime js, ILogService log)
    {
        _js = js;
        _log = log;
    }

    public bool IsEnabled => _initialized && _circuitReady;

    public void Queue(byte[] audioData)
    {
        var base64 = Convert.ToBase64String(audioData);
        _ = EnqueueAsync(base64);
    }

    public void Flush() =>
        _ = SafeInvokeAsync("flush");

    public void Stop() =>
        _ = SafeInvokeAsync("stop");

    public void Reset() =>
        _ = SafeInvokeAsync("reset");

    public void Clear() =>
        _ = SafeInvokeAsync("clear");

    /// <summary>
    /// Marks the circuit as ready and initializes audio.
    /// Call this from OnAfterRenderAsync(firstRender).
    /// </summary>
    public async Task InitializeAsync()
    {
        _circuitReady = true;

        try
        {
            _initialized = await InvokeAsync<bool>("initialize");
            LogInitResult();
        }
        catch (Exception ex)
        {
            _circuitReady = false;
            LogInitError(ex);
        }
    }

    private void LogInitResult()
    {
        if (_initialized)
            _log.Information("Web audio initialized");
        else
            _log.Warning("Web audio unavailable");
    }

    private void LogInitError(Exception ex) =>
        _log.Error(ex, "Web audio init failed");

    private async Task EnqueueAsync(string base64)
    {
        if (!_circuitReady) return;
        
        if (!_initialized)
            await InitializeAsync();
        
        if (!_initialized) return;
        
        await InvokeVoidAsync("enqueue", base64);
    }

    private async Task SafeInvokeAsync(string method)
    {
        if (!_circuitReady) return;
        await InvokeVoidAsync(method);
    }

    private async Task InvokeVoidAsync(string method, params object[] args)
    {
        try
        {
            await _js.InvokeVoidAsync($"audioPlayerInterop.{method}", args);
        }
        catch (JSDisconnectedException)
        {
            _circuitReady = false;
        }
        catch (InvalidOperationException ex) when (ex.Message.Contains("prerender") || 
                                                     ex.Message.Contains("statically"))
        {
            _circuitReady = false;
        }
        catch (Exception ex)
        {
            _log.Error(ex, "Audio interop failed: {Method}", method);
        }
    }

    private async Task<T> InvokeAsync<T>(string method, params object[] args)
    {
        try
        {
            return await _js.InvokeAsync<T>($"audioPlayerInterop.{method}", args);
        }
        catch (JSDisconnectedException)
        {
            _circuitReady = false;
            return default!;
        }
        catch (InvalidOperationException ex) when (ex.Message.Contains("prerender") || 
                                                     ex.Message.Contains("statically"))
        {
            _circuitReady = false;
            return default!;
        }
        catch (Exception ex)
        {
            _log.Error(ex, "Audio interop failed: {Method}", method);
            return default!;
        }
    }

    public void Dispose() { }

    public async ValueTask DisposeAsync()
    {
        if (_circuitReady)
            await SafeInvokeAsync("stop");
    }
}
