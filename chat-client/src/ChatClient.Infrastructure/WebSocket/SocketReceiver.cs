using System.Net.WebSockets;
using System.Reactive.Linq;
using System.Text;
using ChatClient.Domain.ValueObjects;

namespace ChatClient.Infrastructure.WebSocket;

/// <summary>
/// Receives messages from WebSocket as Observable stream.
/// Single Responsibility: Transform WebSocket receive into Rx stream.
/// </summary>
internal sealed class SocketReceiver
{
    private readonly int _bufferSize;

    public SocketReceiver(WebSocketConfig config)
    {
        _bufferSize = config.ReceiveBufferSize;
    }

    private readonly record struct ReceiveResult(string Data, bool IsEndOfMessage, bool IsClose)
    {
        public static ReceiveResult Closed() => new(string.Empty, true, true);
    }

    /// <summary>
    /// Creates an observable stream of complete JSON messages.
    /// </summary>
    public IObservable<string> CreateReceiveStream(SocketConnection connection)
    {
        return Observable.Create<string>(async (observer, ct) =>
        {
            var buffer = new StringBuilder();

            try
            {
                while (!ct.IsCancellationRequested && connection.IsOpen)
                {
                    var result = await ReceiveChunkAsync(connection, ct);

                    if (result.IsClose)
                    {
                        observer.OnCompleted();
                        return;
                    }

                    buffer.Append(result.Data);

                    if (result.IsEndOfMessage)
                    {
                        observer.OnNext(buffer.ToString());
                        buffer.Clear();
                    }
                }

                observer.OnCompleted();
            }
            catch (OperationCanceledException)
            {
                observer.OnCompleted();
            }
            catch (Exception ex)
            {
                observer.OnError(ex);
            }
        });
    }

    /// <summary>
    /// Receives a single complete message (for initial handshake).
    /// </summary>
    public async Task<string> ReceiveOneAsync(SocketConnection connection, CancellationToken ct)
    {
        var buffer = new StringBuilder();

        while (!ct.IsCancellationRequested)
        {
            var result = await ReceiveChunkAsync(connection, ct);

            if (result.IsClose)
                throw new WebSocketException("Connection closed during receive");

            buffer.Append(result.Data);

            if (result.IsEndOfMessage)
                return buffer.ToString();
        }

        throw new OperationCanceledException(ct);
    }

    private async Task<ReceiveResult> ReceiveChunkAsync(
        SocketConnection connection, 
        CancellationToken ct)
    {
        var buffer = new byte[_bufferSize];
        var result = await connection.Socket!.ReceiveAsync(buffer, ct);

        if (result.MessageType == WebSocketMessageType.Close)
            return ReceiveResult.Closed();

        var data = Encoding.UTF8.GetString(buffer, 0, result.Count);
        return new ReceiveResult(data, result.EndOfMessage, false);
    }
}
