import numpy as np
from utils.snakeoil import Client
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TorcsEnv:
    def __init__(self, host='localhost', port=3001):
        self.host = host
        self.port = port
        self.client = None
        self.prev_dist = 0
        self.prev_damage = 0
        self.step_count = 0
        self.stuck_steps = 0
        self.obs_dim = 30

    def connect(self):
        self.client = Client(host=self.host, port=self.port)

    def get_obs(self):
        S = self.client.S.d
        track = S.get('track', [100]*19)
        #fixes sensor out of range
        track = [v if v > 0 else 0 for v in track]
        whl = S.get('wheelSpinVel', [0,0,0,0])

        current_speed = float(S.get('speedX', 0))
        prev_speed = getattr(self, 'prev_speed_obs', current_speed)
        momentum = (current_speed - prev_speed) / 50.0
        #normalise observations
        obs = np.array([
            float(S.get('speedX', 0)) / 200.0,
            float(S.get('speedY', 0)) / 50.0,
            float(S.get('speedZ', 0)) / 50.0,
            float(S.get('rpm', 0)) / 20000.0,
            float(S.get('angle', 0)) / 3.14,
            float(S.get('trackPos', 0)),
            momentum,
            *[v / 200.0 for v in track],
            *[v / 100.0 for v in whl],
        ], dtype=np.float32)
        
        return obs

    def get_reward(self, steer = 0.0):
        S = self.client.S.d
        speed = float(S.get('speedX', 0))
        angle = float(S.get('angle', 0))
        track_pos = float(S.get('trackPos', 0))
        damage = float(S.get('damage', 0))
        dist = float(S.get('distRaced', 0))
        
        # terminate penalty
        if abs(track_pos) > 1.0:
            self.prev_damage = damage
            self.prev_dist = dist
            return -5.0
        
        # no reward if not moving
        if speed < 5.0:
            self.prev_damage = damage
            self.prev_dist = dist
            return 0.0

        # progress rewards
        #progress = max(0, speed * np.cos(angle)) / 50
        dist_delta = dist - self.prev_dist
        self.prev_dist = dist
        progress_reward = max(0, dist_delta) * 0.3

        centre_multiplier = max(0.2, 1.0 - abs(track_pos))
        progress_reward *= centre_multiplier

        angle_penalty = abs(angle) * 0.3

        # edge penalty
        if abs(track_pos) > 0.5:
            edge_penalty = ((abs(track_pos) - 0.5) ** 2) * 2.0
        else:
            edge_penalty = 0.0
        '''target_speed = 175.0
        speed_reward = min(speed / target_speed, 1.0) * 0.5
        if speed < 30:
            # Actively penalise very slow driving
            speed_reward = -0.5
        elif speed < target_speed:
            speed_reward = (speed / target_speed) * 1.0
        else:
            speed_reward = 1.0 - ((speed - target_speed) / target_speed) * 0.3

        # centre line penalty
        if speed > 5:
            centre_penalty = abs(track_pos) * 0.1
        else:
            centre_penalty = 0.0
        if speed > 5:
            centre_penalty = (track_pos ** 2) * 0.5
        if abs(track_pos) > 0.7:
            centre_penalty += (abs(track_pos) - 0.7) * 3.0
        else:
            centre_penalty = 0.0

        # centering reward
        if speed > 5:
            steering_correction = -track_pos * S.get('steer', 0) if hasattr(S, 'get') else 0
            steering_reward = max(0, steering_correction) * 0.8
        else:
            steering_reward = 0.0
        # corner rewards
        if abs(angle) > 0.2:
            corner_reward = max(0, 1.0 - abs(track_pos)) * 0.5
        else:
            corner_reward = 0.0'''

        # damage penalty
        damage_delta = damage - self.prev_damage
        if damage_delta > 0:
            damage_penalty = min(damage_delta * 0.001, 1.0)
        else:
            damage_penalty = 0.0
        self.prev_damage = damage

        reward = progress_reward - angle_penalty - damage_penalty - edge_penalty # + speed_reward + corner_reward + steering_reward - centre_penalty - damage_penalty

        return float(reward)

    def is_done(self):
        S = self.client.S.d
        speed = float(S.get('speedX', 0))
        angle = float(S.get('angle', 0))
        track_pos = float(S.get('trackPos', 0))
        damage = float(S.get('damage', 0))

        '''# Any damage = immediate reset
        if damage > 0:
            return True, 'damage'
        '''
        # instant terminatrion cases
        if abs(track_pos) > 1.0:
            return True, 'off_track'

        if np.cos(angle) < 0:
            return True, 'wrong_way'

        if self.step_count > 500 and abs(speed) < 1:
           return True, 'stuck'

        if self.step_count >= 10000:
            return True, 'timeout'
        
        

        '''
        # Off track
        if abs(track_pos) > 1.0:
            self.off_track_steps += 1
            if self.off_track_steps > 30:
                self.off_track_steps = 0
                return True, 'off_track'
        else:
            self.off_track_steps = 0
        
        # Going backwards
        if np.cos(angle) < 0:
            self.wrong_way_steps += 1
            if self.wrong_way_steps > 30:
                self.wrong_way_steps = 0
                return True, 'wrong_way'
        else:
            self.wrong_way_steps = 0
        '''
        # Too slow after warmup
        if self.step_count > 500 and abs(speed) < 5:
            self.stuck_steps += 1
            if self.stuck_steps > 100:
                self.stuck_steps = 0
                return True, 'stuck'
        else:
            self.stuck_steps = 0
        '''
        if self.step_count >= 2000:
            return True, 'timeout'
        '''
        return False, None

    def reset(self):
        #self.off_track_steps = 0
        #self.wrong_way_steps = 0
        self.stuck_steps = 0
        self.prev_speed_obs = 0.0
        self.prev_damage = 0
        self.step_count = 0
        if self.client is None:
            self.connect()
        else:
            # sends reset signal
            self.client.R.d['meta'] = 1
            self.client.respond_to_server()

            self.client = None
            self.connect()
        
        self.prev_damage = 0
        self.step_count = 0
        
        if not self.client.get_servers_input():
            raise RuntimeError("TORCS disconnected")
        
        return self.get_obs()

    def step(self, action):
        R = self.client.R.d
        steer = float(np.clip(action[0], -1, 1))
        throttle = float(np.clip(action[1], 0, 1))
        speed = float(self.client.S.d.get('speedX', 0))

        if throttle >= 0:
            accel = throttle
            brake = 0.0
        else:
            accel = 0.0
            brake = -throttle
    
        if speed > 100:
            max_steer = 0.3
        elif speed > 60:
            max_steer = 0.5
        else:
            max_steer = 1.0
        steer = float(np.clip(action[0], -max_steer, max_steer))

        R['steer'] = steer
        R['accel'] = accel
        R['brake'] = brake
        R['clutch'] = 0.0
        R['gear'] = self.auto_gear()
        R['meta'] = 0
        
        self.client.respond_to_server()
        
        if not self.client.get_servers_input():
            return self.get_obs(), 0, True, 'disconnected'
        
        obs = self.get_obs()
        reward = self.get_reward(steer=steer)
        done, reason = self.is_done()
        self.step_count += 1

        if done and reason is None:
            reason = 'huh'

        return obs, reward, done, reason

    def auto_gear(self):
        S = self.client.S.d
        speed = float(S.get('speedX', 0))
        rpm = float(S.get('rpm', 0))
        current_gear = int(S.get('gear', 1))

        '''if speed < 0:
            return -1  # reverse
        if speed < 60:
            return 1
        elif speed < 105:
            return 2
        elif speed < 155:
            return 3
        elif speed < 205:
            return 4
        elif speed < 260:
            return 5
        elif speed < 315:
            return 6
        else:
            return 7

        if current_gear <= 0:
            return 1'''

        upshift = [0, 60, 105, 155, 205, 260, 315]
        downshift = [0, 0, 45, 85, 130, 175, 225, 275]

        gear = current_gear

        # tops out gear if rpm maxed out
        if rpm > 16500 and current_gear < 7:
            gear = current_gear + 1

        # speed based if between thresholds
        elif current_gear < 7 and speed > upshift[current_gear]:
            gear = current_gear + 1

        if current_gear > 1 and speed < downshift[current_gear]:
            gear = current_gear - 1

        return max(1, min(7, int(gear)))