import ollama
from ollama import ResponseError

MODEL = "hf.co/ibm-granite/granite-4.0-h-micro-GGUF:Q4_K_M"
AI_PROMPT = """Act as a professional race engineer.
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
# AI_PROMPT = """You are a professional race engineer who is knowledgeable about racing.
#                 Only answer questions related to racing.
#                 Keep answers on the topic of racing.
#                 Keep answers short, remember you are speaking to a racing driver.
#                 Make sure your answers are a maximum of two small sentences.
#                 Damage points should be close to 0.
#                 Centering is how the car is positioned on the track.
#                 If the centering value is greater than or equal to one OR the centering value is less than or equal to negative one, the car is off the track.
#                 """
#AI_PROMPT2 = 'You are a race engineer. Do not talk about the simulation data, reply with simple english, response time matters so be as direct as possible whilst still forming proper sentences.'
#EXAMPLE_TELEMETRY = "{'angle': -2.74844, 'curLapTime': 21.028, 'damage': 285.0, 'distFromStart': 471.785, 'distRaced': 481.785, 'fuel': 93.6591, 'gear': 1.0, 'lastLapTime': 0.0, 'opponents': [200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0, 200.0], 'racePos': 1.0, 'rpm': 942.478, 'speedX': 0.0840397, 'speedY': -0.0265828, 'speedZ': 0.000484125, 'track': [-1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0], 'trackPos': -7.46846, 'wheelSpinVel': [0.0, 0.0, 0.0, 0.0], 'z': 0.338315, 'focus': [-1.0, -1.0, -1.0, -1.0, -1.0]}"


def prompt_model(prompt, telemetry):
  curLapTime = telemetry['curLapTime']
  damage = telemetry['damage']
  gear = telemetry['gear']
  lastLapTime = telemetry['lastLapTime']
  curPos = telemetry['racePos']
  speed = telemetry['speedX']
  centering = telemetry['trackPos']
  response = ollama.chat(
    model=MODEL,
    messages=[
      {
        'role': 'system',
        'content': AI_PROMPT
      },
      {
        'role': 'user',
        'content': f'{prompt}\ncurrent lap time in seconds is {curLapTime}\ncar damage points are {damage}\ncurrent gear is {gear}\nlast lap time in seconds was {lastLapTime}\nour current position is {curPos}\nour current speed is {speed}\n our current centering is {centering}'
      }
    ],
    stream=True
  )

  for chunk in response:
    print(chunk['message']['content'], end='', flush=True)
  
  print()