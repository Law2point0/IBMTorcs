import torch
import torch.nn as nn

class Actor(nn.Module):
    def __init__(self, obs_dim=29, action_dim=3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(obs_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, action_dim),
        )
        # Output heads
        self.steer_head = nn.Tanh()   # [-1, 1]
        self.accel_head = nn.Sigmoid() # [0, 1]
        self.brake_head = nn.Sigmoid() # [0, 1]

    def forward(self, x):
        x = self.net(x)
        steer = self.steer_head(x[:, 0:1])
        accel = self.accel_head(x[:, 1:2])
        brake = self.brake_head(x[:, 2:3])
        return torch.cat([steer, accel, brake], dim=1)