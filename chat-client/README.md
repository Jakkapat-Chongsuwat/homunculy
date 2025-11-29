# Chat Client

A fast interactive WebSocket chat client with real-time audio playback.

## Features

- Real-time streaming chat with LLM
- Audio playback via ElevenLabs TTS
- Human-in-the-loop interruption (send new message stops current audio)
- Low-latency pre-buffering

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python chat_client.py
```

Or with debug logging:

```bash
DEBUG=1 python chat_client.py
```

## Requirements

- Python 3.11+
- PyAudio (for audio playback)
- Pydub (for MP3 decoding)
- websockets

## Configuration

Edit `config.py` to change:
- WebSocket URI
- Voice ID
- Audio settings
- Model settings
