import ollama
from ollama import ResponseError
import httpx
# from ...torcs_jm_par import get_snapshot_data

MODEL = 'hf.co/ibm-granite/granite-4.0-h-tiny-GGUF:Q4_K_M' # Granite 4.0 Tiny
AI_PROMPT = 'You are a race engineer. Keep to 1-3 small, simple sentences. You will be provided with data from the simulation. Comment like you are a real engineer, do not talk in terms of variables or data.'
EXAMPLE_TELEMETRY = "{'angle': -2.74844, 'curLapTime': 21.028, 'damage': 285.0, 'distFromStart': 471.785, 'distRaced': 481.785, 'fuel': 93.6591, 'gear': 1.0, 'lastLapTime': 0.0, 'opponents': [200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0], 'racePos': 1.0, 'rpm': 942.478, 'speedX': 0.0840397, 'speedY': -0.0265828, 'speedZ': 0.000484125, 'track': [-1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0], 'trackPos': -7.46846, 'wheelSpinVel': [0.0, 0.0, 0.0, 0.0], 'z': 0.338315, 'focus': [-1.0, -1.0, -1.0, -1.0, -1.0]}"


def prompt_model(prompt, data):
  response = ollama.chat(
    model=MODEL,
    messages=[
      {
        'role': 'system',
        'content': AI_PROMPT
      },
      {
        'role': 'user',
        'content': f'{prompt}\n\nSnapshot TORCS data: {data}'
      }
    ],
    stream=True
  )

  for chunk in response:
    print(chunk['message']['content'], end='', flush=True)
  
  print()

def main():
  try:
    while True:
      prompt = input("Chat: ")

      response = ollama.chat(
        model=MODEL,
        messages=[
          {
            'role': 'system',
            'content': AI_PROMPT
          },
          {
            'role': 'user',
            'content': f'{prompt}\n\nSnapshot TORCS data: {EXAMPLE_TELEMETRY}'
          }
        ],
        stream=True
      )

      for chunk in response:
        print(chunk['message']['content'], end='', flush=True)
      
      print()
  except ResponseError:
    print(f'Ollama error, make sure you have pulled granite using: ollama pull {MODEL}')
  except httpx.ConnectError:
    print('Ollama error, make sure ollama is running in the background.')


if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    print('Exiting...')