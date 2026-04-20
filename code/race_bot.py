import math

# ================= USER CONFIGURABLE PARAMETERS =================
TARGET_SPEED = 300  # Target speed in km/h. Increasing this makes the car go faster but may reduce stability.
STEER_GAIN = 5     # Steering sensitivity. Higher values make the car turn more aggressively.
CENTERING_GAIN = 0.1 # How strongly the car corrects its position toward the center of the track.
BRAKE_THRESHOLD = 0.05  # Angle threshold for braking. Lower values brake earlier.
GEAR_SPEEDS = [0, 60, 120, 150, 170, 190, 210, 230, 240, 250, 260]  # Speed thresholds for gear shifting.
ENABLE_TRACTION_CONTROL = True  # Toggle traction control system. 

# ================= HELPER FUNCTIONS =================
def calculate_steering(S):
    steer = (S['angle'] * STEER_GAIN / math.pi) - (S['trackPos'] * CENTERING_GAIN)
    return max(-1, min(1, steer))

def calculate_throttle(S, R, target_speed):
    if S['speedX'] < target_speed - (R['steer'] * 2.5):
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
            accel -= 0.05
    return max(0.0, accel)

def drive_to_speed(S, R, target_speed, brake_input): # Drives the car to the passed target speed and will also slow to the speed using the passed braking power
    if S['speedX'] < target_speed:
        R['accel'] = calculate_throttle(S, R, target_speed)
    else:
        speed_difference = max(0, S['speedX'] - target_speed)
        accel_decrease_rate = max(0.0, R['accel'] - (0.2 * speed_difference / target_speed))
        accel = max(0.0, min(1.0, accel_decrease_rate))
        R['accel'] = accel
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
    
def turn_within_lines (S, R, track_pos_L, track_pos_R, steer_angle):
    if S['trackPos'] > track_pos_R:
        steer = S['angle'] - steer_angle * STEER_GAIN
        R['steer'] = steer
    if S['trackPos'] < track_pos_L:
        steer = S['angle'] + steer_angle * STEER_GAIN
        R['steer'] = steer

def steady_accel(S, R, target_speed):
    if S['speedX'] < target_speed:
        R['accel'] = calculate_throttle(S, R, target_speed) / 2
    else:
        if S['speedX'] > target_speed:
            R['accel'] = 0.0
        else:
            R['accel'] = 0.01

def gradual_turn(S, R, target_angle):
    if S['angle'] < target_angle:
        steer = S['angle'] + (target_angle - S['angle']) * 0.2
        R['steer'] = steer
    elif S['angle'] > target_angle:
        steer = S['angle'] - (S['angle'] - target_angle) * 0.2
        R['steer'] = steer
# ================= MAIN DRIVE FUNCTION =================

def drive_modular(c):
    S, R = c.S.d, c.R.d

    # `get_servers_input` normalizes `S['distRaced']` per lap, so use it directly
    dist_bounds = S['distRaced']

    

    if S['rpm'] > 18000:
        R['gear'] = shift_gears(S)
    elif S['rpm'] == 0:
        R['gear'] = 1

    
    if dist_bounds < 60: # car startup
        R['steer'] = calculate_steering(S)
        steady_accel(S, R, TARGET_SPEED)
    if dist_bounds >= 60 and dist_bounds <= 200: #straight to turn 1 
        R['steer'] = calculate_steering(S)
        drive_to_speed(S, R, TARGET_SPEED, 0.3)
    if dist_bounds > 190 and dist_bounds < 230: # turn 1 code
        turn_to_corner(S, R, 0.8, 0.05) # in this instance the car turns to be 80% left of the centre of the track
        drive_to_speed(S, R, TARGET_SPEED, 0.3)
    if dist_bounds >= 230 and dist_bounds <= 400: # straight to turn 2 prep
        turn_within_lines(S, R, -0.7, -0.9, 0.009)
        drive_to_speed(S, R, 90, 0.5) # in this instance the car aims to drive at a limit of 90km/h and brakes with 50% power
    if dist_bounds > 400 and dist_bounds < 570: # turn 2 code
        turn_within_lines(S, R, 1.09, 0.8, 0.03)
        drive_to_speed(S, R, 90, 0.0)
    if dist_bounds >= 570 and dist_bounds <= 600: # kink to turn 3
        turn_within_lines(S, R, -0.5, -0.85, 0.01)
        drive_to_speed(S, R, TARGET_SPEED, 0.3)
    if dist_bounds > 600 and dist_bounds < 690: # straight to turn 3
        turn_to_corner(S, R, 0.8, 0.005)
        drive_to_speed(S, R, TARGET_SPEED, 0.3)
    if dist_bounds >= 690 and dist_bounds < 730: # turn 3 prep
        drive_to_speed(S, R, 100, 0.3)
    if dist_bounds >= 730 and dist_bounds < 790: # turn 3 code
        turn_within_lines(S, R, -0.75, -0.99, 0.075)
        drive_to_speed(S, R, 110, 0.0)
    if dist_bounds >= 790 and dist_bounds < 930: # straight to turn 4
        turn_to_corner(S, R, 0.8, 0.01)
        drive_to_speed(S, R, TARGET_SPEED, 0.3)
    if dist_bounds >= 930 and dist_bounds < 970: # turn 4 prep
        turn_to_corner(S, R, 0.8, 0.01)
        drive_to_speed(S, R, 110, 0.4)
    if dist_bounds >= 970 and dist_bounds < 1050: # turn 4 code
        turn_within_lines(S, R, -0.75, -1.19, 0.03)
        drive_to_speed(S, R, 120, 0.0)
    if dist_bounds >= 1050 and dist_bounds < 1410: # straight to turn 5
        R['steer'] = calculate_steering(S)
        drive_to_speed(S, R, TARGET_SPEED, 0.2)
    if dist_bounds >= 1410 and dist_bounds < 1450: # turn 5 prep
        turn_within_lines(S, R, -0.2, -0.8, 0.01)
        drive_to_speed(S, R, 90, 0.4)
    if dist_bounds >= 1450 and dist_bounds < 1575: # turn 5 code
        turn_within_lines(S, R, 1.29, 0.85, 0.03)
        drive_to_speed(S, R, 95, 0.0)
    if dist_bounds >= 1575 and dist_bounds < 1800: # straight to turn 6
        turn_to_corner(S, R, -0.8, 0.005)
        drive_to_speed(S, R, TARGET_SPEED, 0.2)
    if dist_bounds >= 1850 and dist_bounds < 1900: # turn 6 prep
        turn_within_lines(S, R, -0.6, -0.8, 0.01)
        drive_to_speed(S, R, 110, 0.2)
    if dist_bounds >= 1900 and dist_bounds < 1950: # turn 6 code
        turn_within_lines(S, R, 0.99, 0.75, 0.05)
        drive_to_speed(S, R, 120, 0.1)
    if dist_bounds >= 1950 and dist_bounds < 2270: # straight to turn 7/8 (corkscrew)
        R['steer'] = calculate_steering(S)
        drive_to_speed(S, R, TARGET_SPEED, 0.3)
    if dist_bounds >= 2270 and dist_bounds < 2320: # straight to turn 7/8 (corkscrew)
        R['steer'] = calculate_steering(S)
        drive_to_speed(S, R, 90, 0.3)
    if dist_bounds >= 2320 and dist_bounds < 2425: # prep for turn 7/8 (corkscrew)
        R['steer'] = calculate_steering(S)
        drive_to_speed(S, R, 30, 0.3)
    if dist_bounds >= 2425 and dist_bounds < 2484: # turn 7 code
        turn_within_lines(S, R, 0.9, 0.3, 0.075)
        drive_to_speed(S, R, 25, 0.0)
    if dist_bounds >= 2484 and dist_bounds < 2505: # turn 8 code
        turn_to_corner(S, R, -0.8, 0.04)
        drive_to_speed(S, R, 30, 0.0)
    if dist_bounds >= 2505 and dist_bounds < 2565: # straight to turn 9 1/2
        R['steer'] = calculate_steering(S)
        steady_accel(S, R, TARGET_SPEED)
    if dist_bounds >= 2565 and dist_bounds < 2650: # straight to turn 9 2/2
        R['steer'] = calculate_steering(S)
        drive_to_speed(S, R, 80, 0.3)
    if dist_bounds >= 2650 and dist_bounds < 2740: # turn 9 code
        turn_within_lines(S, R, 1, 0.5, 0.02)
        R['accel'] = traction_control(S, R['accel'])
        drive_to_speed(S, R, 80, 0.0)
    if dist_bounds >= 2740 and dist_bounds < 2830: # straight to turn 10
        turn_within_lines(S, R, 0.7, 0.3, 0.01)
        steady_accel(S, R, TARGET_SPEED)
    if dist_bounds >= 2830 and dist_bounds < 2870: # turn 10 prep
        R['steer'] = calculate_steering(S)
        drive_to_speed(S, R, 100, 0.3)
    if dist_bounds >= 2870 and dist_bounds < 3060: # turn 10 code
        turn_within_lines(S, R, -0.3, -0.99, 0.03)
        drive_to_speed(S, R, 100, 0.0)
    if dist_bounds >= 3060 and dist_bounds < 3140: # straight to turn 11
        turn_within_lines(S, R, -0.3, -0.8, 0.0025)
        drive_to_speed(S, R, TARGET_SPEED, 0.3)
    if dist_bounds >= 3140 and dist_bounds < 3235: # turn 11 prep
        turn_within_lines(S, R, -0.5, -0.99, 0.001)
        drive_to_speed(S, R, 40, 0.3)
    if dist_bounds >= 3235 and dist_bounds < 3275: # turn 11 code
        turn_to_corner(S, R, 0.7, 0.055)
        drive_to_speed(S, R, 40, 0.0)
    if dist_bounds >= 3275 and dist_bounds < 3600: # straight to finish line
        R['steer'] = calculate_steering(S)
        steady_accel(S, R, TARGET_SPEED)
    if dist_bounds >= 3325 and dist_bounds < 3600: # straight to finish line
        R['steer'] = calculate_steering(S)
        drive_to_speed(S, R, TARGET_SPEED, 0.3)
    
    return