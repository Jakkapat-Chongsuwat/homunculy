using System.Net.Http.Json;
using Microsoft.Extensions.Options;
using Microsoft.JSInterop;
using Microsoft.Extensions.Logging;

namespace ChatClient.Presentation.Web.Services;

/// <summary>
/// LiveKit JS interop + token client.
/// </summary>
public sealed class LiveKitService
{
    private readonly IJSRuntime _js;
    private readonly HttpClient _http;
    private readonly LiveKitSettings _settings;
    private readonly ILogger<LiveKitService> _log;

    public LiveKitService(
        IJSRuntime js,
        IHttpClientFactory httpFactory,
        IOptions<LiveKitSettings> options,
        ILogger<LiveKitService> log)
    {
        _js = js;
        _http = httpFactory.CreateClient();
        _settings = options.Value;
        _log = log;
    }

    public async Task<bool> ConnectAsync(string room, string identity, bool enableMic)
    {
        if (!_settings.IsConfigured)
            return FailConfig();
        
        // Disconnect first if already connected
        try
        {
            if (await IsConnectedAsync())
                await DisconnectAsync();
        }
        catch
        {
            // Ignore - may not be initialized
        }
        
        var token = await GetTokenAsync(room, identity);
        await _js.InvokeVoidAsync("livekitInterop.connect", _settings.Url, token);
        await SetMicEnabledAsync(enableMic);
        return true;
    }

    public async Task DisconnectAsync()
    {
        try
        {
            await _js.InvokeVoidAsync("livekitInterop.disconnect");
        }
        catch (JSException ex) when (ex.Message.Contains("Client initiated disconnect"))
        {
            // Expected when disconnecting - ignore
        }
    }

    public Task SetMicEnabledAsync(bool enabled) =>
        _js.InvokeVoidAsync("livekitInterop.setMicEnabled", enabled).AsTask();

    public async Task<bool> IsConnectedAsync() =>
        await _js.InvokeAsync<bool>("livekitInterop.isConnected");

    public Task SendTextAsync(string message) =>
        _js.InvokeVoidAsync("livekitInterop.sendText", message).AsTask();

    public ValueTask RegisterMessageHandlerAsync<T>(DotNetObjectReference<T> reference)
        where T : class =>
        _js.InvokeVoidAsync("livekitInterop.registerMessageHandler", reference);

    public ValueTask UnregisterMessageHandlerAsync() =>
        _js.InvokeVoidAsync("livekitInterop.unregisterMessageHandler");

    private async Task<string> GetTokenAsync(string room, string identity)
    {
        var endpoint = _settings.TokenEndpoint;
        if (!Uri.IsWellFormedUriString(endpoint, UriKind.Absolute))
            throw new InvalidOperationException($"TokenEndpoint must be an absolute URI: {endpoint}");

        var request = new TokenRequest(room, identity, 3600);
        var response = await _http.PostAsJsonAsync(new Uri(endpoint), request);
        return await ReadTokenAsync(response);
    }

    private async Task<string> ReadTokenAsync(HttpResponseMessage response)
    {
        response.EnsureSuccessStatusCode();
        var payload = await response.Content.ReadFromJsonAsync<TokenResponse>();
        if (payload is null) throw new InvalidOperationException("Token response empty");
        return payload.Token;
    }

    private bool FailConfig()
    {
        _log.LogWarning("LiveKit config missing");
        return false;
    }

    private sealed record TokenRequest(string Room, string Identity, int Ttl);
    private sealed record TokenResponse(string Token, string Room, string Identity);
}
