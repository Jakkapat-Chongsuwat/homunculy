"""
Direct TTS test - Generate voice and save to MP3 file.
"""
import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from internal.infrastructure.tts.elevenlabs_service import ElevenLabsTTSService


async def test_tts():
    """Test TTS voice generation and save to file."""
    
    # Get API key from environment
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not set in environment")
        return
    
    print("================================")
    print("Direct TTS Voice Generation Test")
    print("================================\n")
    
    # Initialize TTS service
    print("[1/4] Initializing ElevenLabs TTS service...")
    tts_service = ElevenLabsTTSService(api_key=api_key)
    print("✓ TTS service initialized\n")
    
    # List available voices
    print("[2/4] Fetching available voices...")
    voices = await tts_service.get_voices()
    
    if not voices:
        print("❌ No voices available")
        return
    
    print(f"✓ Found {len(voices)} voices:")
    for i, voice in enumerate(voices[:5], 1):
        print(f"  {i}. {voice['name']} (ID: {voice['voice_id']})")
    print()
    
    # Use first voice for testing
    test_voice = voices[0]
    voice_id = test_voice['voice_id']
    voice_name = test_voice['name']
    
    # Generate speech
    test_text = "Hello! I am Homunculy, your AI assistant. This is a test of the ElevenLabs text-to-speech integration using Clean Architecture principles."
    
    print(f"[3/4] Generating speech with voice '{voice_name}'...")
    print(f"Text: {test_text}\n")
    
    audio_bytes = await tts_service.synthesize(
        text=test_text,
        voice_id=voice_id,
        stability=0.5,
        similarity_boost=0.75,
    )
    
    print(f"✓ Generated {len(audio_bytes):,} bytes of audio\n")
    
    # Save to file
    output_file = "test_voice_output.mp3"
    print(f"[4/4] Saving audio to '{output_file}'...")
    
    with open(output_file, 'wb') as f:
        f.write(audio_bytes)
    
    file_size_kb = len(audio_bytes) / 1024
    print(f"✓ Audio saved successfully ({file_size_kb:.2f} KB)\n")
    
    print("================================")
    print("✓ TTS Test Complete!")
    print("================================\n")
    print(f"To play the audio:")
    print(f"  Windows: start {output_file}")
    print(f"  macOS: open {output_file}")
    print(f"  Linux: xdg-open {output_file}")
    print()


if __name__ == "__main__":
    asyncio.run(test_tts())
