import pyttsx3

# 1. Initialize
tts_engine = pyttsx3.init()

# 2. List available voices
voices = tts_engine.getProperty('voices')
print("Available voices:")
for idx, v in enumerate(voices):
    # On macOS, v.languages is a list like [b'\x05en_US']
    langs = [lang.decode('utf-8', 'ignore') if isinstance(lang, bytes) else lang
             for lang in getattr(v, 'languages', [])]
    print(f"{idx}: id={v.id!r}, name={v.name!r}, langs={langs}, gender={v.gender}")

# 3. Pick an English voice
#   e.g. look for 'en_' in languages, or 'English' in the name
english_voice = None
for v in voices:
    langs = getattr(v, 'languages', [])
    # macOS voices report languages as bytes; Windows as strings
    if any(('en' in (lang.decode() if isinstance(lang, bytes) else lang))
           for lang in langs) or 'English' in v.name:
        english_voice = v.id
        break

if not english_voice:
    raise RuntimeError("No English voice found on this system")

# 4. Set it
tts_engine.setProperty('voice', english_voice)

# 5. (Optional) adjust rate or volume
tts_engine.setProperty('rate', 150)    # default ~200 wpm
tts_engine.setProperty('volume', 1.0)  # min=0.0, max=1.0

# 6. Test
tts_engine.say("Hello! This is now speaking in English.")
tts_engine.runAndWait()
