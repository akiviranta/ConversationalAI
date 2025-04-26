"""
Main script for the Museum Assistant.
Orchestrates ASR, LLM, and TTS components.
"""
import os
import sys
import sounddevice as sd
from vosk import Model # Keep Model import here for loading

# Import functions from our new modules
from asr_client import listen_until_pause, callback, q # Import queue and callback too
from tts_client import speak
from ollama_client import query_ollama

# Constants remain here
MODEL_PATH     = "asr_model"
SAMPLE_RATE    = 16000
PAUSE_TIMEOUT  = 2.0 # seconds of silence to trigger LLM
MODEL_NAME = "gemma3:1b-it-qat"


if __name__ == "__main__":
    # --- Vosk Model Loading ---
    if not os.path.exists(MODEL_PATH):
        print(f"Please download the Vosk model into '{MODEL_PATH}'")
        sys.exit(1)
    try:
        model = Model(MODEL_PATH)
        print("Vosk model loaded successfully.")
    except Exception as e:
        print(f"Error loading Vosk model from {MODEL_PATH}: {e}", file=sys.stderr)
        sys.exit(1)

    # --- Conversation History ---
    conversation_history = []

    # --- Audio Stream Setup ---
    # Use the imported callback and queue from asr_client
    try:
        stream = sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            blocksize=8000, # Keep blocksize reasonable
            device=None, # Default device
            dtype='int16',
            channels=1,
            callback=callback # Use the imported callback
        )
        print("Audio stream opened.")
    except Exception as e:
        print(f"Error opening audio stream: {e}", file=sys.stderr)
        sys.exit(1)


    # --- Main Loop ---
    try:
        with stream: # Use context manager for cleaner start/stop
            while True:
                # ——— TURN 1: Listening ———
                # Stream is managed by the 'with' block, just call listen
                # Pass the loaded model, sample rate, and timeout
                user_input = listen_until_pause(model, SAMPLE_RATE, PAUSE_TIMEOUT)

                if not user_input: # Handle case where listening might fail or return empty
                    print("No input detected.")
                    continue

                # ——— TURN 2: Thinking ———
                print("\n🤖 Thinking...")
                # Pass history to the imported query_ollama
                reply = query_ollama(user_input, conversation_history, MODEL_NAME)
                print(f"\n🧠 Assistant: {reply}\n")

                # ——— TURN 3: Answering ———
                # Use the imported speak function
                speak(reply)
                print() # Add a newline for clarity

                # --- Update History ---
                conversation_history.append(f"USER: {user_input}")
                conversation_history.append(f"ASSISTANT: {reply}")
                # Optional: Limit history size
                # MAX_HISTORY_TURNS = 5
                # if len(conversation_history) > MAX_HISTORY_TURNS * 2:
                #     conversation_history = conversation_history[-(MAX_HISTORY_TURNS * 2):]

    except KeyboardInterrupt:
        print("\nExiting.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)
    finally:
        # The 'with stream:' block handles closing, but explicit close is safe
        if 'stream' in locals() and not stream.closed:
             stream.close()
             print("Audio stream closed.")
        # Optional: Call any cleanup needed for other modules
        # cleanup_tts()
        sys.exit(0)
