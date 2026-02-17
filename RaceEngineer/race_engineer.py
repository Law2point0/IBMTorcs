import ollama
from ollama import ResponseError
import httpx


MODEL = 'hf.co/ibm-granite/granite-4.0-h-tiny-GGUF:Q4_K_M' # Granite 4.0 Tiny
AI_PROMPT = ''


def main():
  try:
    while True:
      prompt = input("")

      response = ollama.chat(
        model=MODEL,
        messages=[
          {
            'role': 'system',
            'content': AI_PROMPT
          },
          {
            'role': 'user',
            'content': f'{prompt}'
          }
        ]
      )
  except ResponseError:
    print(f'Ollama error, make sure you have pulled granite using: ollama pull {MODEL}')
  except httpx.ConnectError:
    print('Ollama error, make sure ollama is running in the background.')


if __name__ == '__main__':
  main()