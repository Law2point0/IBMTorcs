import ollama
from ollama import ResponseError
from httpx import ConnectError

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
      ],
      stream=True
    )

    for chunk in response:
      print(chunk['message']['content'], end='', flush=True)
    
    print()
  except ResponseError:
    print(f'Ollama error, make sure you have pulled granite using: ollama pull {MODEL}')
  except ConnectError:
    print('Ollama error, make sure ollama is running in the background.')
