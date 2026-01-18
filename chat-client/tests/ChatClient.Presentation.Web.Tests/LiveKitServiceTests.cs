using System;
using System.Net.Http;
using System.Threading.Tasks;
using Bunit;
using ChatClient.Presentation.Web.Services;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.Options;
using Moq;
using RichardSzalay.MockHttp;
using Xunit;

namespace ChatClient.Presentation.Web.Tests;

public sealed class LiveKitServiceTests : TestContext
{
    private readonly Mock<IHttpClientFactory> _httpFactoryMock = new();

    public LiveKitServiceTests()
    {
        // Allow unmatched JS calls to return default values instead of hanging
        JSInterop.Mode = JSRuntimeMode.Loose;
    }

    [Fact]
    public void IsConfigured_WhenBothSet_ReturnsTrue()
    {
        var s = new LiveKitSettings { Url = "ws://livekit:7880", TokenEndpoint = "http://api/token" };
        Assert.True(s.IsConfigured);
    }

    [Theory]
    [InlineData("", "http://api/token")]
    [InlineData("ws://livekit:7880", "")]
    [InlineData("", "")]
    public void IsConfigured_WhenMissing_ReturnsFalse(string url, string endpoint)
    {
        var s = new LiveKitSettings { Url = url, TokenEndpoint = endpoint };
        Assert.False(s.IsConfigured);
    }

    [Fact]
    public async Task ConnectAsync_WhenNotConfigured_ReturnsFalse()
    {
        var service = CreateService(new LiveKitSettings());
        Assert.False(await service.ConnectAsync("room", "user", true));
    }

    [Fact]
    public async Task ConnectAsync_WhenConfigured_CallsJsAndReturnsTrue()
    {
        var mockHttp = new MockHttpMessageHandler();
        var settings = ValidSettings();
        
        mockHttp.When(HttpMethod.Post, settings.TokenEndpoint)
            .Respond("application/json", """{"token":"t","room":"r","identity":"i"}""");
        mockHttp.Fallback.Throw(new InvalidOperationException("Unmocked HTTP request"));

        var service = CreateService(settings, mockHttp.ToHttpClient());

        Assert.True(await service.ConnectAsync("room", "user", true));
        JSInterop.VerifyInvoke("livekitInterop.connect", 1);
        JSInterop.VerifyInvoke("livekitInterop.setMicEnabled", 1);
    }

    [Fact]
    public async Task ConnectAsync_WithRelativeUrl_Throws()
    {
        var settings = new LiveKitSettings { Url = "ws://livekit:7880", TokenEndpoint = "/api/token" };
        var service = CreateService(settings);
        await Assert.ThrowsAsync<InvalidOperationException>(() => service.ConnectAsync("room", "user", true));
    }

    [Fact]
    public async Task DisconnectAsync_CallsJs()
    {
        var service = CreateService(ValidSettings());
        await service.DisconnectAsync();
        JSInterop.VerifyInvoke("livekitInterop.disconnect", 1);
    }

    [Fact]
    public async Task SetMicEnabledAsync_CallsJs()
    {
        var service = CreateService(ValidSettings());
        await service.SetMicEnabledAsync(true);
        JSInterop.VerifyInvoke("livekitInterop.setMicEnabled", 1);
    }

    [Fact]
    public async Task IsConnectedAsync_ReturnsJsResult()
    {
        JSInterop.Setup<bool>("livekitInterop.isConnected").SetResult(true);
        var service = CreateService(ValidSettings());
        Assert.True(await service.IsConnectedAsync());
    }

    private LiveKitService CreateService(LiveKitSettings settings, HttpClient? client = null)
    {
        client ??= new HttpClient(new RejectAllHandler());
        _httpFactoryMock.Setup(f => f.CreateClient(It.IsAny<string>())).Returns(client);
        return new LiveKitService(JSInterop.JSRuntime, _httpFactoryMock.Object, Options.Create(settings), NullLogger<LiveKitService>.Instance);
    }

    private static LiveKitSettings ValidSettings() => new() { Url = "ws://livekit:7880", TokenEndpoint = "http://api:8000/token" };

    private sealed class RejectAllHandler : HttpMessageHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage r, System.Threading.CancellationToken c)
            => throw new HttpRequestException($"No real HTTP in tests: {r.Method} {r.RequestUri}");
    }
}
