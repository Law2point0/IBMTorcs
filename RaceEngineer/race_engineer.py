import queue
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
from faster_whisper import WhisperModel
import tempfile


WAKE_WORD = "computer"
MODEL_SIZE = "small"

SAMPLE_RATE = 16000
CHANNELS = 1

CHUNK_SECONDS = 1.2
SILENCE_LIMIT = 1.0
ENERGY_THRESHOLD = 0.6

model = WhisperModel(MODEL_SIZE, compute_type="int8")

audio_queue = queue.Queue()


def audio_callback(indata, frames, time_info, status):
  audio_queue.put(indata.copy())


def get_audio(seconds):
  frames_needed = int(SAMPLE_RATE * seconds)
  frames = []

  while sum(len(f) for f in frames) < frames_needed:
    frames.append(audio_queue.get()) 

  return np.concatenate(frames).flatten()


def rms_energy(audio):
  return np.sqrt(np.mean(audio**2))


def transcribe(audio):
  with tempfile.NamedTemporaryFile(suffix=".wav") as f:
    write(f.name, SAMPLE_RATE, audio)
    segments, _ = model.transcribe(f.name)
    return " ".join(seg.text for seg in segments).lower()


def record_until_silence():
  recorded = []
  silence_time = 0

  while True:
    chunk = get_audio(0.2)
    energy = rms_energy(chunk)

    if energy > ENERGY_THRESHOLD:
      recorded.append(chunk)
      silence_time = 0
    else:
      silence_time += 0.2
      if silence_time >= SILENCE_LIMIT:
        break

  if not recorded:
    return None

  return np.concatenate(recorded)


def main():
  with sd.InputStream(
    samplerate=SAMPLE_RATE,
    channels=CHANNELS,
    callback=audio_callback,
    blocksize=1024,
  ):
    while True:
      chunk = get_audio(CHUNK_SECONDS)
      text = transcribe(chunk)

      if text:
        print("Heard:", text)

      if WAKE_WORD in text:
        print("Wake word detected!")

        command_audio = record_until_silence()
        if command_audio is not None:
          command = transcribe(command_audio)
          print("Command:", command)

        print("\nWaiting for wake word...\n")

if __name__ == "__main__":
  main()