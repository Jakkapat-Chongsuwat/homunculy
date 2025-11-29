"""
Audio Components.

Handles MP3 decoding and PCM playback.
"""

import os
import queue
import threading
from io import BytesIO
from typing import Any, Optional

from config import AUDIO


class Mp3Decoder:
    """Decode MP3 bytes to raw PCM."""

    MIN_VALID_SIZE = 100

    def __init__(self) -> None:
        self._configure_ffmpeg()

    def decode(self, mp3_data: bytes) -> Optional[bytes]:
        """Decode MP3 to PCM bytes."""
        if not self._is_valid_size(mp3_data):
            return None
        return self._decode_audio(mp3_data)

    def _is_valid_size(self, data: bytes) -> bool:
        """Check if data is large enough."""
        return len(data) >= self.MIN_VALID_SIZE

    def _decode_audio(self, mp3_data: bytes) -> Optional[bytes]:
        """Decode and normalize audio."""
        try:
            audio = self._load_mp3(mp3_data)
            audio = self._normalize(audio)
            return audio.raw_data
        except (OSError, IOError):
            return None

    def _load_mp3(self, data: bytes) -> Any:
        """Load MP3 from bytes."""
        from pydub import AudioSegment  # type: ignore[import-untyped]

        return AudioSegment.from_mp3(BytesIO(data))  # type: ignore[no-any-return]

    def _normalize(self, audio: Any) -> Any:
        """Normalize audio format."""
        audio = audio.set_frame_rate(AUDIO.sample_rate)
        audio = audio.set_channels(AUDIO.channels)
        audio = audio.set_sample_width(AUDIO.sample_width)
        audio = audio + AUDIO.volume_boost
        return audio

    def _configure_ffmpeg(self) -> None:
        """Configure ffmpeg path."""
        paths = self._get_ffmpeg_paths()
        self._set_first_valid_path(paths)

    def _get_ffmpeg_paths(self) -> list[str]:
        """Get possible ffmpeg paths."""
        return [
            r"C:\Users\Jakkapat\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe",
            r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
        ]

    def _set_first_valid_path(self, paths: list[str]) -> None:
        """Set first valid ffmpeg path."""
        from pydub import AudioSegment  # type: ignore[import-untyped]

        for path in paths:
            if os.path.exists(path):
                AudioSegment.converter = path
                return


class AudioBuffer:
    """Thread-safe buffer for MP3 chunks."""

    def __init__(self) -> None:
        self._buffer = bytearray()
        self._lock = threading.Lock()

    def add(self, data: bytes) -> None:
        """Add data to buffer."""
        with self._lock:
            self._buffer.extend(data)

    def size(self) -> int:
        """Get current buffer size."""
        with self._lock:
            return len(self._buffer)

    def extract(self) -> bytes:
        """Extract and clear buffer."""
        with self._lock:
            data = bytes(self._buffer)
            self._buffer.clear()
            return data

    def clear(self) -> None:
        """Clear the buffer."""
        with self._lock:
            self._buffer.clear()

    def is_ready(self) -> bool:
        """Check if buffer has enough data."""
        return self.size() >= AUDIO.min_buffer_size


class PreBufferTracker:
    """Track pre-buffering progress."""

    def __init__(self) -> None:
        self._bytes = 0
        self._lock = threading.Lock()
        self._ready = threading.Event()

    def add(self, size: int) -> None:
        """Add decoded bytes to count."""
        with self._lock:
            self._bytes += size
            if self._bytes >= AUDIO.pre_buffer_size:
                self._ready.set()

    def wait(self, timeout: float = 0.1) -> bool:
        """Wait for pre-buffer to be ready."""
        return self._ready.wait(timeout=timeout)

    def reset(self) -> None:
        """Reset pre-buffer state."""
        with self._lock:
            self._bytes = 0
        self._ready.clear()

    def force_ready(self) -> None:
        """Force pre-buffer to ready state."""
        self._ready.set()


class DecoderWorker:
    """Background worker that decodes MP3 to PCM."""

    FLUSH_SIGNAL = b"FLUSH"

    def __init__(
        self,
        input_queue: "queue.Queue[Optional[bytes]]",
        output_queue: "queue.Queue[bytes]",
        buffer: AudioBuffer,
        tracker: PreBufferTracker,
    ) -> None:
        self._input = input_queue
        self._output = output_queue
        self._buffer = buffer
        self._tracker = tracker
        self._decoder = Mp3Decoder()
        self._running = False

    def start(self) -> threading.Thread:
        """Start the worker thread."""
        self._running = True
        thread = threading.Thread(target=self._run, daemon=True, name="Decoder")
        thread.start()
        return thread

    def stop(self) -> None:
        """Stop the worker."""
        self._running = False

    def _run(self) -> None:
        """Main worker loop."""
        while self._running:
            self._process_next()

    def _process_next(self) -> None:
        """Process next item from queue."""
        item = self._get_item()
        if item is None:
            self._running = False
        elif item == self.FLUSH_SIGNAL:
            self._flush()
        else:
            self._buffer_and_decode(item)

    def _get_item(self) -> Optional[bytes]:
        """Get next item from queue."""
        try:
            return self._input.get(timeout=0.1)
        except queue.Empty:
            return b""

    def _flush(self) -> None:
        """Flush remaining buffer."""
        data = self._buffer.extract()
        if data:
            self._decode_and_queue(data)
        self._tracker.force_ready()

    def _buffer_and_decode(self, data: bytes) -> None:
        """Buffer data and decode when ready."""
        if not data:
            return
        self._buffer.add(data)
        if self._buffer.is_ready():
            self._decode_buffered()

    def _decode_buffered(self) -> None:
        """Decode buffered data."""
        data = self._buffer.extract()
        self._decode_and_queue(data)

    def _decode_and_queue(self, data: bytes) -> None:
        """Decode and add to output queue."""
        pcm = self._decoder.decode(data)
        if pcm:
            self._output.put(pcm)
            self._tracker.add(len(pcm))


class PlayerWorker:
    """Background worker that plays PCM audio."""

    def __init__(
        self,
        pcm_queue: "queue.Queue[bytes]",
        tracker: PreBufferTracker,
    ) -> None:
        self._queue = pcm_queue
        self._tracker = tracker
        self._pyaudio: Any = None
        self._stream: Any = None
        self._running = False

    def start(self) -> Optional[threading.Thread]:
        """Start the player thread."""
        if not self._init_pyaudio():
            return None
        self._running = True
        thread = threading.Thread(target=self._run, daemon=True, name="Player")
        thread.start()
        return thread

    def stop(self) -> None:
        """Stop the player."""
        self._running = False
        self._tracker.force_ready()

    def cleanup(self) -> None:
        """Clean up audio resources."""
        self._close_stream()
        self._terminate_pyaudio()

    def _init_pyaudio(self) -> bool:
        """Initialize PyAudio."""
        try:
            import pyaudio  # type: ignore[import-not-found]

            self._pyaudio = pyaudio.PyAudio()
            return True
        except ImportError:
            return False

    def _run(self) -> None:
        """Main player loop."""
        self._open_stream()
        try:
            while self._running:
                self._play_next()
        finally:
            self._close_stream()

    def _open_stream(self) -> None:
        """Open audio stream."""
        self._stream = self._pyaudio.open(
            format=self._pyaudio.get_format_from_width(AUDIO.sample_width),
            channels=AUDIO.channels,
            rate=AUDIO.sample_rate,
            output=True,
            frames_per_buffer=AUDIO.frame_buffer,
        )

    def _play_next(self) -> None:
        """Play next PCM chunk."""
        if not self._tracker.wait(timeout=0.1):
            return
        pcm = self._get_pcm()
        if pcm:
            self._play(pcm)

    def _get_pcm(self) -> Optional[bytes]:
        """Get next PCM data."""
        try:
            return self._queue.get(timeout=0.05)
        except queue.Empty:
            return None

    def _play(self, pcm: bytes) -> None:
        """Write PCM to stream."""
        if self._stream:
            self._stream.write(pcm)

    def _close_stream(self) -> None:
        """Close audio stream."""
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None

    def _terminate_pyaudio(self) -> None:
        """Terminate PyAudio."""
        if self._pyaudio:
            self._pyaudio.terminate()
            self._pyaudio = None


class AudioPlayer:
    """Orchestrates audio decoding and playback."""

    def __init__(self) -> None:
        self._chunk_queue: queue.Queue[Optional[bytes]] = queue.Queue()
        self._pcm_queue: queue.Queue[bytes] = queue.Queue()
        self._buffer = AudioBuffer()
        self._tracker = PreBufferTracker()
        self._decoder: DecoderWorker
        self._player: PlayerWorker
        self._decoder_thread: Optional[threading.Thread] = None
        self._player_thread: Optional[threading.Thread] = None
        self._enabled = False
        self._initialize()

    @property
    def is_enabled(self) -> bool:
        """Check if audio is enabled."""
        return self._enabled

    def queue_audio(self, mp3_data: bytes) -> None:
        """Queue MP3 data for playback."""
        if self._enabled:
            self._chunk_queue.put(mp3_data)

    def flush(self) -> None:
        """Flush remaining audio."""
        if self._enabled:
            self._chunk_queue.put(DecoderWorker.FLUSH_SIGNAL)

    def reset_for_new_message(self) -> None:
        """Reset state for new message."""
        self._clear_queues()
        self._buffer.clear()
        self._tracker.reset()

    def stop(self) -> None:
        """Stop and cleanup."""
        self._stop_workers()
        self._join_threads()
        self._cleanup_player()

    def _initialize(self) -> None:
        """Initialize audio system."""
        self._decoder = self._create_decoder()
        self._player = self._create_player()
        self._start_workers()

    def _create_decoder(self) -> DecoderWorker:
        """Create decoder worker."""
        return DecoderWorker(
            self._chunk_queue,
            self._pcm_queue,
            self._buffer,
            self._tracker,
        )

    def _create_player(self) -> PlayerWorker:
        """Create player worker."""
        return PlayerWorker(self._pcm_queue, self._tracker)

    def _start_workers(self) -> None:
        """Start worker threads."""
        self._decoder_thread = self._decoder.start()
        self._player_thread = self._player.start()
        self._enabled = self._player_thread is not None

    def _clear_queues(self) -> None:
        """Clear all queues."""
        while not self._chunk_queue.empty():
            try:
                self._chunk_queue.get_nowait()
            except queue.Empty:
                break
        while not self._pcm_queue.empty():
            try:
                self._pcm_queue.get_nowait()
            except queue.Empty:
                break

    def _stop_workers(self) -> None:
        """Stop worker threads."""
        if self._decoder:
            self._decoder.stop()
        if self._player:
            self._player.stop()
        self._chunk_queue.put(None)

    def _join_threads(self) -> None:
        """Wait for threads to finish."""
        self._join_thread(self._decoder_thread)
        self._join_thread(self._player_thread)

    def _join_thread(self, thread: Optional[threading.Thread]) -> None:
        """Join a thread with timeout."""
        if thread and thread.is_alive():
            thread.join(timeout=1.0)

    def _cleanup_player(self) -> None:
        """Cleanup player resources."""
        if self._player:
            self._player.cleanup()
