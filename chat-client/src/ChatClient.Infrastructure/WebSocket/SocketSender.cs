using System.Net.WebSockets;
using System.Text;
using System.Text.Json;

namespace ChatClient.Infrastructure.WebSocket;

/// <summary>
/// Sends messages through WebSocket.
/// Single Responsibility: Serialize and send data.
/// </summary>
internal sealed class SocketSender
{
    public async Task SendJsonAsync<T>(
        SocketConnection connection, 
        T message, 
        CancellationToken ct)
    {
        if (!connection.IsOpen)
            throw new InvalidOperationException("Socket is not connected");

        var json = JsonSerializer.Serialize(message);
        var bytes = Encoding.UTF8.GetBytes(json);
        
        await connection.Socket!.SendAsync(
            bytes, 
            WebSocketMessageType.Text, 
            endOfMessage: true, 
            ct);
    }

    public Task SendPingAsync(SocketConnection connection, CancellationToken ct)
    {
        var ping = new { type = "ping", timestamp = DateTime.UtcNow.ToString("O") };
        return SendJsonAsync(connection, ping, ct);
    }
}
