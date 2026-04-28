import torch
import torch.nn as nn

class Actor(nn.Module):
    def __init__(self, obs_dim=30, action_dim=3):
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
        self.throttle_head = nn.Tanh()

    def forward(self, x):
        x = self.net(x)
        steer = self.steer_head(x[:, 0:1])
        throttle = self.throttle_head(x[:, 1:2])
        return torch.cat([steer, throttle], dim=1)