namespace ChatClient.Presentation.Web.Services;

/// <summary>
/// LiveKit configuration settings.
/// </summary>
public sealed class LiveKitSettings
{
    public string Url { get; set; } = string.Empty;
    public string TokenEndpoint { get; set; } = string.Empty;

    public bool IsConfigured =>
        !string.IsNullOrWhiteSpace(Url) && !string.IsNullOrWhiteSpace(TokenEndpoint);
}
