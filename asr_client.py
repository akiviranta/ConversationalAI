import queue
import sounddevice as sd
import sys
import time
import numpy as np # Import numpy for audio processing
from faster_whisper import WhisperModel # Import WhisperModel

# --- Configuration ---
# Choose the model size (e.g., "tiny.en", "base.en", "small.en", "medium.en")
# Smaller models are faster but less accurate. ".en" models are English-only.
WHISPER_MODEL_SIZE = "base.en"
# Set compute type ("int8", "float16", "float32"). "int8" is often fastest on CPU/GPU.
# On Apple Silicon (M1/M2/M3), "float16" might be good, or let it default.
COMPUTE_TYPE = "default" # Let faster-whisper choose based on device
DEVICE = "cpu" # Can be "cpu" or "cuda" if you have NVIDIA GPU + CUDA toolkit

# --- Load Model Globally ---
# This loads the model once when the module is imported, improving performance.
# It will download the model on the first run if not cached.
try:
    print(f"Loading faster-whisper model: {WHISPER_MODEL_SIZE}...")
    whisper_model = WhisperModel(WHISPER_MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
    print("Faster-whisper model loaded successfully.")
except Exception as e:
    print(f"Error loading faster-whisper model: {e}", file=sys.stderr)
    whisper_model = None # Set to None if loading fails

# Global queue for audio data (remains the same)
q = queue.Queue()

def callback(indata, frames, time_info, status):
    """SoundDevice callback: push raw audio into queue."""
    if status:
        print(status, file=sys.stderr)
    # Put raw bytes data into the queue
    q.put(bytes(indata))

# --- Simplified Listening Function ---
def listen_until_pause(sample_rate: int) -> str: # Removed pause_timeout
    """
    Listen from mic, accumulate audio when sound is detected,
    and transcribe using faster-whisper when the sound stops.
    """
    if not whisper_model:
        print("Whisper model not loaded. Cannot transcribe.", file=sys.stderr)
        return ""

    audio_buffer = []  # Store chunks of audio data (bytes)
    triggered = False  # Flag to indicate if we've started accumulating meaningful audio

    # Flush any old audio in queue
    while not q.empty():
        try:
            q.get_nowait()
        except queue.Empty:
            break

    print("🎤 Listening... (speak to start, stop to send)")

    SILENCE_THRESHOLD = 100  # You may need to tune this

    while True:
        try:
            # Get data with a short timeout
            data = q.get(timeout=0.2) # Increased timeout slightly
            if data:
                audio_np = np.frombuffer(data, dtype=np.int16)
                amplitude = np.abs(audio_np).mean()
                print(amplitude)

                if amplitude > SILENCE_THRESHOLD:
                    if not triggered:
                        print("Recording started...")
                        triggered = True
                        audio_buffer = [data] # Start buffer *only* when triggered
                    else:
                        audio_buffer.append(data) # Append subsequent data
                    # print(".", end="", flush=True) # Optional: visual feedback
                elif triggered:
                    # Append data below threshold only if already triggered
                    # This helps capture the tail end of speech
                    audio_buffer.append(data)

        except queue.Empty:
            # Queue is empty - check if we were triggered
            if triggered:
                print(f"\nSilence detected. Transcribing...")

                # Combine all collected audio chunks
                full_audio_data = b"".join(audio_buffer)

                # Reset buffer and triggered flag *before* transcription attempt
                audio_buffer = []
                triggered = False # Reset triggered status

                if not full_audio_data:
                    print("No audio data captured despite trigger.")
                    print("🎤 Listening again...")
                    continue # Continue listening

                # --- Transcription Process ---
                try:
                    # Convert raw bytes to NumPy array of int16
                    audio_np = np.frombuffer(full_audio_data, dtype=np.int16)
                    # Convert to float32 and normalize to [-1.0, 1.0]
                    audio_fp32 = audio_np.astype(np.float32) / 32768.0

                    segments, info = whisper_model.transcribe(
                        audio_fp32,
                        language="en",
                        beam_size=5,
                        vad_filter=True, # Keep VAD
                        vad_parameters=dict(min_silence_duration_ms=100) # Shorter VAD silence
                    )
                    transcript = "".join(segment.text for segment in segments).strip()
                    print(f"\r> You: {transcript}                                  ")
                    return transcript # Return the transcript

                except Exception as e:
                    print(f"\nError during transcription: {e}", file=sys.stderr)
                    return "" # Return empty on error
            else:
                # Queue is empty, but we weren't triggered (silence before speech)
                pass # Continue listening silently

        # Add a small sleep to prevent high CPU usage when idle
        time.sleep(0.01)

# Note: The main part of your script that calls this function
# will need to be updated to call listen_until_pause(sample_rate)
# without the pause_timeout argument.