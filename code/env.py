import numpy as np
from snakeoil import Client

class TorcsEnv:
    def __init__(self, host='localhost', port=3001):
        self.host = host
        self.port = port
        self.client = None
        self.prev_dist = 0
        self.prev_damage = 0
        self.step_count = 0
        self.obs_dim = 29

    def _connect(self):
        self.client = Client(host=self.host, port=self.port)

    def _get_obs(self):
        S = self.client.S.d
        track = S.get('track', [100]*19)
        #fixes sensor out of range
        track = [v if v > 0 else 0 for v in track]
        whl = S.get('wheelSpinVel', [0,0,0,0])
        
        #normalise observations
        obs = np.array([
            float(S.get('speedX', 0)) / 200.0,
            float(S.get('speedY', 0)) / 50.0,
            float(S.get('speedZ', 0)) / 50.0,
            float(S.get('rpm', 0)) / 20000.0,
            float(S.get('angle', 0)) / 3.14,
            float(S.get('trackPos', 0)),
            *[v / 200.0 for v in track],
            *[v / 100.0 for v in whl],
        ], dtype=np.float32)
        
        return obs

    def _get_reward(self):
        S = self.client.S.d
        speed = float(S.get('speedX', 0))
        angle = float(S.get('angle', 0))
        track_pos = float(S.get('trackPos', 0))
        damage = float(S.get('damage', 0))
        
        # progress rewards
        progress = max(0, speed * np.cos(angle)) / 100.0
        
        # centre line penalty
        if speed > 5:
            centre_penalty = abs(track_pos) * 0.1
        else:
            centre_penalty = 0.0

        # damage penalty
        damage_delta = damage - self.prev_damage
        if damage_delta > 0:
            damage_penalty = min(damage_delta * 0.001, 1.0)
        else:
            damage_penalty = 0.0
        self.prev_damage = damage

        reward = progress - centre_penalty - damage_penalty

        return float(reward)

    def _is_done(self):
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
        
        # Too slow after warmup
        if self.step_count > 500 and abs(speed) < 5:
            self.stuck_steps += 1
            if self.stuck_steps > 100:
                self.stuck_steps = 0
                return True, 'stuck'
        else:
            self.stuck_steps = 0

        if self.step_count >= 2000:
            return True, 'timeout'
        '''
        return False, None

    def reset(self):
        #self.off_track_steps = 0
        #self.wrong_way_steps = 0
        #self.stuck_steps = 0
        self.prev_damage = 0
        self.step_count = 0
        if self.client is None:
            self._connect()
        else:
            # sends reset signal
            self.client.R.d['meta'] = 1
            self.client.respond_to_server()

            self.client = None
            self._connect()
        
        self.prev_damage = 0
        self.step_count = 0
        
        if not self.client.get_servers_input():
            raise RuntimeError("TORCS disconnected")
        
        return self._get_obs()

    def step(self, action):
        R = self.client.R.d
        
        R['steer'] = float(np.clip(action[0], -1, 1))
        R['accel'] = float(np.clip(action[1], 0, 1))
        R['brake'] = float(np.clip(action[2], 0, 1))
        R['clutch'] = 0.0
        R['gear'] = self._auto_gear()
        R['meta'] = 0
        
        self.client.respond_to_server()
        
        if not self.client.get_servers_input():
            return self._get_obs(), 0, True, 'disconnected'
        
        obs = self._get_obs()
        reward = self._get_reward()
        done, reason = self._is_done()
        self.step_count += 1

        if done and reason is None:
            reason = 'huh'

        return obs, reward, done, reason

    def _auto_gear(self):
        S = self.client.S.d
        speed = float(S.get('speedX', 0))
        rpm = float(S.get('rpm', 0))
        current_gear = int(S.get('gear', 1))

        if current_gear <= 0:
            return 1

        upshift = [0, 60, 105, 155, 205, 260, 315]
        downshift = [0, 0, 45, 85, 130, 175, 225, 275]

        gear = current_gear

        # tops out gear if rpm maxed out
        if rpm > 17000 and current_gear < 7:
            gear = current_gear + 1

        # speed based if between thresholds
        elif current_gear < 7 and speed > upshift[current_gear]:
            gear = current_gear + 1

        if current_gear > 1 and speed < downshift[current_gear]:
            gear = current_gear - 1

        return max(1, min(7, int(gear)))