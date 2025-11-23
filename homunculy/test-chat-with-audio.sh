#!/bin/bash
# Test chat with optional TTS audio response

set -e

echo "🎤 Testing Chat with Optional Audio..."
echo ""
echo "Test 1: Text only (include_audio=false)"
echo "========================================"

RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/agents/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "text-only-test",
    "message": "Hello! Please introduce yourself briefly.",
    "configuration": {
      "provider": "langraph",
      "model_name": "gpt-4o-mini",
      "personality": {
        "name": "Homunculy",
        "description": "AI Assistant",
        "traits": {},
        "mood": "friendly"
      },
      "system_prompt": "You are Homunculy, a friendly AI assistant.",
      "temperature": 0.7,
      "max_tokens": 100
    },
    "context": {},
    "include_audio": false
  }')

echo "📝 Response (text only):"
echo "$RESPONSE" | python -m json.tool
echo ""
echo ""

echo "Test 2: Text + Audio (include_audio=true)"
echo "=========================================="

RESPONSE_WITH_AUDIO=$(curl -s -X POST http://localhost:8000/api/v1/agents/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "audio-test",
    "message": "Hello! Please introduce yourself briefly.",
    "configuration": {
      "provider": "langraph",
      "model_name": "gpt-4o-mini",
      "personality": {
        "name": "Homunculy",
        "description": "AI Assistant",
        "traits": {},
        "mood": "friendly"
      },
      "system_prompt": "You are Homunculy, a friendly AI assistant.",
      "temperature": 0.7,
      "max_tokens": 100
    },
    "context": {},
    "include_audio": true
  }')

# Extract audio data using Python
AUDIO_DATA=$(echo "$RESPONSE_WITH_AUDIO" | python -c "import sys, json; data=json.load(sys.stdin); audio=data.get('audio'); print(audio.get('data', '') if audio else '')")

if [ -n "$AUDIO_DATA" ]; then
    echo "✅ Audio found!"
    echo ""
    echo "📝 Response metadata:"
    echo "$RESPONSE_WITH_AUDIO" | python -c "import sys, json; data=json.load(sys.stdin); audio=data.get('audio'); print(json.dumps({'format': audio.get('format'), 'encoding': audio.get('encoding'), 'size_bytes': audio.get('size_bytes'), 'voice_id': audio.get('voice_id')}, indent=2) if audio else 'No audio')"
    echo ""
    
    echo "🔊 Decoding and saving audio..."
    echo "$AUDIO_DATA" | base64 -d > chat_response.mp3
    
    FILE_SIZE=$(stat -f%z chat_response.mp3 2>/dev/null || stat -c%s chat_response.mp3 2>/dev/null || wc -c < chat_response.mp3)
    echo "✅ Audio saved: chat_response.mp3 (${FILE_SIZE} bytes)"
    echo ""
    echo "▶️  Playing audio..."
    
    # Play on Windows
    if command -v cmd.exe &> /dev/null; then
        cmd.exe /c start chat_response.mp3
        echo "✅ Audio playing in default media player!"
    else
        echo "Audio saved. Open chat_response.mp3 to play."
    fi
else
    echo "❌ No audio in response"
    echo ""
    echo "Full response:"
    echo "$RESPONSE_WITH_AUDIO" | python -m json.tool
fi

