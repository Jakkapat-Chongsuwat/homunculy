#!/usr/bin/env python3
"""
Fast Interactive WebSocket Chat Client with Real-time Audio.

Supports interruption - sending new message stops current audio.

Usage:
    python chat_fast.py
"""

import asyncio
import base64
import json
import sys
import os
import threading
import queue
from io import BytesIO
from typing import Any, Optional
from dataclasses import dataclass


# =============================================================================
# Logging Setup
# =============================================================================

DEBUG = os.environ.get("DEBUG", "0") == "1"


def log_debug(msg: str, **kwargs: Any) -> None:
    """Log debug message if DEBUG is enabled."""
    if DEBUG:
        extras = " ".join(f"{k}={v}" for k, v in kwargs.items())
        print(f"[DEBUG] {msg} {extras}", file=sys.stderr)


def log_info(msg: str, **kwargs: Any) -> None:
    """Log info message."""
    extras = " ".join(f"{k}={v}" for k, v in kwargs.items())
    print(f"[INFO] {msg} {extras}", file=sys.stderr)


def log_error(msg: str, **kwargs: Any) -> None:
    """Log error message."""
    extras = " ".join(f"{k}={v}" for k, v in kwargs.items())
    print(f"[ERROR] {msg} {extras}", file=sys.stderr)


# =============================================================================
# Audio Player with Smooth Buffered Playback
# =============================================================================


class AudioPlayer:
    """
    Audio player with buffered MP3 decoding for smooth playback.
    
    Accumulates MP3 chunks into larger buffers before decoding to avoid
    stuttering caused by decoding many small fragments.
    """

    SAMPLE_RATE = 44100
    CHANNELS = 1
    SAMPLE_WIDTH = 2
    # Larger buffer = smoother playback, but more latency
    # 16KB gives good balance between smoothness and responsiveness
    MIN_BUFFER_SIZE = 16384
    # Pre-buffer this many decoded PCM bytes before starting playback
    PRE_BUFFER_SIZE = 44100  # ~0.5 seconds of audio

    def __init__(self) -> None:
        self._pyaudio: Any = None
        self._stream: Any = None
        self._chunk_queue: queue.Queue[Optional[bytes]] = queue.Queue()
        self._pcm_queue: queue.Queue[bytes] = queue.Queue()
        self._running = False
        self._decoder_thread: Optional[threading.Thread] = None
        self._player_thread: Optional[threading.Thread] = None
        self._enabled = False
        self._mp3_buffer = bytearray()
        self._buffer_lock = threading.Lock()
        self._pre_buffered = threading.Event()
        self._pre_buffer_bytes = 0
        self._pre_buffer_lock = threading.Lock()
        self._initialize()

    def _initialize(self) -> None:
        """Initialize PyAudio and pydub."""
        try:
            import pyaudio  # type: ignore[import-not-found]
            self._pyaudio = pyaudio.PyAudio()
            self._configure_ffmpeg()
            self._enabled = True
            self._start_workers()
            log_info("audio_player_initialized")
        except ImportError as e:
            log_error("audio_init_failed", error=str(e))
            self._enabled = False

    def _configure_ffmpeg(self) -> None:
        """Configure ffmpeg path for pydub."""
        from pydub import AudioSegment  # type: ignore[import-untyped]
        ffmpeg_paths = [
            r"C:\Users\Jakkapat\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe",
            r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
        ]
        for path in ffmpeg_paths:
            if os.path.exists(path):
                AudioSegment.converter = path
                log_debug("ffmpeg_found", path=path)
                break

    def _start_workers(self) -> None:
        """Start decoder and player threads."""
        self._running = True
        self._decoder_thread = threading.Thread(
            target=self._decoder_worker, daemon=True, name="AudioDecoder"
        )
        self._player_thread = threading.Thread(
            target=self._player_worker, daemon=True, name="AudioPlayer"
        )
        self._decoder_thread.start()
        self._player_thread.start()

    def _decode_mp3(self, mp3_data: bytes) -> Optional[bytes]:
        """Decode MP3 data to raw PCM."""
        if len(mp3_data) < 100:
            return None
        try:
            from pydub import AudioSegment  # type: ignore[import-untyped]
            audio = AudioSegment.from_mp3(BytesIO(mp3_data))  # type: ignore[no-untyped-call]
            audio = audio.set_frame_rate(self.SAMPLE_RATE)  # type: ignore[union-attr]
            audio = audio.set_channels(self.CHANNELS)  # type: ignore[union-attr]
            audio = audio.set_sample_width(self.SAMPLE_WIDTH)  # type: ignore[union-attr]
            audio = audio + 6  # type: ignore[operator] # Boost volume
            return audio.raw_data  # type: ignore[union-attr, return-value]
        except (OSError, IOError) as e:
            log_debug("decode_error", error=str(e)[:50])
            return None

    def _decoder_worker(self) -> None:
        """Background thread that decodes MP3 chunks to PCM."""
        while self._running:
            try:
                item = self._chunk_queue.get(timeout=0.1)
                
                if item is None:  # Stop signal
                    break
                
                if item == b"FLUSH":
                    # Decode remaining buffer
                    with self._buffer_lock:
                        if len(self._mp3_buffer) > 0:
                            mp3_data = bytes(self._mp3_buffer)
                            self._mp3_buffer.clear()
                            raw = self._decode_mp3(mp3_data)
                            if raw:
                                self._pcm_queue.put(raw)
                                log_debug("flushed_final", pcm=len(raw))
                    # Signal pre-buffer complete if not already
                    self._pre_buffered.set()
                    continue
                
                # Add to buffer
                with self._buffer_lock:
                    self._mp3_buffer.extend(item)
                    current_size = len(self._mp3_buffer)
                
                # Decode when buffer is large enough
                if current_size >= self.MIN_BUFFER_SIZE:
                    with self._buffer_lock:
                        mp3_data = bytes(self._mp3_buffer)
                        self._mp3_buffer.clear()
                    
                    raw = self._decode_mp3(mp3_data)
                    if raw:
                        self._pcm_queue.put(raw)
                        with self._pre_buffer_lock:
                            self._pre_buffer_bytes += len(raw)
                            current_prebuf = self._pre_buffer_bytes
                        log_debug("decoded", pcm=len(raw), prebuf=current_prebuf)
                        
                        # Signal when pre-buffer threshold reached
                        if current_prebuf >= self.PRE_BUFFER_SIZE:
                            self._pre_buffered.set()

            except queue.Empty:
                continue

    def _player_worker(self) -> None:
        """Background thread that plays PCM audio."""
        if not self._pyaudio:
            return

        # Create persistent stream
        self._stream = self._pyaudio.open(
            format=self._pyaudio.get_format_from_width(self.SAMPLE_WIDTH),
            channels=self.CHANNELS,
            rate=self.SAMPLE_RATE,
            output=True,
            frames_per_buffer=4096,  # Larger buffer for smoother playback
        )

        try:
            while self._running:
                # Wait for pre-buffer before starting playback
                if not self._pre_buffered.wait(timeout=0.1):
                    continue
                
                try:
                    pcm_data = self._pcm_queue.get(timeout=0.05)
                    if self._stream:
                        self._stream.write(pcm_data)
                        log_debug("played", bytes=len(pcm_data))
                except queue.Empty:
                    continue

        finally:
            if self._stream:
                self._stream.stop_stream()
                self._stream.close()

    @property
    def is_enabled(self) -> bool:
        """Check if audio is enabled."""
        return self._enabled

    def queue_audio(self, mp3_data: bytes) -> None:
        """Queue MP3 data for playback."""
        if self._enabled:
            self._chunk_queue.put(mp3_data)

    def flush(self) -> None:
        """Signal to flush any accumulated audio."""
        if self._enabled:
            self._chunk_queue.put(b"FLUSH")

    def clear_queue(self) -> None:
        """Clear all pending audio (for interruption)."""
        # Clear chunk queue
        cleared = 0
        while not self._chunk_queue.empty():
            try:
                self._chunk_queue.get_nowait()
                cleared += 1
            except queue.Empty:
                break
        
        # Clear PCM queue
        while not self._pcm_queue.empty():
            try:
                self._pcm_queue.get_nowait()
            except queue.Empty:
                break
        
        # Clear buffer
        with self._buffer_lock:
            self._mp3_buffer.clear()
        
        log_debug("audio_cleared", chunks=cleared)

    def reset_for_new_message(self) -> None:
        """Reset state for a new message (clears queue and resets pre-buffer)."""
        self.clear_queue()
        self._pre_buffered.clear()
        with self._pre_buffer_lock:
            self._pre_buffer_bytes = 0
        log_debug("reset_for_new_message")

    def stop(self) -> None:
        """Stop playback and cleanup."""
        self._running = False
        self._pre_buffered.set()  # Unblock player
        self._chunk_queue.put(None)
        
        if self._decoder_thread and self._decoder_thread.is_alive():
            self._decoder_thread.join(timeout=1.0)
        if self._player_thread and self._player_thread.is_alive():
            self._player_thread.join(timeout=1.0)
        if self._pyaudio:
            self._pyaudio.terminate()


# =============================================================================
# Chat Client
# =============================================================================


@dataclass
class ChatClient:
    """WebSocket chat client with audio support."""

    uri: str = "ws://localhost:8000/api/v1/ws/chat"
    user_id: str = "User"
    websocket: Any = None
    audio_player: Any = None
    _receiving: bool = False

    async def connect(self) -> bool:
        """Connect to chat server."""
        try:
            import websockets  # type: ignore[import-untyped]
            self.websocket = await websockets.connect(self.uri)
            status = json.loads(await self.websocket.recv())
            print(f"[OK] {status.get('message', 'Connected')}")
            log_info("connected")
            return True
        except ConnectionRefusedError:
            print("[ERROR] Connection refused - is the server running?")
            return False
        except OSError as e:
            print(f"[ERROR] Connection failed: {e}")
            return False

    async def send_message(self, message: str) -> None:
        """Send a chat message."""
        # Reset audio for new message
        if self.audio_player:
            self.audio_player.reset_for_new_message()

        request: dict[str, Any] = {
            "type": "chat_request",
            "user_id": self.user_id,
            "message": message,
            "configuration": {
                "provider": "langraph",
                "model_name": "gpt-4o-mini",
                "personality": {
                    "name": "Homunculy",
                    "description": "A friendly AI assistant",
                    "traits": {},
                    "mood": "cheerful",
                },
                "system_prompt": (
                    "You are Homunculy, a friendly AI assistant. "
                    "Respond directly to the user's message. Be concise. "
                    "Never summarize previous conversations. "
                    "If interrupted, just respond to the new message naturally."
                ),
                "temperature": 0.7,
                "max_tokens": 500,
            },
            "context": {},
            "stream_audio": self.audio_player.is_enabled if self.audio_player else False,
            "voice_id": "EXAVITQu4vr4xnSDxMaL",
        }

        await self.websocket.send(json.dumps(request))
        log_debug("message_sent")

    async def receive_loop(self) -> None:
        """Continuously receive and process messages."""
        self._receiving = True
        response_started = False
        audio_chunks = 0

        while self._receiving:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)
                msg_type = data.get("type", "")

                if msg_type == "text_chunk":
                    if not response_started:
                        print("\nHomunculy: ", end="", flush=True)
                        response_started = True
                    chunk = data.get("chunk", "")
                    print(chunk, end="", flush=True)

                elif msg_type == "audio_chunk":
                    audio_b64 = data.get("data", "")
                    if audio_b64 and self.audio_player:
                        audio_bytes = base64.b64decode(audio_b64)
                        self.audio_player.queue_audio(audio_bytes)
                        audio_chunks += 1
                        log_debug("audio_queued", chunk=audio_chunks)

                elif msg_type == "complete":
                    print()
                    if audio_chunks > 0:
                        print(f"[AUDIO] {audio_chunks} chunks received")
                        if self.audio_player:
                            self.audio_player.flush()
                    response_started = False
                    audio_chunks = 0
                    log_info("response_complete")

                elif msg_type == "interrupted":
                    # Immediately stop all audio when interrupted
                    if self.audio_player:
                        self.audio_player.clear_queue()
                    print("\n[INTERRUPTED]")
                    response_started = False
                    audio_chunks = 0
                    log_info("interrupted")

                elif msg_type == "error":
                    print(f"\n[ERROR] {data.get('message', 'Unknown error')}")
                    response_started = False

            except json.JSONDecodeError as e:
                log_error("json_error", error=str(e))
            except ConnectionError:
                print("\n[DISCONNECTED]")
                break

    async def close(self) -> None:
        """Close connection and cleanup."""
        self._receiving = False
        if self.websocket:
            await self.websocket.close()
        if self.audio_player:
            self.audio_player.stop()


# =============================================================================
# Main
# =============================================================================


async def async_input(prompt: str) -> str:
    """Non-blocking input using executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: input(prompt).strip())


async def main() -> None:
    """Main entry point."""
    print("=" * 60)
    print("Homunculy Chat Client")
    print("=" * 60)

    # Create audio player
    audio = AudioPlayer()
    if audio.is_enabled:
        print("[AUDIO] Real-time voice enabled")
    else:
        print("[AUDIO] Disabled (missing pyaudio or pydub)")

    # Create client
    client = ChatClient()
    client.audio_player = audio

    # Connect
    print("\nConnecting...")
    if not await client.connect():
        return

    # Get user name
    client.user_id = await async_input("Your name (or Enter for 'User'): ") or "User"
    print(f"\nHello {client.user_id}! Type 'quit' to exit.")
    print("-" * 60)

    # Start receive loop in background
    receive_task = asyncio.create_task(client.receive_loop())

    try:
        while True:
            message = await async_input(f"\n{client.user_id}: ")

            if not message:
                continue

            if message.lower() in ("quit", "exit", "bye"):
                print("\nGoodbye!")
                break

            await client.send_message(message)

    except (KeyboardInterrupt, EOFError):
        print("\n\nGoodbye!")

    finally:
        receive_task.cancel()
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
