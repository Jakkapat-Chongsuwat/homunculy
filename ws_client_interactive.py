import sys
import asyncio
import json
import websockets

async def run(agent_id: str, thread_id: str = "interactive-thread"):
    uri = f"ws://localhost:8000/ws/agents/{agent_id}/chat?thread_id={thread_id}"
    print(f"Connecting to {uri}...")
    async with websockets.connect(uri) as ws:
        print("Connected. Type messages and press Enter. Type /quit to exit.")

        async def receiver():
            try:
                async for message in ws:
                    try:
                        data = json.loads(message)
                        # pretty print small objects
                        print("\n<< ", json.dumps(data, ensure_ascii=False))
                        print('> ', end='', flush=True)
                    except Exception:
                        print("\n<< ", message)
                        print('> ', end='', flush=True)
            except websockets.ConnectionClosed:
                print("\nWebSocket connection closed")

        recv_task = asyncio.create_task(receiver())

        loop = asyncio.get_event_loop()
        try:
            while True:
                # read user input without blocking the event loop
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                line = line.strip()
                if line in ("/quit", "/exit"):
                    print("Closing connection...")
                    break
                if line == "":
                    continue
                payload = json.dumps({"message": line, "context": {}})
                await ws.send(payload)
        except KeyboardInterrupt:
            print("Interrupted by user, closing...")
        finally:
            try:
                await ws.close()
            except Exception:
                pass
            recv_task.cancel()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python ws_client_interactive.py <agent_id> [thread_id]")
        sys.exit(1)
    agent_id = sys.argv[1]
    thread_id = sys.argv[2] if len(sys.argv) > 2 else "interactive-thread"
    asyncio.run(run(agent_id, thread_id))
