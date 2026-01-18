using ChatClient.Application.Configuration;
using Xunit;

namespace ChatClient.Presentation.Web.Tests;

public sealed class ChatSettingsTests
{
    [Fact]
    public void Defaults_AreStable()
    {
        var settings = new ChatSettings();

        Assert.Equal("ws://localhost:8000/api/v1/ws/chat", settings.ServerUri);
        Assert.True(settings.EnableAudio);
        Assert.Equal("gpt-4o-mini", settings.Agent.ModelName);
    }
}
