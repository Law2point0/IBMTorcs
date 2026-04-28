import socket
import sys

DATA_SIZE = 2**17

class Client:
    def __init__(self, host='localhost', port=3001, sid='SCR'):
        self.host = host
        self.port = port
        self.sid = sid
        self.so = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.so.settimeout(1.0)
        self.S = ServerState()
        self.R = DriverAction()
        self._connect()

    def _connect(self):
        #custom sensor ranges
        angles = "-90 -60 -45 -40 -25 -15 -8 -4 -1 0 1 4 8 15 25 40 45 60 90"
        init_msg = f"{self.sid}(init {angles})"
        while True:
            try:
                self.so.sendto(init_msg.encode(), (self.host, self.port))
                data, _ = self.so.recvfrom(DATA_SIZE)
                data = data.decode('utf-8')
                if '***identified***' in data:
                    print(f"Connected to TORCS on port {self.port}")
                    break
            except socket.timeout:
                print("Waiting for TORCS...")

    def get_servers_input(self):
        while True:
            try:
                data, _ = self.so.recvfrom(DATA_SIZE)
                data = data.decode('utf-8')
                if '***shutdown***' in data or '***restart***' in data:
                    print("TORCS signal received:", data)
                    return False
                if data:
                    self.S.parse(data)
                    return True
            except socket.timeout:
                pass

    def respond_to_server(self):
        msg = repr(self.R)
        self.so.sendto(msg.encode(), (self.host, self.port))

    def shutdown(self):
        self.so.close()


class ServerState:
    def __init__(self):
        self.d = {}

    def parse(self, s):
        s = s.strip().lstrip('(').rstrip(')')
        for item in s.split(')('):
            parts = item.split()
            if len(parts) >= 2:
                key = parts[0]
                vals = parts[1:]
                try:
                    if len(vals) == 1:
                        self.d[key] = float(vals[0])
                    else:
                        self.d[key] = [float(v) for v in vals]
                except ValueError:
                    self.d[key] = vals[0] if len(vals) == 1 else vals


class DriverAction:
    def __init__(self):
        self.d = {
            'accel': 0.0,
            'brake': 0.0,
            'clutch': 0.0,
            'gear': 1,
            'steer': 0.0,
            'focus': [-90, -45, 0, 45, 90],
            'meta': 0
        }

    def __repr__(self):

        self.d['brake'] = max(0.0, min(1.0, self.d['brake']))
        self.d['accel'] = max(0.0, min(1.0, self.d['accel']))
        self.d['steer'] = max(-1.0, min(1.0, self.d['steer']))

        out = ''
        for k, v in self.d.items():
            out += f'({k} '
            if isinstance(v, list):
                out += ' '.join(str(x) for x in v)
            elif k == 'gear':
                out += str(int(v))  # gear must be integer
            else:
                out += f'{v:.3f}' if isinstance(v, float) else str(v)
            out += ')'
        return out