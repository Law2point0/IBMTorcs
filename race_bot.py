import math

# ================= USER CONFIGURABLE PARAMETERS =================
TARGET_SPEED = 300  # Target speed in km/h. Increasing this makes the car go faster but may reduce stability.
STEER_GAIN = 5     # Steering sensitivity. Higher values make the car turn more aggressively.
CENTERING_GAIN = 0.1 # How strongly the car corrects its position toward the center of the track.
BRAKE_THRESHOLD = 0.05  # Angle threshold for braking. Lower values brake earlier.
GEAR_SPEEDS = [0, 60, 120, 150, 170, 190, 210, 230, 240, 250, 260]  # Speed thresholds for gear shifting.
ENABLE_TRACTION_CONTROL = True  # Toggle traction control system. 

def calculate_steering(S):
  steer = (S['angle'] * STEER_GAIN / math.pi) - (S['trackPos'] * CENTERING_GAIN)
  return max(-1, min(1, steer))

def calculate_throttle(S, R):
  if S['speedX'] < TARGET_SPEED - (R['steer'] * 2.5):
    accel = min(1.0, R['accel'] + 0.4)
  else:
    accel = max(0.0, R['accel'] - 0.2)
  if S['speedX'] < 10:
    accel += 1 / (S['speedX'] + 0.1)
  return max(0.0, min(1.0, accel))

def apply_brakes(S):
  return 0.5 * abs(S['angle']) if abs(S['angle']) > BRAKE_THRESHOLD else 0.0

def shift_gears(S):
  gear = 1
  for i, speed in enumerate(GEAR_SPEEDS):
    if S['speedX'] > speed:
      gear = i + 1
  return min(gear, 11)

def traction_control(S, accel):
  if ENABLE_TRACTION_CONTROL:
    if ((S['wheelSpinVel'][2] + S['wheelSpinVel'][3]) - (S['wheelSpinVel'][0] + S['wheelSpinVel'][1])) > 2:
      accel -= 0.1
  return max(0.0, accel)

def drive_to_speed(S, R, target_speed, brake_input): # Drives the car to the passed target speed and will also slow to the speed using the passed braking power
  if S['speedX'] < target_speed:
    accel_increase_rate = min(1.0, R['accel'] + 0.4)
    accel = max(0.0, accel_increase_rate)
  else:
    speed_difference = max(0, S['speedX'] - target_speed)
    accel_decrease_rate = max(0.0, R['accel'] - (0.2 * speed_difference / target_speed))
    accel = max(0.0, min(1.0, accel_decrease_rate))
    R['brake'] = brake_input
    R['gear'] = shift_gears(S)

def turn_to_corner(S, R, track_pos, steer_angle): # Turns the car towards a line at a certain angle. Increasing the steer_angle makes the car turn sharper
  if track_pos > 0:
    if S['trackPos'] < track_pos:
      steer = S['angle'] + steer_angle * STEER_GAIN
      R['steer'] = steer
  else:
    if S['trackPos'] > track_pos:
      steer = S['angle'] - steer_angle * STEER_GAIN
      R['steer'] = steer

def drive(c):
  S, R = c.S.d, c.R.d

  # `get_servers_input` normalizes `S['distRaced']` per lap, so use it directly
  dist_bounds = S['distRaced']

  drive_to_speed(S, R, TARGET_SPEED, 0.3)

  R['steer'] = calculate_steering(S)
  R['accel'] = calculate_throttle(S, R)
  R['brake'] = apply_brakes(S)
  R['accel'] = traction_control(S, R['accel'])

  if S['rpm'] > 8000:
    R['gear'] = shift_gears(S)
  elif S['rpm'] == 0:
    R['gear'] = 1

  if dist_bounds < 180 : # start line to turn 1
    drive_to_speed(S, R, TARGET_SPEED, 0.3)

  if dist_bounds >= 180 and dist_bounds <= 230: # turn 1 code
    turn_to_corner(S, R, 0.9, 0.02) # in this instance the car turns to be 90% left of the centre of the track and turns at an angle of 0.02 radians
    drive_to_speed(S, R, TARGET_SPEED, 0.3) # in this instance the car aims to drive at the global target speed (as fast as it can) and will brake with 30% power
  if dist_bounds > 230 and dist_bounds < 300: # straight to turn 2 
    turn_to_corner(S, R, -0.8, 0.01) # in this instance the car turns to be -80% left of the centre of the track (80% to the right)
    drive_to_speed(S, R, TARGET_SPEED, 0.3)
  if dist_bounds >= 300 and dist_bounds <= 390: # straight to turn 2 prep
    turn_to_corner(S, R, -0.8, 0.03)
    drive_to_speed(S, R, 100, 0.4) # in this instance the car aims to drive at a limit of 100km/h and brakes with 40% power
  if dist_bounds > 390 and dist_bounds < 515: # turn 2 code
    turn_to_corner(S, R, 0.8, 0.15)
    drive_to_speed(S, R, 85, 0.3)
  if dist_bounds >= 515 and dist_bounds <= 600: # kink to turn 3
    turn_to_corner(S, R, -0.8, 0.001)
    drive_to_speed(S, R, 95, 0.3)
  if dist_bounds > 600 and dist_bounds < 730: # straight to turn 3
    turn_to_corner(S, R, 0.8, 0.005)
    drive_to_speed(S, R, 120, 0.3)
  if dist_bounds >= 730 and dist_bounds <= 790: # turn 3 code
    turn_to_corner(S, R, -0.8, 0.075)
    drive_to_speed(S, R, 90, 0.35)
  if dist_bounds > 790 and dist_bounds < 970: # straight to turn 4
    turn_to_corner(S, R, 0.8, 0.01)
    drive_to_speed(S, R, TARGET_SPEED, 0.3)
  if dist_bounds >= 970 and dist_bounds < 1050: # turn 4 code
    turn_to_corner(S, R, -0.8, 0.06)
    drive_to_speed(S, R, 90, 0.3)
  if dist_bounds >= 1050 and dist_bounds < 1425: # straight to turn 5
    turn_to_corner(S, R, -0.8, 0.01)
    drive_to_speed(S, R, TARGET_SPEED, 0.3)
  if dist_bounds >= 1425 and dist_bounds < 1450: # turn 5 prep
    turn_to_corner(S, R, -0.8, 0.045)
    drive_to_speed(S, R, 90, 0.32)
  if dist_bounds >= 1450 and dist_bounds < 1575: # turn 5 code
    turn_to_corner(S, R, 0.7, 0.075)
    drive_to_speed(S, R, 95, 0.3)
  if dist_bounds >= 1575 and dist_bounds < 1800: # straight to turn 6
    turn_to_corner(S, R, -0.8, 0.005)
    drive_to_speed(S, R, TARGET_SPEED, 0.3)
  if dist_bounds >= 1850 and dist_bounds < 1900: # turn 6 prep
    turn_to_corner(S, R, -0.8, 0.005)
    drive_to_speed(S, R, 110, 0.3)
  if dist_bounds >= 1900 and dist_bounds < 1950: # turn 6 code
    turn_to_corner(S, R, 0.8, 0.075)
    drive_to_speed(S, R, 120, 0.3)
  if dist_bounds >= 1950 and dist_bounds < 2200: # straight to turn 7/8 (corkscrew)
    turn_to_corner(S, R, -0.8, 0.001)
    drive_to_speed(S, R, TARGET_SPEED, 0.3)
  if dist_bounds >= 2200 and dist_bounds < 2280: # straight to turn 7/8 (corkscrew)
    turn_to_corner(S, R, -0.8, 0.001)
    drive_to_speed(S, R, 90, 0.3)
  if dist_bounds >= 2280 and dist_bounds < 2380: # prep for turn 7/8 (corkscrew)
    turn_to_corner(S, R, -0.8, 0.001)
    drive_to_speed(S, R, 40, 0.3)
  if dist_bounds >= 2380 and dist_bounds < 2430: # prep for turn 7/8 (corkscrew)
    turn_to_corner(S, R, -0.5, 0.01)
    drive_to_speed(S, R, 30, 0.3)
  if dist_bounds >= 2430 and dist_bounds < 2475: # turn 7 code
    turn_to_corner(S, R, 0.75, 0.05)
    drive_to_speed(S, R, 20, 0.2)
  if dist_bounds >= 2475 and dist_bounds < 2500: # turn 8 code
    turn_to_corner(S, R, -0.8, 0.05)
    drive_to_speed(S, R, 30, 0.1)
  if dist_bounds >= 2500 and dist_bounds < 2650: # straight to turn 9
    turn_to_corner(S, R, -0.8, 0.01)
    drive_to_speed(S, R, 120, 0.3)
  if dist_bounds >= 2650 and dist_bounds < 2800: # turn 9 code
    turn_to_corner(S, R, 0.8, 0.075)
    drive_to_speed(S, R, 135, 0.3)
  if dist_bounds >= 2800 and dist_bounds < 2850: # straight to turn 10
    turn_to_corner(S, R, 0.8, 0.01)
    drive_to_speed(S, R, TARGET_SPEED, 0.3)
  if dist_bounds >= 2850 and dist_bounds < 2920: # turn 10 prep
    turn_to_corner(S, R, 0.8, 0.075)
    drive_to_speed(S, R, 120, 0.3)
  if dist_bounds >= 2920 and dist_bounds < 3000: # turn 10 code
    turn_to_corner(S, R, -0.8, 0.075)
    drive_to_speed(S, R, 100, 0.3)
  if dist_bounds >= 3000 and dist_bounds < 3050: # straight to turn 11
    turn_to_corner(S, R, -0.8, 0.005)
    drive_to_speed(S, R, TARGET_SPEED, 0.3)
  if dist_bounds >= 3150 and dist_bounds < 3250: # turn 11 prep
    turn_to_corner(S, R, -0.8, 0.02)
    drive_to_speed(S, R, 50, 0.35)
  if dist_bounds >= 3250 and dist_bounds < 3275: # turn 11 code
    turn_to_corner(S, R, 0.7, 0.075)
    drive_to_speed(S, R, 45, 0.3)
  
  return