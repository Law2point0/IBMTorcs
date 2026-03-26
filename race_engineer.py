import ollama
from httpx import ConnectError
import time
from shared import chatbot_queue, chatbot_request_queue, SECRET_QUIT_PHRASE, server_data
import queue

GRANITE_TINY = 'hf.co/ibm-granite/granite-4.0-h-tiny-GGUF:Q4_K_M'
GRANITE_MICRO = 'hf.co/ibm-granite/granite-4.0-micro-GGUF:Q4_K_M'

MODEL = GRANITE_MICRO
AI_PROMPT = 'You are a race engineer. Keep to 1-3 small, simple sentences, response time is very important so keep it short. You will be provided with data from the car. Comment like you are a real engineer, do not talk in terms of variables or data.'


def prompt_model(prompt, data):
  try:
    response = ollama.chat(
      model=MODEL,
      messages=[
        {
          'role': 'system',
          'content': AI_PROMPT
        },
        {
          'role': 'user',
          'content': f'{prompt}\n{data}'
        }
      ]
    )

    reply = response['message']['content']
    print(f"[DEBUG] reply: {reply}")
    return reply
  except ollama.ResponseError:
    print(f'Ollama error, make sure you have pulled granite using: ollama pull {MODEL}')
  except ConnectError:
    print('Ollama error, make sure ollama is running in the background.')


def race_engineer_thread():
  running = True
  while running:
    time.sleep(0.1)
    try:
      msg = chatbot_request_queue.get_nowait()

      if msg == SECRET_QUIT_PHRASE:
        running = False
      else:
        chatbot_queue.put(prompt_model(msg, server_data))
    except queue.Empty:
      continue
    