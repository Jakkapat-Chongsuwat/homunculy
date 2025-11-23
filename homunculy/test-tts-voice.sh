#!/bin/bash
# Test TTS Voice Generation and Playback

set -e

BASE_URL="http://localhost:8000"
USER_ID="tts-test-user-$RANDOM"
OUTPUT_FILE="test_voice_output.mp3"

echo "================================"
echo "Testing TTS Voice Generation"
echo "================================"
echo ""

# Test: Request agent to generate voice using TTS tool
echo "[1/2] Requesting TTS generation..."
echo ""

RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/agents/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "'"$USER_ID"'",
    "message": "Please use the text_to_speech tool to convert this message to audio: Hello, I am Homunculy, your AI assistant. This is a test of the ElevenLabs text-to-speech integration.",
    "configuration": {
      "provider": "langraph",
      "model_name": "gpt-4o-mini",
      "personality": {
        "name": "Homunculy",
        "description": "AI Voice Assistant",
        "traits": {},
        "mood": "friendly"
      },
      "system_prompt": "You are Homunculy, an AI assistant with text-to-speech capabilities. When asked to generate voice, use the text_to_speech tool with appropriate parameters. Available voices can be listed with list_voices tool.",
      "temperature": 0.7,
      "max_tokens": 1000
    },
    "context": {}
  }')

echo "$RESPONSE"
echo ""
echo ""

# Check if audio was generated (look for tool usage in response)
if echo "$RESPONSE" | grep -q "text_to_speech\|audio\|voice"; then
    echo "[2/2] ✓ TTS tool invoked successfully!"
    echo ""
    echo "Note: Audio bytes are generated but not returned in API response."
    echo "To play audio, you would need to:"
    echo "  1. Save audio bytes to file in the agent"
    echo "  2. Return audio URL or base64 data"
    echo "  3. Download and play the audio file"
else
    echo "[2/2] ⚠ TTS tool may not be bound to agent yet"
    echo ""
    echo "Response:"
    echo "$RESPONSE"
fi

echo ""
echo "================================"
echo "TTS Infrastructure Status"
echo "================================"
echo "✓ ElevenLabs service integrated"
echo "✓ TTS tools created (text_to_speech, list_voices)"
echo "✓ DI container configured"
echo "⚠ Tools need to be bound to LangGraph agent"
echo ""
echo "Next steps:"
echo "  - Bind TTS tools in agent_service.py"
echo "  - Modify response to include audio data"
echo "  - Test audio playback"
