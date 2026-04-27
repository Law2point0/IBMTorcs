import torch
import numpy as np
from snakeoil import Client
from actor import Actor
import shared
import telemetry_logging

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

actor = Actor(obs_dim=30, action_dim=2).to(device)
checkpoint = torch.load('checkpoints/latest.pt', map_location=device)
actor.load_state_dict(checkpoint['actor'])
actor.eval()
print(f"Loaded Inference model succesfully on {device}")

def get_obs(S):
    track = S.get('track', [100]*19)
    track = [v if v > 0 else 0 for v in track]
    
    whl = S.get('wheelSpinVel', [0,0,0,0])
    current_speed = float(S.get('speedX', 0))

    return np.array([
        current_speed / 200.0,
        float(S.get('speedY', 0)) / 50.0,
        float(S.get('speedZ', 0)) / 50.0,
        float(S.get('rpm', 0)) / 20000.0,
        float(S.get('angle', 0)) / 3.14,
        float(S.get('trackPos', 0)),
        0.0,
        *[v / 200.0 for v in track],
        *[v / 100.0 for v in whl],
    ], dtype=np.float32)

def auto_gear(speed):
    if speed < 60:   return 1
    elif speed < 105: return 2
    elif speed < 155: return 3
    elif speed < 205: return 4
    elif speed < 260: return 5
    elif speed < 315: return 6
    else:            return 7

def inference_client_thread():
    try:
        print("Waiting for TORCS...")
        C = Client(host='localhost', port=3001)
        print("Connected - running inference")

        log_interval_sec = 1.0
        next_log_time = log_interval_sec
        handle = None

        if shared.run_telemetry:
            handle = open(f"telemetry/{telemetry_logging.log_file_name()}.csv", "w", newline="")
            writer_state = (None, handle)

        step = 0
        while True:
            if not C.get_servers_input():
                print("TORCS disconnected")
                break

            S = C.S.d
            obs = get_obs(S)
            obs_t = torch.FloatTensor(obs).unsqueeze(0).to(device)

            with torch.no_grad():
                action = actor(obs_t).cpu().numpy().flatten()

            speed = float(S.get('speedX', 0))

            if speed > 150:   max_steer = 0.15
            elif speed > 100: max_steer = 0.25
            elif speed > 60:  max_steer = 0.4
            else:             max_steer = 1.0

            steer = float(np.clip(action[0], -max_steer, max_steer))
            throttle = float(np.clip(action[1], -1, 1))

            if throttle >= 0:
                accel, brake = throttle, 0.0
            else:
                accel, brake = 0.0, -throttle

            C.R.d['steer']  = steer
            C.R.d['accel']  = accel
            C.R.d['brake']  = brake
            C.R.d['gear']   = auto_gear(speed)
            C.R.d['clutch'] = 0.0
            C.R.d['meta']   = 0

            if shared.run_telemetry:
                writer_state, next_log_time = telemetry_logging.log_telemetry(
                    S,
                    C.R.d,
                    writer_state,
                    next_log_time,
                    log_interval_sec
                )

            shared.server_data.update(S)
            C.respond_to_server()
            step += 1

        C.shutdown()
        if handle:
            handle.close()

    except Exception as e:
        import traceback
        with open("crash.log", "w") as f:
            traceback.print_exc(file=f)
