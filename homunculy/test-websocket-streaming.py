#!/usr/bin/env python3
"""
Test WebSocket Streaming Chat with TTS.

This script tests the WebSocket endpoint that streams both text and audio chunks in real-time.
"""

import asyncio
import json
import base64
import websockets
from pathlib import Path


async def test_websocket_streaming():
    """Test WebSocket streaming with TTS audio."""
    
    uri = "ws://localhost:8000/api/v1/ws/chat"
    
    print("🔌 Connecting to WebSocket...")
    
    async with websockets.connect(uri) as websocket:
        # Wait for connection status
        status_msg = await websocket.recv()
        status = json.loads(status_msg)
        print(f"✅ {status['message']}")
        print()
        
        # Prepare chat request
        request = {
            "type": "chat_request",
            "user_id": "websocket-test-user",
            "message": "Hello! Please introduce yourself in one sentence.",
            "configuration": {
                "provider": "langraph",
                "model_name": "gpt-4o-mini",
                "personality": {
                    "name": "Homunculy",
                    "description": "AI Assistant",
                    "traits": {},
                    "mood": "friendly"
                },
                "system_prompt": "You are Homunculy, a friendly AI assistant. Keep responses concise.",
                "temperature": 0.7,
                "max_tokens": 150
            },
            "context": {},
            "stream_audio": True,
            "voice_id": "EXAVITQu4vr4xnSDxMaL"
        }
        
        print("📤 Sending chat request...")
        await websocket.send(json.dumps(request))
        print()
        
        # Receive streaming responses
        full_text = ""
        audio_chunks = []
        text_chunk_count = 0
        audio_chunk_count = 0
        
        print("📥 Receiving streaming response:")
        print("=" * 60)
        
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                msg_type = data.get("type")
                
                if msg_type == "text_chunk":
                    chunk = data.get("chunk", "")
                    full_text += chunk
                    text_chunk_count += 1
                    print(chunk, end="", flush=True)
                    
                    if data.get("is_final"):
                        print()  # New line after final chunk
                
                elif msg_type == "audio_chunk":
                    if data.get("data"):  # Not the final empty marker
                        audio_data = data.get("data", "")
                        audio_chunks.append(audio_data)
                        audio_chunk_count += 1
                        size_kb = data.get("size_bytes", 0) / 1024
                        print(f"🔊 Audio chunk {data.get('chunk_index')}: {size_kb:.2f} KB")
                    
                    if data.get("is_final"):
                        print("✅ Audio streaming complete")
                
                elif msg_type == "metadata":
                    print()
                    print("=" * 60)
                    print("📊 Metadata:")
                    print(f"  Model: {data.get('model_used')}")
                    print(f"  Tokens: {data.get('tokens_used')}")
                    exec_time = data.get('execution_time_ms')
                    if exec_time is not None:
                        print(f"  Execution time: {exec_time:.2f}ms")
                    print(f"  Thread ID: {data.get('thread_id')}")
                    print(f"  Voice ID: {data.get('voice_id')}")
                    print(f"  Text chunks: {data.get('total_text_chunks')}")
                    print(f"  Audio chunks: {data.get('total_audio_chunks')}")
                    print()
                
                elif msg_type == "complete":
                    print("✅ Stream completed successfully")
                    print()
                    break
                
                elif msg_type == "error":
                    print(f"❌ Error: {data.get('code')} - {data.get('message')}")
                    print()
                    break
                    
            except websockets.exceptions.ConnectionClosed:
                print("❌ Connection closed unexpectedly")
                break
        
        # Save audio if received
        if audio_chunks:
            print(f"💾 Saving audio ({len(audio_chunks)} chunks)...")
            
            # Decode and combine all audio chunks
            audio_data = b""
            for chunk_b64 in audio_chunks:
                audio_data += base64.b64decode(chunk_b64)
            
            # Save to logs directory
            output_path = Path(__file__).parent / "logs" / "websocket_stream_response.mp3"
            output_path.parent.mkdir(exist_ok=True)
            
            with open(output_path, "wb") as f:
                f.write(audio_data)
            
            size_kb = len(audio_data) / 1024
            print(f"✅ Audio saved: {output_path} ({size_kb:.2f} KB)")
            print()
            
            # Try to play the audio
            try:
                import subprocess
                import platform
                
                if platform.system() == "Windows":
                    subprocess.run(["cmd", "/c", "start", str(output_path)], check=False)
                    print("▶️  Audio playing in default media player!")
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", str(output_path)], check=False)
                    print("▶️  Audio playing in default media player!")
                else:  # Linux
                    subprocess.run(["xdg-open", str(output_path)], check=False)
                    print("▶️  Audio playing in default media player!")
            except Exception:
                print(f"ℹ️  Audio saved. Open {output_path} to play.")
        
        print("=" * 60)
        print("📝 Summary:")
        print(f"  Full text: {full_text}")
        print(f"  Text chunks received: {text_chunk_count}")
        print(f"  Audio chunks received: {audio_chunk_count}")
        print()


if __name__ == "__main__":
    print("🎤 Testing WebSocket Streaming Chat with TTS")
    print()
    
    try:
        asyncio.run(test_websocket_streaming())
        print("✅ Test completed successfully!")
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
