import pyttsx3
import sys

# Initialize TTS engine globally within this module
try:
    tts_engine = pyttsx3.init()
    # Consider making the voice ID configurable
    tts_engine.setProperty('voice', 'com.apple.eloquence.en-GB.Sandy')
    # Optional: Adjust rate or volume if needed
    # tts_engine.setProperty('rate', 150)
    # tts_engine.setProperty('volume', 1.0)
except Exception as e:
    print(f"Error initializing TTS engine: {e}", file=sys.stderr)
    tts_engine = None

def speak(text: str):
    """Block until speech is finished."""
    if tts_engine:
        try:
            tts_engine.say(text)
            tts_engine.runAndWait()
        except Exception as e:
            print(f"Error during TTS playback: {e}", file=sys.stderr)
    else:
        print("TTS engine not available.", file=sys.stderr)
        # Fallback: print the text if TTS fails
        print(f"Assistant (TTS failed): {text}")

# Optional: Add a function to clean up the engine if needed, though often not necessary
# def cleanup_tts():
#     if tts_engine:
#         # pyttsx3 doesn't have an explicit stop/cleanup in the typical sense,
#         # but runAndWait handles finishing the queue.
#         pass
