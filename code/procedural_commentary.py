import ollama
from httpx import ConnectError
import time
from shared import commentary_queue, server_data     

last_server_data = dict()   
talking_points = []

GRANITE_TINY = 'hf.co/ibm-granite/granite-4.0-h-tiny-GGUF:Q4_K_M'
GRANITE_MICRO = 'hf.co/ibm-granite/granite-4.0-micro-GGUF:Q4_K_M'

MODEL = GRANITE_MICRO
AI_PROMPT = (
  'You are an enthusiastic motorsport TV commentator. '
  'You will receive a list of notable events that just happened over the last 5-6 seconds of a race. '
  'Give 1-3 short, punchy sentences of live commentary as if talking to a TV audience. '
  'Speak naturally - do not recite numbers or event names, just describe the drama'
  'You are an enthusiastic motorsport TV commentator calling a live race. '
  'You will receive a list of notable events that just happened over the last 5-6 seconds. '
  'Give 1-3 short, punchy sentences as if speaking live to a TV audience.'
  'The race is ongoing - never use words like "finally", "at last", or "eventually". '
  'Speak naturally about what just happened, not what is coming next '
  'Do not recite numbers or variable names, just describe the action.' 
  'When crossed the finish line make emphasis on the drama of the event, make it big. ' 
)
      
sampleInterval = 0.1
windowSeconds = 9
windowSamples = int(windowSeconds / sampleInterval)

# Thresholds for change detection
speedChangeThresh = 30
speedHighThresh = 150
speedHoldSamples = 20
angleThresh = 0.3
trackEdgeThresh = 0.75
trackOffThresh = 1.0
damageThresh = 50
rpmRedline = 8500
fuelLow = 5.0


def get_speed(snap):
  v = snap.get('speedX')
  if v is None:
    return None
  return v


def detect_talking_points(samples):
  points = []

  prev = None
  high_speed_run = 0
  high_speed_reported = False
  edge_samples = 0
  off_track_samples = 0
  redline_samples = 0

  speed_at_brake_start = None
  speed_at_accel_start = None

  damage_start = 0

  for snap in samples:
    spd = get_speed(snap)

    if damage_start is None:
      damage_start = snap.get('damage', 0) or 0

    if prev is None:
      prev = snap
      continue

    prev_spd = get_speed(prev)

    ######### Gear changes #########
    gear = snap.get('gear')
    prev_gear = prev.get('gear')
    if gear is not None and prev_gear is not None and gear != prev_gear:
      #checks for up or down shift and adds to points
      direction = 'up' if gear > prev_gear else 'down'
      points.append(f"Gear shi ft {direction}: {prev_gear} -> {gear}")

    ######### Brake Detection #########
    if spd is not None and prev_spd is not None:
      delta = spd - prev_spd
      if delta < -speedChangeThresh:
        if speed_at_brake_start is None:
          speed_at_brake_start = prev_spd
        #clears acceleration event - is now breaking
        speed_at_accel_start = None

      ######### Acceleration Detection #########  
      elif delta > speedChangeThresh:
        if speed_at_accel_start is None:
          speed_at_accel_start = prev_spd
        if speed_at_brake_start is not None:
          #if we were breaking but now accelerating - repor breaking end
          points.append(f"Hard braking: {speed_at_brake_start:.0f} -> {prev_spd:.0f} km/h")
          #clears breaking
          speed_at_brake_start = None

      ######### Stable speed Accel/Break Tracking ######### 
      else:
        if speed_at_brake_start is not None:
          points.append(f"Hard braking: {speed_at_brake_start:.0f} - {spd:.0f} km/h")
          speed_at_brake_start = None
        if speed_at_accel_start is not None:
          points.append(f"Heavy acceleration: {speed_at_accel_start:.0f} -> {spd:.0f} km/h")
          speed_at_accel_start = None

      ######### Sustained high speed #########
      if spd >= speedHighThresh:
        #increments run at high speed
        high_speed_run += 1
      else:
        if high_speed_run >= speedHoldSamples:
          #reports and resets high speed run
          high_speed_reported = False
        high_speed_run = 0

      if high_speed_run >= speedHoldSamples and not high_speed_reported:
        points.append(f"Holding {spd:.0f} km/h - flat out on the straight")
        high_speed_reported = True

    ######### Track position #########
    track_pos = snap.get('trackPos')
    if track_pos is not None:
      if abs(track_pos) >= trackOffThresh:
        #tracks offtrackness using 
        off_track_samples += 1
        edge_samples = 0
      elif abs(track_pos) >= trackEdgeThresh:
        #checks if its near to an edge instead
        edge_samples += 1
        off_track_samples = 0
      else:
        if off_track_samples >= 3:
          side = "right" if track_pos > 0 else "left"
          points.append(f"Car went off-track to the {side}")
        elif edge_samples >= 5:
          side = "right" if track_pos > 0 else "left"
          points.append(f"Running very close to the {side} edge")
        off_track_samples = 0
        edge_samples = 0

    ######### Angle of car #########
    angle = snap.get('angle')
    if angle is not None and abs(angle) > angleThresh:
      points.append(f"Car sliding - angle {angle:.2f} rad from track centre")

    ######### RPM redline #########
    rpm = snap.get('rpm')
    if rpm is not None:
      if rpm >= rpmRedline:
        redline_samples += 1
        if redline_samples == 5:
          points.append(f"Hitting the redline at {rpm:.0f} RPM")
      else:
        redline_samples = 0

    ######### Finish line #########
    dist = snap.get('distRaced')
    prev_dist = prev.get('distRaced')
    if dist is not None and prev_dist is not None:
      if prev_dist - dist > 3000:
        points.append("Crossed the finish line - lap complete!")

    prev = snap

  ######### Closes open events for final summary #########
  last_spd = get_speed(samples[-1]) if samples else None
  if speed_at_brake_start is not None and last_spd is not None:
    points.append(f"Hard braking: {speed_at_brake_start:.0f} -> {last_spd:.0f} km/h")
  if speed_at_accel_start is not None and last_spd is not None:
    points.append(f"Heavy acceleration: {speed_at_accel_start:.0f} -> {last_spd:.0f} km/h")

  ######### Damage over the whole window #########
  damage_end = samples[-1].get('damage', 0) or 0
  damage_taken = damage_end - damage_start
  if damage_taken >= damageThresh:
    points.append(f"Took {damage_taken:.0f} damage points - possible wall contact")

  ######### (snapshot at end of window) #########
  fuel = samples[-1].get('fuel')
  if fuel is not None and fuel <= fuelLow:
    points.append(f"Fuel critically low: {fuel:.1f} L remaining")

  return points
      
    
def prompt_model(talking_points):
  if not talking_points:
    return None

  if talking_points:
    bullet_list = "\n".join(f"- {p}" for p in talking_points)
    prompt = f"Notable events in the last 5-6 seconds:\n{bullet_list}"
  else:
    prompt = "No notable events in the last 5-6 seconds, but provide some general commentary"

  try:
    response = ollama.chat(
      model=MODEL,
      messages=[
        {'role': 'system', 'content': AI_PROMPT},
        {'role': 'user',   'content': prompt}
      ]
    )
    return response['message']['content']
  except ollama.ResponseError:
    print(f'Ollama error, make sure you have pulled granite using: ollama pull {MODEL}')
  except ConnectError:
    print('Ollama error, make sure ollama is running in the background.')
  return None
      
      
def procedural_commentary_thread():
  samples = []
  prevDist = None
  while True:
    #time.sleep(0.1)
    time.sleep(sampleInterval)

    '''if not last_server_data:
      if server_data:
        last_server_data = server_data
        pass
        last_server_data = server_data
      '''
    
    if server_data:
      samples.append(dict(server_data))
    if len(samples) >= windowSamples:
      talking_points = detect_talking_points(samples)
      samples.clear()
      reply = prompt_model(talking_points)
      if reply:
        commentary_queue.put(reply)

 