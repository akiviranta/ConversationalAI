import queue
import sounddevice as sd
import sys
import json
import time
from vosk import KaldiRecognizer, Model # Keep Model import here if needed for recognizer init

# Global queue for audio data
q = queue.Queue()

def callback(indata, frames, time_info, status):
    """SoundDevice callback: push raw audio into queue."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def listen_until_pause(model: Model, sample_rate: int, pause_timeout: float) -> str:
    """
    Listen from mic until the user pauses for pause_timeout,
    then return the full transcript. Requires a Vosk Model object.
    """
    buffer_text = ""
    last_spoken = time.time()

    # Flush any old audio in queue
    while not q.empty():
        try:
            q.get_nowait()
        except queue.Empty:
            break # Exit if queue becomes empty during flush

    # Initialize recognizer here, using the passed model
    recognizer = KaldiRecognizer(model, sample_rate)
    recognizer.SetWords(True) # Enable word timestamps if needed

    print("🎤 Listening... (pause ~1s to send)")
    # Note: The audio stream (sd.RawInputStream) should be managed
    # by the main script, starting/stopping it around this function call.
    while True:
        try:
            data = q.get(timeout=pause_timeout / 2) # Add a timeout to prevent blocking forever if no audio comes
        except queue.Empty:
            # Check if pause duration has been met even without new data
            if buffer_text.strip() and (time.time() - last_spoken) > pause_timeout:
                print("\nPause detected.")
                return buffer_text.strip()
            continue # Continue waiting if no text and not paused long enough

        if recognizer.AcceptWaveform(data):
            try:
                res = json.loads(recognizer.Result())
                text = res.get("text", "")
                if text:
                    buffer_text += " " + text
                    print(f"\r> {buffer_text.strip()}", end="") # Update line with full buffer
                    last_spoken = time.time()
            except json.JSONDecodeError:
                print("\nError decoding Vosk result JSON", file=sys.stderr)
        else:
            try:
                partial = json.loads(recognizer.PartialResult()).get("partial", "")
                if partial:
                    # Show partial result, overwriting previous partial
                    print(f"\rYou: {buffer_text.strip()} {partial}...", end="")
            except json.JSONDecodeError:
                 print("\nError decoding Vosk partial result JSON", file=sys.stderr)


        # Check pause condition after processing data
        if buffer_text.strip() and (time.time() - last_spoken) > pause_timeout:
             print("\nPause detected.")
             return buffer_text.strip()
