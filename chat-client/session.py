"""
WebSocket Message Handling.

Handles sending and receiving WebSocket messages.
"""

import asyncio
import base64
import json
from dataclasses import dataclass, field
from typing import Any, Optional

from config import AGENT, SERVER
from audio import AudioPlayer


class MessageSender:
    """Send messages to WebSocket."""

    def __init__(self, websocket: Any, user_id: str, audio_enabled: bool) -> None:
        self._ws = websocket
        self._user_id = user_id
        self._audio_enabled = audio_enabled

    async def send_chat(self, message: str) -> None:
        """Send chat message."""
        request = self._build_request(message)
        await self._send(request)

    def _build_request(self, message: str) -> dict[str, Any]:
        """Build chat request."""
        return {
            "type": "chat_request",
            "user_id": self._user_id,
            "message": message,
            "configuration": self._build_config(),
            "context": {},
            "stream_audio": self._audio_enabled,
            "voice_id": AGENT.voice_id,
        }

    def _build_config(self) -> dict[str, Any]:
        """Build agent configuration."""
        return {
            "provider": AGENT.provider,
            "model_name": AGENT.model_name,
            "personality": self._build_personality(),
            "system_prompt": AGENT.system_prompt,
            "temperature": AGENT.temperature,
            "max_tokens": AGENT.max_tokens,
        }

    def _build_personality(self) -> dict[str, Any]:
        """Build personality config."""
        return {
            "name": AGENT.personality_name,
            "description": AGENT.personality_description,
            "traits": {},
            "mood": AGENT.personality_mood,
        }

    async def _send(self, request: dict[str, Any]) -> None:
        """Send JSON request."""
        await self._ws.send(json.dumps(request))


class MessageReceiver:
    """Receive and route WebSocket messages."""

    def __init__(self, websocket: Any, audio_player: Optional[AudioPlayer]) -> None:
        self._ws = websocket
        self._audio = audio_player
        self._response_started = False
        self._audio_chunks = 0

    async def receive_loop(self) -> None:
        """Main receive loop."""
        while True:
            message = await self._receive()
            if message is None:
                break
            self._route(message)

    async def _receive(self) -> Optional[dict[str, Any]]:
        """Receive one message."""
        try:
            raw = await self._ws.recv()
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
        except ConnectionError:
            print("\n[DISCONNECTED]")
            return None

    def _route(self, data: dict[str, Any]) -> None:
        """Route message to handler."""
        msg_type = data.get("type", "")
        handlers: dict[str, Any] = {
            "text_chunk": self._handle_text,
            "audio_chunk": self._handle_audio,
            "complete": self._handle_complete,
            "interrupted": self._handle_interrupted,
            "error": self._handle_error,
        }
        handler = handlers.get(msg_type)
        if handler:
            handler(data)

    def _handle_text(self, data: dict[str, Any]) -> None:
        """Handle text chunk."""
        self._ensure_response_started()
        self._print_chunk(data)

    def _ensure_response_started(self) -> None:
        """Ensure response header is printed."""
        if not self._response_started:
            print("\nHomunculy: ", end="", flush=True)
            self._response_started = True

    def _print_chunk(self, data: dict[str, Any]) -> None:
        """Print text chunk."""
        chunk = data.get("chunk", "")
        print(chunk, end="", flush=True)

    def _handle_audio(self, data: dict[str, Any]) -> None:
        """Handle audio chunk."""
        if not self._audio:
            return
        audio_bytes = self._decode_audio(data)
        if audio_bytes:
            self._queue_audio(audio_bytes)

    def _decode_audio(self, data: dict[str, Any]) -> Optional[bytes]:
        """Decode base64 audio."""
        audio_b64 = data.get("data", "")
        if not audio_b64:
            return None
        return base64.b64decode(audio_b64)

    def _queue_audio(self, audio_bytes: bytes) -> None:
        """Queue audio for playback."""
        if self._audio:
            self._audio.queue_audio(audio_bytes)
        self._audio_chunks += 1

    def _handle_complete(self, _data: dict[str, Any]) -> None:
        """Handle completion."""
        print()
        self._print_audio_summary()
        self._flush_audio()
        self._reset_state()

    def _print_audio_summary(self) -> None:
        """Print audio chunk count."""
        if self._audio_chunks > 0:
            print(f"[AUDIO] {self._audio_chunks} chunks received")

    def _flush_audio(self) -> None:
        """Flush audio buffer."""
        if self._audio and self._audio_chunks > 0:
            self._audio.flush()

    def _reset_state(self) -> None:
        """Reset receiver state."""
        self._response_started = False
        self._audio_chunks = 0

    def _handle_interrupted(self, _data: dict[str, Any]) -> None:
        """Handle interruption."""
        self._clear_audio()
        print("\n[INTERRUPTED]")
        self._reset_state()

    def _clear_audio(self) -> None:
        """Clear audio queue."""
        if self._audio:
            self._audio.reset_for_new_message()

    def _handle_error(self, data: dict[str, Any]) -> None:
        """Handle error."""
        message = data.get("message", "Unknown error")
        print(f"\n[ERROR] {message}")
        self._reset_state()


@dataclass
class ChatSession:
    """Orchestrates a chat session."""

    uri: str = SERVER.uri
    user_id: str = "User"
    _websocket: Any = field(default=None, repr=False)
    _audio: Optional[AudioPlayer] = field(default=None, repr=False)
    _sender: Optional[MessageSender] = field(default=None, repr=False)
    _receiver: Optional[MessageReceiver] = field(default=None, repr=False)

    async def connect(self) -> bool:
        """Connect to server."""
        try:
            return await self._do_connect()
        except ConnectionRefusedError:
            self._print_connection_refused()
            return False
        except OSError as e:
            self._print_connection_error(e)
            return False

    async def _do_connect(self) -> bool:
        """Perform connection."""
        import websockets

        self._websocket = await websockets.connect(self.uri)
        await self._receive_status()
        self._create_components()
        return True

    async def _receive_status(self) -> None:
        """Receive connection status."""
        status = json.loads(await self._websocket.recv())
        message = status.get("message", "Connected")
        print(f"[OK] {message}")

    def _create_components(self) -> None:
        """Create sender and receiver."""
        audio_enabled = self._audio.is_enabled if self._audio else False
        self._sender = MessageSender(self._websocket, self.user_id, audio_enabled)
        self._receiver = MessageReceiver(self._websocket, self._audio)

    def _print_connection_refused(self) -> None:
        """Print connection refused message."""
        print("[ERROR] Connection refused - is the server running?")

    def _print_connection_error(self, e: Exception) -> None:
        """Print connection error."""
        print(f"[ERROR] Connection failed: {e}")

    def set_audio(self, audio: AudioPlayer) -> None:
        """Set audio player."""
        self._audio = audio

    async def send(self, message: str) -> None:
        """Send a message."""
        self._reset_audio()
        if self._sender:
            await self._sender.send_chat(message)

    def _reset_audio(self) -> None:
        """Reset audio for new message."""
        if self._audio:
            self._audio.reset_for_new_message()

    async def receive_loop(self) -> None:
        """Run receive loop."""
        if self._receiver:
            await self._receiver.receive_loop()

    async def close(self) -> None:
        """Close session."""
        await self._close_websocket()
        self._stop_audio()

    async def _close_websocket(self) -> None:
        """Close WebSocket."""
        if self._websocket:
            await self._websocket.close()

    def _stop_audio(self) -> None:
        """Stop audio player."""
        if self._audio:
            self._audio.stop()


class ChatApp:
    """Main chat application."""

    def __init__(self) -> None:
        self._audio = AudioPlayer()
        self._session = ChatSession()

    async def run(self) -> None:
        """Run the application."""
        self._print_header()
        self._print_audio_status()
        if not await self._connect():
            return
        await self._chat_loop()

    def _print_header(self) -> None:
        """Print welcome header."""
        print("=" * 60)
        print("Homunculy Chat Client")
        print("=" * 60)

    def _print_audio_status(self) -> None:
        """Print audio status."""
        if self._audio.is_enabled:
            print("[AUDIO] Real-time voice enabled")
        else:
            print("[AUDIO] Disabled (missing pyaudio or pydub)")

    async def _connect(self) -> bool:
        """Connect to server."""
        print("\nConnecting...")
        self._session.set_audio(self._audio)
        return await self._session.connect()

    async def _chat_loop(self) -> None:
        """Main chat loop."""
        await self._get_user_name()
        self._print_welcome()
        receive_task = self._start_receiver()
        try:
            await self._input_loop()
        finally:
            await self._cleanup(receive_task)

    async def _get_user_name(self) -> None:
        """Get user name from input."""
        name = await self._async_input("Your name (or Enter for 'User'): ")
        self._session.user_id = name or "User"

    def _print_welcome(self) -> None:
        """Print welcome message."""
        print(f"\nHello {self._session.user_id}! Type 'quit' to exit.")
        print("-" * 60)

    def _start_receiver(self) -> "asyncio.Task[None]":
        """Start receive task."""
        return asyncio.create_task(self._session.receive_loop())

    async def _input_loop(self) -> None:
        """Process user input."""
        while True:
            message = await self._get_input()
            if self._should_quit(message):
                break
            if message:
                await self._session.send(message)

    async def _get_input(self) -> str:
        """Get user input."""
        prompt = f"\n{self._session.user_id}: "
        return await self._async_input(prompt)

    def _should_quit(self, message: str) -> bool:
        """Check if should quit."""
        if message.lower() in ("quit", "exit", "bye"):
            print("\nGoodbye!")
            return True
        return False

    async def _cleanup(self, receive_task: "asyncio.Task[None]") -> None:
        """Cleanup resources."""
        receive_task.cancel()
        await self._session.close()

    async def _async_input(self, prompt: str) -> str:
        """Non-blocking input."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: input(prompt).strip())
