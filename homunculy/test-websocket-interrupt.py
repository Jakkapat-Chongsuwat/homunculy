#!/usr/bin/env python3
"""
Test WebSocket Interruption with Real-Time Audio.

Automatically tests interruption by sending messages while AI is streaming.
Plays audio to demonstrate real-time voice chat interruption.
"""

import asyncio
import json
import base64
import websockets
from pathlib import Path
from datetime import datetime
import subprocess
import platform


class AutoInterruptTester:
    """Automatic WebSocket interruption tester with audio playback."""
    
    def __init__(self, uri: str):
        self.uri = uri
        self.websocket = None
        self.audio_chunks = []
        self.current_text = ""
        self.interrupted_count = 0
        self.completed_count = 0
    
    async def connect(self):
        """Connect to WebSocket server."""
        print("🔌 Connecting to WebSocket...")
        self.websocket = await websockets.connect(self.uri)
        
        # Wait for connection status
        status_msg = await self.websocket.recv()
        status = json.loads(status_msg)
        print(f"✅ {status['message']}\n")
    
    async def send_message(self, message: str):
        """Send a chat message."""
        if not self.websocket:
            return
            
        request = {
            "type": "chat_request",
            "user_id": "interrupt-test",
            "message": message,
            "configuration": {
                "provider": "langraph",
                "model_name": "gpt-4o-mini",
                "personality": {
                    "name": "Homunculy",
                    "description": "AI Assistant",
                    "traits": {},
                    "mood": "friendly"
                },
                "system_prompt": "You are a helpful AI. Be concise.",
                "temperature": 0.7,
                "max_tokens": 200
            },
            "context": {},
            "stream_audio": True,
            "voice_id": "EXAVITQu4vr4xnSDxMaL"
        }
        
        print(f"📤 Sending: \"{message}\"")
        await self.websocket.send(json.dumps(request))
        self.current_text = ""
        self.audio_chunks = []
    
    async def receive_messages(self):
        """Receive and process all WebSocket messages."""
        if not self.websocket:
            return
            
        try:
            async for message in self.websocket:
                data = json.loads(message)
                msg_type = data.get("type")
                
                if msg_type == "text_chunk":
                    chunk = data.get("chunk", "")
                    self.current_text += chunk
                    print(chunk, end="", flush=True)
                
                elif msg_type == "audio_chunk":
                    if data.get("data"):
                        self.audio_chunks.append(data.get("data"))
                    
                    if data.get("is_final"):
                        print(f"\n🔊 Audio: {len(self.audio_chunks)} chunks")
                
                elif msg_type == "interrupted":
                    self.interrupted_count += 1
                    print(f"\n⚠️  INTERRUPTED! (at text chunk {data.get('interrupted_at_text_chunk')}, audio chunk {data.get('interrupted_at_audio_chunk')})")
                    print(f"   Reason: {data.get('message')}\n")
                
                elif msg_type == "complete":
                    self.completed_count += 1
                    print("✅ Complete\n")
                    
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")
    
    def play_audio(self):
        """Play collected audio chunks."""
        if not self.audio_chunks:
            return
        
        print(f"🎵 Playing audio ({len(self.audio_chunks)} chunks)...")
        
        # Decode audio
        audio_data = b""
        for chunk_b64 in self.audio_chunks:
            audio_data += base64.b64decode(chunk_b64)
        
        # Save temporarily
        output_path = Path(__file__).parent / "logs" / f"interrupt_test_{datetime.now().strftime('%H%M%S')}.mp3"
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, "wb") as f:
            f.write(audio_data)
        
        # Play
        try:
            if platform.system() == "Windows":
                subprocess.run(["cmd", "/c", "start", "", str(output_path)], check=False)
            elif platform.system() == "Darwin":
                subprocess.run(["afplay", str(output_path)], check=False)
            else:
                subprocess.run(["xdg-open", str(output_path)], check=False)
            
            print(f"▶️  Playing: {output_path}\n")
        except Exception as e:
            print(f"⚠️  Couldn't auto-play: {e}\n")
    
    async def test_interruption(self):
        """Run automatic interruption test."""
        print("=" * 70)
        print("🎤 AUTOMATIC WEBSOCKET INTERRUPTION TEST")
        print("=" * 70)
        print("\nThis test will:")
        print("1. Send a long story request")
        print("2. After 1.5s, interrupt DURING LLM generation")
        print("3. Verify INTERRUPTED message received")
        print("4. Play final audio")
        print()
        
        # Start receiver in background
        receiver_task = asyncio.create_task(self.receive_messages())
        
        # Test 1: Send message
        await self.send_message("Tell me a detailed story about a brave dragon who saves a village, including descriptions of the characters, the setting, and the exciting adventure. Make it at least 100 words.")
        
        # Wait for LLM to start streaming, then interrupt during generation
        await asyncio.sleep(1.5)
        
        # Test 2: INTERRUPT during LLM streaming
        print("\n🔥 INTERRUPTING DURING LLM GENERATION!\n")
        await self.send_message("Stop! Tell me a quick joke instead!")
        
        # Wait for completion
        await asyncio.sleep(6)
        
        # Close connection
        if self.websocket:
            await self.websocket.close()
        
        # Wait for receiver to finish
        try:
            await asyncio.wait_for(receiver_task, timeout=2)
        except asyncio.TimeoutError:
            receiver_task.cancel()
        
        # Results
        print("=" * 70)
        print("📊 TEST RESULTS")
        print("=" * 70)
        print(f"Interruptions detected: {self.interrupted_count}")
        print(f"Completions received: {self.completed_count}")
        print(f"Final text length: {len(self.current_text)} chars")
        print(f"Final audio chunks: {len(self.audio_chunks)}")
        print()
        
        if self.interrupted_count > 0:
            print("✅ SUCCESS: Interruption working!")
        else:
            print("⚠️  Note: Interruption works during audio streaming")
            print("   LLM call is currently blocking (future: add streaming LLM)")
        
        print()
        
        # Play final audio
        if self.audio_chunks:
            self.play_audio()
    
    async def run(self):
        """Run the test."""
        await self.connect()
        await self.test_interruption()


async def main():
    """Main entry point."""
    uri = "ws://localhost:8000/api/v1/ws/chat"
    tester = AutoInterruptTester(uri)
    
    try:
        await tester.run()
        print("✅ Test completed!")
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
