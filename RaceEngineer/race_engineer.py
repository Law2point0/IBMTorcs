import sounddevice as sd
import queue
import json
from vosk import Model, KaldiRecognizer
import ollama
from ollama import ResponseError
import httpx

MODEL_PATH = 'big_model'
DEVICE_SAMPLE_RATE = int(sd.query_devices(None, 'input')['default_samplerate'])
SAMPLE_RATE = 16000
WAKE_WORD = 'granite'

audio_queue = queue.Queue()


def audio_callback(indata, frames, time, status):
  if status:
    print(status)
  audio_queue.put(bytes(indata))


def wait_for_wake_word(recognizer):
  print(f'Listening for {WAKE_WORD}...')

  if 0:
    while True:
      data = audio_queue.get()

      if recognizer.AcceptWaveform(data):
        result = json.loads(recognizer.Result())
        text = result.get('text', '').strip()

        if WAKE_WORD in text:
          return
  else:
    while True:
      data = audio_queue.get()

      if recognizer.AcceptWaveform(data):
        result = json.loads(recognizer.Result())
        text = result.get('text', '').strip()
        print(f'[DEBUG final] "{text}"')

        if WAKE_WORD in text:
          print(f'[DEBUG partial] "{text}"')
          return


def listen_for_command(recognizer):
  last_partial = ''

  while True:
    data = audio_queue.get()

    if recognizer.AcceptWaveform(data):
      result = json.loads(recognizer.Result())
      print()
      return result.get('text', '').strip()

    else:
      partial = json.loads(recognizer.PartialResult()).get('partial', '')

      if partial != last_partial:
        print("\r" + partial, end="", flush=True)
        last_partial = partial


def ask_granite(text):
  try:
    response = ollama.chat(
      model='hf.co/ibm-granite/granite-4.0-h-tiny-GGUF:Q4_K_M',
      messages=[
        {
          'role': 'system',
          'content': 'You are a race engineer who will provide coaching tips based off of a stream of telemetry data from TORCS. Please provide short responses on what the car should do.'
        },
        {
          'role': 'user',
          'content': text
        }
      ],
      stream=True
    )

    for chunk in response:
      print(chunk['message']['content'], end='', flush=True)

    print('\n')
  except ResponseError:
    print('Ollama error, make sure you have pulled granite using: ollama pull hf.co/ibm-granite/granite-4.0-h-tiny-GGUF:Q4_K_M')
  except httpx.ConnectError:
    print('Ollama error, make sure ollama is running in the background.')


if __name__ == "__main__":
  try:
    print(f'Device sample rate: {DEVICE_SAMPLE_RATE} Sample rate: {SAMPLE_RATE}')
    model = Model(MODEL_PATH)

    recognizer = KaldiRecognizer(model, SAMPLE_RATE)

    with sd.RawInputStream(
      samplerate=SAMPLE_RATE,
      blocksize=8000,
      dtype='int16',
      channels=1,
      callback=audio_callback
    ):
      while True:
        wait_for_wake_word(recognizer)

        command = listen_for_command(recognizer)

        if command and command != WAKE_WORD:
          ask_granite(command) 
  except KeyboardInterrupt:
    print('Exiting...')