"""Quick WebSocket test for waifu chat."""
import asyncio
import websockets
import json


async def test_waifu_chat():
    """Test WebSocket connection and chat."""
    waifu_id = "test_waifu_fresh"  # Use new ID to force creation
    user_id = "test_user"
    url = f"ws://localhost:8000/ws/waifu/agents/{waifu_id}/chat?user_id={user_id}"
    
    print(f"🔗 Connecting to: {url}")
    
    async with websockets.connect(url) as websocket:
        print("✅ Connected!")
        
        # Receive welcome messages
        for _ in range(3):  # Get initial system messages
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                data = json.loads(response)
                print(f"📨 Received: {json.dumps(data, indent=2)[:200]}...")
            except asyncio.TimeoutError:
                break
        
        # Send a test message
        test_message = {"message": "Hello! How are you?", "context": {}}
        print(f"📤 Sending: {test_message}")
        await websocket.send(json.dumps(test_message))
        
        # Receive responses
        print("\n📨 Responses:")
        for _ in range(10):  # Collect up to 10 responses
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"  [{data.get('type')}] {data.get('message', data)}")
            except asyncio.TimeoutError:
                print("  ⏱️ Timeout - no more messages")
                break
    
    print("\n✅ Test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_waifu_chat())
