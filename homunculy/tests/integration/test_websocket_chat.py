#!/usr/bin/env python3
"""
Integration tests for WebSocket chat with audio streaming and interruption.

Tests:
1. Basic chat response streaming
2. Audio chunk streaming (no playback, just verify chunks received)
3. Interruption - sending new message cancels previous response
4. Concurrent message handling
"""

import asyncio
import json
import base64
import pytest
import websockets
from typing import AsyncGenerator

# Test configuration
WS_URI = "ws://localhost:8000/api/v1/ws/chat"
TEST_TIMEOUT = 30.0


def create_chat_request(
    message: str,
    user_id: str = "integration-test",
    stream_audio: bool = True,
) -> dict:
    """Create a chat request message."""
    return {
        "type": "chat_request",
        "user_id": user_id,
        "message": message,
        "configuration": {
            "provider": "langraph",
            "model_name": "gpt-4o-mini",
            "personality": {
                "name": "Homunculy",
                "description": "AI Assistant",
                "traits": {},
                "mood": "friendly",
            },
            "system_prompt": "You are Homunculy. Keep responses very short (1-2 sentences max).",
            "temperature": 0.7,
            "max_tokens": 50,
        },
        "context": {},
        "stream_audio": stream_audio,
        "voice_id": "EXAVITQu4vr4xnSDxMaL",
    }


async def collect_response(
    websocket, timeout: float = TEST_TIMEOUT
) -> dict:
    """Collect all messages until complete or error."""
    result = {
        "text_chunks": [],
        "audio_chunks": [],
        "full_text": "",
        "complete": False,
        "interrupted": False,
        "error": None,
        "metadata": None,
    }

    deadline = asyncio.get_event_loop().time() + timeout

    while asyncio.get_event_loop().time() < deadline:
        try:
            remaining = deadline - asyncio.get_event_loop().time()
            message = await asyncio.wait_for(websocket.recv(), timeout=remaining)
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "text_chunk":
                chunk = data.get("chunk", "")
                result["text_chunks"].append(chunk)
                result["full_text"] += chunk

            elif msg_type == "audio_chunk":
                if data.get("data"):
                    result["audio_chunks"].append(data)

            elif msg_type == "metadata":
                result["metadata"] = data

            elif msg_type == "complete":
                result["complete"] = True
                break

            elif msg_type == "interrupted":
                result["interrupted"] = True
                break

            elif msg_type == "error":
                result["error"] = data
                break

        except asyncio.TimeoutError:
            break

    return result


@pytest.mark.asyncio
async def test_basic_chat_response():
    """Test basic chat response streaming without audio."""
    async with websockets.connect(WS_URI) as ws:
        # Receive connection status
        status = json.loads(await ws.recv())
        assert status["status"] == "connected"

        # Send chat request (no audio for speed)
        request = create_chat_request("Say hello", stream_audio=False)
        await ws.send(json.dumps(request))

        # Collect response
        result = await collect_response(ws)

        assert result["complete"], "Response should complete"
        assert len(result["text_chunks"]) > 0, "Should receive text chunks"
        assert len(result["full_text"]) > 0, "Should have response text"
        assert result["audio_chunks"] == [], "No audio when disabled"

        print(f"✅ Received {len(result['text_chunks'])} text chunks")
        print(f"   Response: {result['full_text'][:100]}...")


@pytest.mark.asyncio
async def test_audio_streaming():
    """Test that audio chunks are received when enabled."""
    async with websockets.connect(WS_URI) as ws:
        status = json.loads(await ws.recv())
        assert status["status"] == "connected"

        request = create_chat_request("Say hi", stream_audio=True)
        await ws.send(json.dumps(request))

        result = await collect_response(ws)

        assert result["complete"], "Response should complete"
        assert len(result["audio_chunks"]) > 0, "Should receive audio chunks"

        total_audio_bytes = sum(
            len(base64.b64decode(c["data"])) for c in result["audio_chunks"]
        )
        print(f"✅ Received {len(result['audio_chunks'])} audio chunks")
        print(f"   Total audio: {total_audio_bytes / 1024:.2f} KB")


@pytest.mark.asyncio
async def test_interruption():
    """Test that sending a new message interrupts the previous response."""
    async with websockets.connect(WS_URI) as ws:
        status = json.loads(await ws.recv())
        assert status["status"] == "connected"

        # Send first message (with audio to make it slower)
        request1 = create_chat_request(
            "Tell me a long story about a dragon",
            stream_audio=True,
        )
        await ws.send(json.dumps(request1))

        # Wait a bit for streaming to start
        await asyncio.sleep(0.5)

        # Send interrupting message
        request2 = create_chat_request(
            "Stop! Say only: INTERRUPTED",
            stream_audio=False,
        )
        await ws.send(json.dumps(request2))

        # Collect until we get interrupted or complete
        interrupted = False
        second_response_started = False
        messages_after_interrupt = []

        deadline = asyncio.get_event_loop().time() + TEST_TIMEOUT

        while asyncio.get_event_loop().time() < deadline:
            try:
                remaining = deadline - asyncio.get_event_loop().time()
                message = await asyncio.wait_for(ws.recv(), timeout=remaining)
                data = json.loads(message)
                msg_type = data.get("type")

                if msg_type == "interrupted":
                    interrupted = True
                    print(f"✅ Received interruption: {data.get('message')}")
                    continue

                if interrupted:
                    messages_after_interrupt.append(data)
                    if msg_type == "complete":
                        second_response_started = True
                        break

            except asyncio.TimeoutError:
                break

        assert interrupted, "Should receive interrupted message"
        assert second_response_started, "Should receive complete for second message"
        print(f"✅ Interruption works - received {len(messages_after_interrupt)} messages after interrupt")


@pytest.mark.asyncio
async def test_rapid_messages():
    """Test sending multiple messages rapidly."""
    async with websockets.connect(WS_URI) as ws:
        status = json.loads(await ws.recv())
        assert status["status"] == "connected"

        # Send 3 messages rapidly
        messages = ["First", "Second", "Third"]
        for msg in messages:
            request = create_chat_request(msg, stream_audio=False)
            await ws.send(json.dumps(request))
            await asyncio.sleep(0.1)  # Small delay

        # Should receive interruptions and final response
        interrupt_count = 0
        complete_count = 0

        deadline = asyncio.get_event_loop().time() + TEST_TIMEOUT

        while asyncio.get_event_loop().time() < deadline:
            try:
                remaining = deadline - asyncio.get_event_loop().time()
                message = await asyncio.wait_for(ws.recv(), timeout=remaining)
                data = json.loads(message)
                msg_type = data.get("type")

                if msg_type == "interrupted":
                    interrupt_count += 1
                elif msg_type == "complete":
                    complete_count += 1
                    if complete_count >= 1:  # At least one complete
                        break

            except asyncio.TimeoutError:
                break

        # Should have at least 2 interruptions (first 2 messages interrupted)
        assert interrupt_count >= 2, f"Expected at least 2 interruptions, got {interrupt_count}"
        assert complete_count >= 1, "Should complete at least one message"

        print(f"✅ Rapid messages: {interrupt_count} interrupts, {complete_count} completes")


if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("WebSocket Chat Integration Tests")
    print("=" * 60)
    print()
    print("Make sure the server is running: make run")
    print()

    async def run_all_tests():
        tests = [
            ("Basic Chat", test_basic_chat_response),
            ("Audio Streaming", test_audio_streaming),
            ("Interruption", test_interruption),
            ("Rapid Messages", test_rapid_messages),
        ]

        passed = 0
        failed = 0

        for name, test_func in tests:
            print(f"\n🧪 Running: {name}")
            print("-" * 40)
            try:
                await test_func()
                passed += 1
                print(f"✅ {name} PASSED")
            except AssertionError as e:
                failed += 1
                print(f"❌ {name} FAILED: {e}")
            except Exception as e:
                failed += 1
                print(f"❌ {name} ERROR: {e}")

        print()
        print("=" * 60)
        print(f"Results: {passed} passed, {failed} failed")
        return failed == 0

    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
