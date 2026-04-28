import ollama
from httpx import ConnectError
import time
from runtime.shared import chatbot_queue, chatbot_request_queue, server_data
import queue

GRANITE_TINY = 'hf.co/ibm-granite/granite-4.0-h-tiny-GGUF:Q4_K_M'
GRANITE_MICRO = 'hf.co/ibm-granite/granite-4.0-micro-GGUF:Q4_K_M'

MODEL = GRANITE_MICRO
AI_PROMPT = 'You are a race engineer. Keep to 1-3 small, simple sentences, response time is very important so keep it short. You will be provided with data from the car. Comment like you are a real engineer, do not talk in terms of variables or data.'
'''AI_PROMPT = """Act as a professional race engineer.
                Only answer questions related to racing.
                Give short one scentence answers.
                Keep answers on the topic of racing.
                values will be passed at runtime.
                Do not make up any values.
                If you are not certain about the value then output "Value not found".
                If the centering value is greater than or equal to one OR the centering value is less than or equal to negative one, the car is off the track.
                Centering value should be close to 0.
                Centering value should be less than 1.
                Centering value should be more than -1 
                
                Text:"What is my speed?"
                Output:"Your speed is 20km/h."
                Text:"What position am I in?"
                Output:"You are in 1st.Keep it up."
                Text:"Am I exceeding track limits?"
                Output:"Based on the centering we are not off the track"
                Text:"What is my current lap time?"
                Output:"Your current lap time so far is 85 seconds"
                Text:"What is our last lap time?"
                Output:"Our last lap time was 98 seconds."
                """
'''

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
    #print(f"[DEBUG] reply: {reply}")
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

      if msg == 'quit':
        running = False
      else:
        if not server_data:
          print("[DEBUG] No server data yet, sending waiting message to chatbot.")
          chatbot_queue.put("Waiting for TORCS...")
        else:
          print(f"[DEBUG] Received message from chatbot_request_queue: {msg}")
          chatbot_queue.put(prompt_model(msg, server_data))
    except queue.Empty:
      continue
    