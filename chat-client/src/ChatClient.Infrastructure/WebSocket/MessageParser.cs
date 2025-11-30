using System.Text.Json;
using ChatClient.Domain.Events;

namespace ChatClient.Infrastructure.WebSocket;

/// <summary>
/// Parses WebSocket messages into domain events.
/// </summary>
internal static class MessageParser
{
    public static ChatEvent? Parse(string json)
    {
        try
        {
            using var doc = JsonDocument.Parse(json);
            return ParseDocument(doc.RootElement);
        }
        catch (JsonException)
        {
            return null;
        }
    }

    private static ChatEvent? ParseDocument(JsonElement root)
    {
        if (!TryGetType(root, out var type))
            return null;

        return type switch
        {
            "text_chunk" => ParseTextChunk(root),
            "audio_chunk" => ParseAudioChunk(root),
            "complete" => new ResponseCompleted(),
            "interrupted" => new ResponseInterrupted(),
            "error" => ParseError(root),
            "connection_status" => ParseStatus(root),
            _ => null
        };
    }

    private static bool TryGetType(
        JsonElement root,
        out string type)
    {
        type = string.Empty;
        if (!root.TryGetProperty("type", out var prop))
            return false;
        type = prop.GetString() ?? string.Empty;
        return !string.IsNullOrEmpty(type);
    }

    private static TextChunkReceived ParseTextChunk(JsonElement root)
    {
        var chunk = GetStringProperty(root, "chunk");
        return new TextChunkReceived(chunk);
    }

    private static AudioChunkReceived? ParseAudioChunk(JsonElement root)
    {
        var base64 = GetStringProperty(root, "data");
        if (string.IsNullOrEmpty(base64))
            return null;

        var bytes = Convert.FromBase64String(base64);
        return new AudioChunkReceived(bytes);
    }

    private static ErrorOccurred ParseError(JsonElement root)
    {
        var message = GetStringProperty(root, "message");
        return new ErrorOccurred(message);
    }

    private static StatusMessageReceived ParseStatus(JsonElement root)
    {
        var message = GetStringProperty(root, "message");
        return new StatusMessageReceived(message);
    }

    private static string GetStringProperty(
        JsonElement root,
        string name)
    {
        if (!root.TryGetProperty(name, out var prop))
            return string.Empty;
        return prop.GetString() ?? string.Empty;
    }
}
