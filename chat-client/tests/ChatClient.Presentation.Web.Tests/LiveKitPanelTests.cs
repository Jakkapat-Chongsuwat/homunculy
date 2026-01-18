using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Bunit;
using ChatClient.Presentation.Web.Components;
using ChatClient.Presentation.Web.Services;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;
using MudBlazor.Services;
using Xunit;

namespace ChatClient.Presentation.Web.Tests;

public sealed class LiveKitPanelTests : TestContext
{
    public LiveKitPanelTests()
    {
        JSInterop.Mode = JSRuntimeMode.Loose;
        Services.AddMudServices();
        Services.Configure<LiveKitSettings>(options =>
        {
            options.Url = "ws://localhost:7880";
            options.TokenEndpoint = "http://localhost/api/v1/livekit/token";
        });
        Services.AddSingleton<IHttpClientFactory>(new TestHttpClientFactory(CreateHttpClient()));
        Services.AddScoped<LiveKitService>();
    }

    [Fact]
    public void Renders_DefaultStatus()
    {
        var cut = RenderComponent<LiveKitPanel>();
        cut.Markup.Contains("Status: Disconnected");
    }

    [Fact]
    public void Connect_SetsStatusConnected()
    {
        var cut = RenderComponent<LiveKitPanel>();
        cut.Find("button").Click();
        cut.Markup.Contains("Status: Connected");
    }

    private static HttpClient CreateHttpClient() =>
        new(new TokenHandler());

    private sealed class TestHttpClientFactory : IHttpClientFactory
    {
        private readonly HttpClient _client;

        public TestHttpClientFactory(HttpClient client) => _client = client;

        public HttpClient CreateClient(string name) => _client;
    }

    private sealed class TokenHandler : HttpMessageHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken)
        {
            var payload = JsonSerializer.Serialize(new
            {
                token = "test-token",
                room = "dev-room",
                identity = "test"
            });

            var response = new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(payload, Encoding.UTF8, "application/json")
            };

            return Task.FromResult(response);
        }
    }
}
