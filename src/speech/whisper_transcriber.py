from faster_whisper import WhisperModel

model = WhisperModel("base", device="cpu", compute_type="int8")  # Use "cuda" if GPU available

def transcribe_audio(audio_path: str) -> str:
    segments, _ = model.transcribe(audio_path)

    transcript = ""
    for segment in segments:
        transcript += segment.text + " "
    return transcript.strip()
