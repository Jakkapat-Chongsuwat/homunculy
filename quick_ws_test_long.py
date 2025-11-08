import asyncio
import json
import websockets

async def test_waifu_chat():
    waifu_id = "test_waifu_fresh"
    user_id = "test_user"
    url = f"ws://localhost:8000/ws/waifu/agents/{waifu_id}/chat?user_id={user_id}"
    
    print(f"🔗 Connecting to: {url}")
    
    async with websockets.connect(url) as websocket:
        print("✅ Connected!")
        
        # Receive initial messages
        for _ in range(3):  # Expect: system message, maybe more
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"📨 Received: {json.dumps(data, indent=2)}...")
                if "..." not in str(data):
                    print(json.dumps(data, indent=2))
            except asyncio.TimeoutError:
                break
        
        # Send a test message
        test_message = {
            "message": "Hello! How are you?",
            "context": {}
        }
        await websocket.send(json.dumps(test_message))
        print(f"📤 Sent: {test_message}")
        
        # Collect responses with longer timeout
        print("\n📨 Responses:")
        try:
            while True:
                response = await asyncio.wait_for(websocket.recv(), timeout=30.0)  # 30 second timeout
                data = json.loads(response)
                msg_type = data.get("type", "unknown")
                message = data.get("message", "")[:100]  # Truncate long messages
                print(f"  [{msg_type}] {message}")
                
                # Break if we get final message or error
                if msg_type in ["final", "error"]:
                    break
        except asyncio.TimeoutError:
            print("  ⏱️ Timeout - no more messages")
        
        print("\n✅ Test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_waifu_chat())
