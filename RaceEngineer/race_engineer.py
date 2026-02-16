import ollama
from ollama import ResponseError
import httpx
import speech_recognition as sr

r = sr.Recognizer()


if __name__ == "__main__":
  try:
    while True:
      with sr.Microphone() as source:
        print('Listening...')
        while True:
          try:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, phrase_time_limit=3)
            text = r.recognize_google(audio)
            text = text.lower()
            break
          except sr.UnknownValueError:
            pass

        print(f'You said: {text}')

      response = ollama.chat(
        model='hf.co/ibm-granite/granite-4.0-h-tiny-GGUF:Q4_K_M',
        messages=[
          {'role': 'system', 'content': 'You are a race engineer who will provide coaching tips based off of a stream of telemetry data from TORCS. Please provide short responses on what the car should do.'},
          {'role': 'user', 'content': text}
        ],
        stream=True
      )

      for chunk in response:
        print(chunk['message']['content'], end='', flush=True)
  except ResponseError:
    print('Ollama error, make sure you have pulled granite using: ollama pull hf.co/ibm-granite/granite-4.0-h-tiny-GGUF:Q4_K_M')
  except httpx.ConnectError:
    print('Ollama error, make sure ollama is running in the background.')
  except KeyboardInterrupt:
    print('Exiting...')